from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .constants import ROOT
from .orchestrator import OrchestratorGraph, latest_run
from .registry import agent_registry, tool_registry
from .utils import read_json, write_json


def _project(path: str) -> Path:
    return Path(path).resolve()


def cmd_init_project(args: argparse.Namespace) -> int:
    project_dir = _project(args.project)
    OrchestratorGraph(factory_root=ROOT, project_dir=project_dir).initialize_project()
    write_json(project_dir / "tool-availability.json", detect_tools())
    print(f"project_ready={project_dir}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    project_dir = _project(args.project)
    if args.clean_generated_app and args.no_clean_generated_app:
        print("error=clean_generated_app_flags_conflict")
        return 2
    clean_generated_app = False if args.no_clean_generated_app else True if args.clean_generated_app else None
    run_dir = OrchestratorGraph(factory_root=ROOT, project_dir=project_dir).run(args.objective, phase=args.phase, from_phase=args.from_phase, clean_generated_app=clean_generated_app)
    write_json(project_dir / "latest-run.json", {"run_dir": str(run_dir)})
    print(f"run_dir={run_dir}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    project_dir = _project(args.project)
    source_run = Path(args.run).resolve() if args.run else latest_run(project_dir)
    if source_run is None:
        print("error=no_run_found")
        return 2
    objective = args.objective or f"Reanudar fabrica desde {source_run.name}"
    run_dir = OrchestratorGraph(factory_root=ROOT, project_dir=project_dir).run(objective, from_phase=args.from_phase, resume_from=source_run)
    write_json(project_dir / "latest-run.json", {"run_dir": str(run_dir)})
    print(f"resumed_from={source_run}")
    print(f"run_dir={run_dir}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    project_dir = _project(args.project)
    run_dir = Path(args.run).resolve() if args.run else latest_run(project_dir)
    if run_dir is None:
        print("error=no_run_found")
        return 2
    result = verify_run(run_dir)
    write_json(run_dir / "verification-summary.json", result)
    print(f"status={result['status']}")
    print(f"run_dir={run_dir}")
    if result["run_policy"]["status"] != "current":
        print(f"run_policy={result['run_policy']['status']}:{result['run_policy']['reason']}")
    if result["missing"]:
        print("missing=" + ",".join(result["missing"]))
    if result["app_audit"]["findings"]:
        print("app_findings=" + " | ".join(result["app_audit"]["findings"][:8]))
    if result["runtime_status"]["findings"]:
        print("runtime_findings=" + " | ".join(result["runtime_status"]["findings"]))
    return 0 if result["status"] == "complete" else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    project_dir = _project(args.project)
    result = doctor_project(project_dir)
    write_json(project_dir / "doctor-report.json", result)
    print(f"status={result['status']}")
    for check in result["checks"]:
        print(f"{check['id']}={check['status']}:{check['detail']}")
    return 0 if result["status"] == "complete" else 1


def cmd_list(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "agents": sorted(agent_registry()),
        "tools": sorted(tool_registry()),
    }
    write_json(Path(args.output).resolve(), payload) if args.output else print(payload)
    return 0


def detect_tools() -> dict[str, Any]:
    detected = {}
    for tool_id, spec in tool_registry().items():
        if spec.available_command:
            detected[tool_id] = {
                "command": spec.available_command,
                "available": shutil.which(spec.available_command) is not None,
            }
        else:
            detected[tool_id] = {"command": None, "available": True}
    return detected


def verify_run(run_dir: Path) -> dict[str, Any]:
    required = [
        "work_order.json",
        "state.json",
        "spec.md",
        "clarifications.md",
        "checklist.md",
        "context-pack.json",
        "context-pack.md",
        "evidence-register.json",
        "plan.md",
        "contracts.md",
        "tasks.md",
        "analyze-report.json",
        "test-plan.md",
        "test-report.md",
        "coverage-report.json",
        "scope-inventory.json",
        "scope-validation.json",
        "docker-validation.json",
        "git-publication.json",
        "deployment-validation.json",
        "security-review.md",
        "validation-report.json",
        "traceability-matrix.md",
        "final-report.json",
        "RUN_STATE.md",
        "DECISIONS.md",
        "ERRORS.md",
        "billing-ledger.json",
        "CHECKLIST_APLICADO.md",
        "docs-validation.json",
        "traceability-validation.json",
        "assumptions-register.md",
        "executive-summary.md",
        "factory-metrics.json",
        "factory-metrics.md",
        "repair-ledger.json",
    ]
    missing = [name for name in required if not (run_dir / name).exists()]
    agents_json = run_dir / "registries" / "agents.json"
    tools_json = run_dir / "registries" / "tools.json"
    skills_json = run_dir / "registries" / "skills.json"
    if not agents_json.exists():
        missing.append("registries/agents.json")
    if not tools_json.exists():
        missing.append("registries/tools.json")
    if not skills_json.exists():
        missing.append("registries/skills.json")
    final_status = "error"
    if (run_dir / "final-report.json").exists():
        final_status = read_json(run_dir / "final-report.json").get("status", "error")
    docs_status = read_json(run_dir / "docs-validation.json").get("status", "error") if (run_dir / "docs-validation.json").exists() else "error"
    trace_status = read_json(run_dir / "traceability-validation.json").get("status", "error") if (run_dir / "traceability-validation.json").exists() else "error"
    app_audit = audit_generated_app(run_dir)
    runtime_status = audit_runtime_evidence(run_dir)
    run_policy = audit_run_policy(run_dir)
    status = "complete" if not missing and final_status == "complete" and docs_status == "complete" and trace_status == "complete" and app_audit["status"] == "complete" and runtime_status["status"] == "complete" and run_policy["status"] == "current" else "error"
    return {
        "status": status,
        "run_dir": str(run_dir),
        "missing": missing,
        "final_status": final_status,
        "docs_status": docs_status,
        "traceability_status": trace_status,
        "app_audit": app_audit,
        "runtime_status": runtime_status,
        "run_policy": run_policy,
        "agents_registered": len(read_json(agents_json)) if agents_json.exists() else 0,
        "tools_registered": len(read_json(tools_json)) if tools_json.exists() else 0,
        "skills_registered": len(read_json(skills_json)) if skills_json.exists() else 0,
    }


def audit_run_policy(run_dir: Path) -> dict[str, Any]:
    cleanup = run_dir / "generated-app-cleanup.json"
    runtime_gate = run_dir / "runtime-close-gate.json"
    if not cleanup.exists():
        return {
            "status": "legacy",
            "reason": "run creado antes de la politica de limpieza/verificacion actual; ejecuta una corrida nueva para evidencia vigente",
            "missing_current_policy_artifacts": ["generated-app-cleanup.json"],
        }
    missing = [name for name, path in {"runtime-close-gate.json": runtime_gate}.items() if not path.exists()]
    if missing:
        return {"status": "partial_current", "reason": "run no tiene todos los artefactos de cierre actuales", "missing_current_policy_artifacts": missing}
    return {"status": "current", "reason": "run contiene artefactos de politica actual", "missing_current_policy_artifacts": []}


def audit_generated_app(run_dir: Path) -> dict[str, Any]:
    app_dir = run_dir.parents[2] / "app-generada"
    findings: list[str] = []
    required_files = (
        "docker-compose.yml",
        "frontend/package.json",
        "frontend/src/app/services/feature-api.service.ts",
        "frontend/src/app/services/portal-api.service.ts",
        "backend/pom.xml",
        "backend/src/main/java/cl/benjamin/claveunica/service/PortalWorkflowService.java",
        "database/schema.sql",
        "data/openapi.yaml",
        "data/traceability-matrix.json",
        "data/requirements-model.json",
        "data/product-generation-policy.json",
        "tests/e2e.spec.ts",
        "playwright.config.ts",
    )
    if not app_dir.exists():
        return {"status": "error", "app_dir": str(app_dir), "findings": ["app-generada no existe"], "required_missing": list(required_files)}
    missing_required = [name for name in required_files if not (app_dir / name).exists()]
    findings.extend(f"falta {name}" for name in missing_required)

    pages_dir = app_dir / "frontend" / "src" / "app" / "pages"
    html_files = sorted(pages_dir.glob("*.component.html")) if pages_dir.exists() else []
    html_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in html_files)
    feature_api = _read_text(app_dir / "frontend" / "src" / "app" / "services" / "feature-api.service.ts")
    portal_api = _read_text(app_dir / "frontend" / "src" / "app" / "services" / "portal-api.service.ts")
    schema_sql = _read_text(app_dir / "database" / "schema.sql")
    frontend_text = "\n".join([html_text, feature_api, portal_api])
    forbidden_markers = {
        "Validaciones": frontend_text.count("Validaciones"),
        "Actividad reciente": frontend_text.count("Actividad reciente"),
        "screen.records": frontend_text.count("screen.records"),
        "state().db.events": frontend_text.count("state().db.events"),
        "ejecutado desde Angular": frontend_text.count("ejecutado desde Angular"),
        "/api/v1/actions": frontend_text.count("/api/v1/actions"),
        "runAction(screenRoute": frontend_text.count("runAction(screenRoute"),
    }
    for marker, count in forbidden_markers.items():
        if count:
            findings.append(f"frontend contiene {marker}: {count}")
    if "metadata JSONB NOT NULL DEFAULT '{}'" in schema_sql:
        findings.append("schema contiene tabla generica con metadata JSONB")
    if html_files and len({path.read_text(encoding="utf-8", errors="replace") for path in html_files}) < 20:
        findings.append("pantallas HTML insuficientemente diferenciadas")

    traceability = read_json(app_dir / "data" / "traceability-matrix.json") if (app_dir / "data" / "traceability-matrix.json").exists() else []
    requirements_model = read_json(app_dir / "data" / "requirements-model.json") if (app_dir / "data" / "requirements-model.json").exists() else {}
    generation_policy = read_json(app_dir / "data" / "product-generation-policy.json") if (app_dir / "data" / "product-generation-policy.json").exists() else {}
    if not isinstance(traceability, list) or len(traceability) < 30:
        findings.append("trazabilidad interna insuficiente")
    elif not all(item.get("ui_visibility") == "internal_only" for item in traceability if isinstance(item, dict)):
        findings.append("trazabilidad interna sin ui_visibility=internal_only")
    if (requirements_model.get("coverage_policy") or {}).get("frontend_must_not_render_requirement_ids") is not True:
        findings.append("requirements-model no declara frontend_must_not_render_requirement_ids=true")
    if (requirements_model.get("coverage_policy") or {}).get("product_generation_policy_required") is not True:
        findings.append("requirements-model no declara product_generation_policy_required=true")
    if generation_policy.get("status") != "complete":
        findings.append("product-generation-policy no esta complete")

    return {
        "status": "complete" if not findings else "error",
        "app_dir": str(app_dir),
        "findings": findings,
        "required_missing": missing_required,
        "html_pages": len(html_files),
        "forbidden_marker_counts": forbidden_markers,
    }


def audit_runtime_evidence(run_dir: Path) -> dict[str, Any]:
    docker_runtime = read_json(run_dir / "docker-runtime-validation.json") if (run_dir / "docker-runtime-validation.json").exists() else {}
    docker_validation = read_json(run_dir / "docker-validation.json") if (run_dir / "docker-validation.json").exists() else {}
    findings = []
    if docker_validation.get("status") not in {"complete", "runtime_complete"}:
        findings.append("docker-validation no esta complete")
    if docker_runtime.get("status") != "runtime_complete":
        findings.append("docker-runtime-validation no esta runtime_complete")
    if docker_runtime.get("playwright_status") != "complete":
        findings.append("Playwright E2E no esta complete")
    return {
        "status": "complete" if not findings else "error",
        "findings": findings,
        "docker_validation_status": docker_validation.get("status", "missing"),
        "docker_runtime_status": docker_runtime.get("status", "missing"),
        "playwright_status": docker_runtime.get("playwright_status", "missing"),
    }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def doctor_project(project_dir: Path) -> dict[str, Any]:
    checks = [
        _command_check("python", sys.executable, ["--version"]),
        _module_check("pytest", "pytest"),
        _command_check("node", "node", ["--version"]),
        _command_check("npm", "npm", ["--version"]),
        _command_check("docker", "docker", ["--version"]),
        _command_check("docker_info", "docker", ["info"]),
        _command_check("java", "java", ["--version"]),
        _command_check("maven", "mvn", ["--version"]),
        _model_provider_check(project_dir),
        _generated_app_preflight(project_dir),
    ]
    status = "complete" if all(item["status"] == "complete" for item in checks) else "warning"
    return {"status": status, "project_dir": str(project_dir), "checks": checks}


def _command_check(check_id: str, executable: str, args: list[str]) -> dict[str, Any]:
    resolved = executable if Path(executable).exists() else shutil.which(executable)
    if not resolved:
        return {"id": check_id, "status": "warning", "detail": f"{executable} no disponible"}
    try:
        completed = subprocess.run([resolved, *args], text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:
        return {"id": check_id, "status": "warning", "detail": str(exc)[:180]}
    detail = (completed.stdout or completed.stderr or "").strip().splitlines()
    return {"id": check_id, "status": "complete" if completed.returncode == 0 else "warning", "detail": detail[0][:180] if detail else f"returncode={completed.returncode}"}


def _module_check(check_id: str, module: str) -> dict[str, Any]:
    available = importlib.util.find_spec(module) is not None
    return {"id": check_id, "status": "complete" if available else "warning", "detail": "instalado" if available else f"modulo {module} no instalado"}


def _model_provider_check(project_dir: Path) -> dict[str, Any]:
    mode_path = project_dir / "secrets" / "execution-mode.local.json"
    if mode_path.exists():
        try:
            mode_config = read_json(mode_path)
            if mode_config.get("mode") == "codex_direct" and mode_config.get("allow_openai_api_calls") is False:
                return {"id": "model_provider", "status": "complete", "detail": "codex_direct activo: OpenAI API bloqueada intencionalmente"}
        except Exception:
            pass
    path = project_dir / "secrets" / "model-provider.local.json"
    if not path.exists():
        return {"id": "model_provider", "status": "warning", "detail": "model-provider.local.json no existe"}
    config = read_json(path)
    api_key_env = str(config.get("api_key_env") or "OPENAI_API_KEY")
    has_key = bool(os.environ.get(api_key_env) or _read_windows_user_env(api_key_env))
    ok = config.get("enabled") is True and config.get("provider") == "openai" and config.get("apply_model_writes") is True and has_key
    detail = f"enabled={config.get('enabled')} provider={config.get('provider')} apply_model_writes={config.get('apply_model_writes')} key_env={api_key_env} key_present={has_key}"
    return {"id": "model_provider", "status": "complete" if ok else "warning", "detail": detail}


def _generated_app_preflight(project_dir: Path) -> dict[str, Any]:
    app_dir = project_dir.parent / "app-generada"
    if not app_dir.exists():
        return {"id": "app_generada", "status": "complete", "detail": "app-generada no existe; corrida limpia posible"}
    fake_markers = 0
    product_sources = [
        app_dir / "frontend" / "src",
        app_dir / "backend" / "src",
    ]
    product_files = [
        path
        for root in product_sources
        if root.exists()
        for path in root.glob("**/*")
        if path.is_file() and path.suffix in {".ts", ".html", ".java", ".json", ".sql", ".md"}
    ]
    for pattern in ("Validaciones", "Actividad reciente", "screen.records", "/api/v1/actions"):
        fake_markers += sum(path.read_text(encoding="utf-8", errors="replace").count(pattern) for path in product_files)
    return {"id": "app_generada", "status": "complete" if fake_markers == 0 else "warning", "detail": f"marcadores_de_app_vieja={fake_markers}"}


def _read_windows_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
        return str(value) if value else None
    except OSError:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fabrica Web ARNES SDD")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-project")
    init.add_argument("--project", default="project")
    init.set_defaults(func=cmd_init_project)

    run = sub.add_parser("run")
    run.add_argument("--project", default="project")
    run.add_argument("--objective", required=True)
    run.add_argument("--phase", choices=[phase for phase, _agents in OrchestratorGraph.ROUTE])
    run.add_argument("--from-phase", choices=[phase for phase, _agents in OrchestratorGraph.ROUTE])
    run.add_argument("--clean-generated-app", action="store_true", help="Move existing app-generada into the new run backup before generation.")
    run.add_argument("--no-clean-generated-app", action="store_true", help="Keep existing app-generada even on a fresh full run.")
    run.set_defaults(func=cmd_run)

    resume = sub.add_parser("resume")
    resume.add_argument("--project", default="project")
    resume.add_argument("--run")
    resume.add_argument("--from-phase", required=True, choices=[phase for phase, _agents in OrchestratorGraph.ROUTE])
    resume.add_argument("--objective")
    resume.set_defaults(func=cmd_resume)

    verify = sub.add_parser("verify")
    verify.add_argument("--project", default="project")
    verify.add_argument("--run")
    verify.set_defaults(func=cmd_verify)

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--project", default="project")
    doctor.set_defaults(func=cmd_doctor)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--output")
    list_cmd.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
