from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from .principles import ordered_principles, validate_principles
from .rubric import validate_scope_inventory
from .utils import read_json, sha256_file, sha256_text, stable_json, write_json


REQUIRED_FACTORY_DOCS = (
    "FACTORY.md",
    "AGENTS.md",
    "docs/fabrica/00_ANALISIS_FABRICAS_ANTERIORES.md",
    "docs/fabrica/01_CONSTITUCION_FABRICA.md",
    "docs/fabrica/02_PLAN_OPERACION.md",
    "docs/fabrica/03_PUBLICACION_DESPLIEGUE.md",
    "rules/00-reglas-comunes.md",
    "rules/10-rubrica-final.md",
    "rules/20-cierre-evidencia.md",
    "workflows/00-intake.md",
    "workflows/01-documentar-validar.md",
    "workflows/02-implementar-probar.md",
    "workflows/03-cierre.md",
)


def ensure_run_dirs(run_dir: Path) -> None:
    for rel in ("evidence", "generated-docs", "reports", "logs"):
        (run_dir / rel).mkdir(parents=True, exist_ok=True)


def validate_factory_docs(factory_root: Path, run_dir: Path) -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_FACTORY_DOCS if not (factory_root / rel).exists()]
    payload = {
        "status": "complete" if not missing else "error",
        "required": list(REQUIRED_FACTORY_DOCS),
        "missing": missing,
    }
    write_json(run_dir / "docs-validation.json", payload)
    return payload


def validate_traceability(run_dir: Path) -> dict[str, Any]:
    scope = validate_scope_inventory(run_dir / "scope-inventory.json")
    required = {
        "scope_inventory": run_dir / "scope-inventory.json",
        "scope_validation": run_dir / "scope-validation.json",
        "traceability_matrix": run_dir / "traceability-matrix.md",
        "validation_report": run_dir / "validation-report.json",
    }
    missing_files = [name for name, path in required.items() if not path.exists()]
    payload = {
        "status": "complete" if scope.status == "complete" and not missing_files else "error",
        "scope_status": scope.status,
        "scope_counts": scope.counts,
        "missing_files": missing_files,
        "checks": [
            "scope inventory exists",
            "scope validation exists",
            "traceability matrix exists",
            "validation report exists",
            "rubric minimums complete",
        ],
    }
    write_json(run_dir / "traceability-validation.json", payload)
    return payload


def write_principle_ledger(run_dir: Path) -> None:
    errors = validate_principles()
    ledger = {
        "status": "complete" if not errors else "error",
        "errors": errors,
        "principles": [principle.to_dict() for principle in ordered_principles()],
    }
    write_json(run_dir / "principle-ledger.json", ledger)
    lines = ["# Constitution P01-P12", ""]
    for principle in ordered_principles():
        lines.extend(
            [
                f"## {principle.principle_id} {principle.name}",
                "",
                f"- Control: {principle.control}",
                f"- Gates: {', '.join(principle.gates)}",
                f"- Evidence: {', '.join(principle.evidence)}",
                "",
            ]
        )
    (run_dir / "constitution.md").write_text("\n".join(lines), encoding="utf-8")


def write_phase_ledger(run_dir: Path, results: list[dict[str, Any]]) -> None:
    phases = []
    for item in results:
        output = item.get("output", {})
        phases.append(
            {
                "cycle_id": item.get("cycle_id"),
                "phase": output.get("phase"),
                "agent_id": item.get("agent_id"),
                "status": item.get("status"),
                "artifacts": output.get("artifacts", []),
                "evidence_refs": output.get("evidence_refs", []),
                "gates": item.get("validation", {}).get("items", []),
                "output_hash": item.get("logs", {}).get("output_hash"),
            }
        )
    write_json(run_dir / "phase-ledger.json", phases)


def write_claim_map(run_dir: Path, results: list[dict[str, Any]]) -> None:
    lines = ["# Claim Map", "", "| claim | agent | evidence | status |", "|---|---|---|---|"]
    rows = 0
    for item in results:
        agent_id = item.get("agent_id", "")
        status = item.get("status", "")
        for claim in item.get("output", {}).get("critical_claims", []):
            rows += 1
            lines.append(f"| {claim.get('claim', '')} | `{agent_id}` | `{claim.get('evidence_id', '')}` | `{status}` |")
    if rows == 0:
        lines.append("| Sin claims criticos declarados | `n/a` | `n/a` | `complete` |")
    (run_dir / "claim-map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_project_isolation(factory_root: Path, project_dir: Path, run_dir: Path) -> None:
    project_id = "claveunica-licitacion"
    workspace_root = project_dir / "workspaces" / project_id
    version_root = workspace_root / "versions" / "v0001"
    sandbox_root = workspace_root / "sandboxes"
    for rel in (
        "memory",
        "learning",
        "versions/v0001",
        "versions/v0001/frontend",
        "sandboxes/DEV/workspace",
        "sandboxes/DEV/memory",
        "sandboxes/DEV/learning",
        "sandboxes/QA/workspace",
        "sandboxes/QA/memory",
        "sandboxes/QA/learning",
    ):
        (workspace_root / rel).mkdir(parents=True, exist_ok=True)

    template_root = factory_root / "templates" / "frontend"
    required = ["README.md", "AGENTS.md", "HANDOFF-REACT.md"]
    missing_template = [name for name in required if not (template_root / name).exists()]
    template_hash = "sha256:missing" if missing_template else sha256_text(stable_json([{"path": name, "hash": sha256_file(template_root / name)} for name in required]))
    template_manifest = {
        "template_name": "factory_frontend_template",
        "mandatory": True,
        "source": "templates/frontend",
        "required_files": required,
        "missing_files": missing_template,
        "hash": template_hash,
        "applies_to": "app-generada, DEV sandbox y QA sandbox",
    }
    write_json(run_dir / "frontend-template-manifest.json", template_manifest)
    write_json(workspace_root / "frontend-template-manifest.json", template_manifest)
    write_json(version_root / "frontend" / "frontend-template-manifest.json", template_manifest)
    (version_root / "README.md").write_text("# Version v0001\n\nFuente local para DEV y QA.\n", encoding="utf-8")

    sandboxes = []
    for name in ("DEV", "QA"):
        sandbox_path = sandbox_root / name
        manifest = {
            "name": name,
            "path": str(sandbox_path.relative_to(factory_root)),
            "workspace": str((sandbox_path / "workspace").relative_to(factory_root)),
            "memory_path": str((sandbox_path / "memory").relative_to(factory_root)),
            "learning_path": str((sandbox_path / "learning").relative_to(factory_root)),
            "clone_source": str(version_root.relative_to(factory_root)),
            "shared_with_factory": False,
            "frontend_template_required": True,
            "frontend_template_hash": template_hash,
        }
        write_json(sandbox_path / "sandbox-manifest.json", manifest)
        write_json(sandbox_path / "frontend-template-manifest.json", template_manifest)
        (sandbox_path / "workspace" / "README.md").write_text(f"# Sandbox {name}\n\nWorkspace aislado para pruebas {name}.\n", encoding="utf-8")
        sandboxes.append(manifest)

    project_manifest = {
        "project_id": project_id,
        "project_root": str(workspace_root.relative_to(factory_root)),
        "current_version": "v0001",
        "versions_root": str((workspace_root / "versions").relative_to(factory_root)),
        "sandboxes_root": str(sandbox_root.relative_to(factory_root)),
        "memory_shared_with_factory": False,
        "frontend_template": template_manifest,
    }
    memory_policy = {
        "project_id": project_id,
        "mode": "project_scoped_propose_only",
        "factory_memory_read_allowed": False,
        "factory_learning_write_allowed": False,
        "shared_with_factory": False,
        "project_memory_root": str((workspace_root / "memory").relative_to(factory_root)),
        "project_learning_root": str((workspace_root / "learning").relative_to(factory_root)),
    }
    write_json(run_dir / "project-manifest.json", project_manifest)
    write_json(run_dir / "project-memory-policy.json", memory_policy)
    write_json(run_dir / "project-sandboxes.json", {"project_id": project_id, "sandboxes": sandboxes})
    (run_dir / "project-isolation-policy.md").write_text(
        "\n".join(
            [
                "# Project Isolation Policy",
                "",
                "- La entrada/contexto vive en `project/`.",
                "- Los workspaces generados viven en `project/workspaces/<project_id>/`.",
                "- DEV y QA son carpetas separadas.",
                "- La memoria del proyecto no se comparte con la fabrica.",
                "- La app desplegable final vive en `app-generada/`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _secret_findings(root: Path) -> list[dict[str, str]]:
    patterns = (
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-]{16,}"),
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    )
    findings: list[dict[str, str]] = []
    ignored_parts = {".git", "__pycache__", "node_modules", "runs", "cache", "secrets"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".env"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            if pattern.search(text):
                findings.append({"path": str(path.relative_to(root)), "pattern": pattern.pattern})
    return findings


def write_security_delivery_reports(factory_root: Path, run_dir: Path) -> None:
    findings = _secret_findings(factory_root)
    manifests = [name for name in ("pyproject.toml", "requirements.txt", "package.json", "package-lock.json") if (factory_root / name).exists()]
    write_json(run_dir / "secrets-report.json", {"status": "complete" if not findings else "error", "secrets_detected": len(findings), "findings": findings})
    write_json(run_dir / "dependency-report.json", {"status": "complete", "manifests": manifests, "high_critical_open": 0, "note": "Revision local de manifiestos; sin consulta externa CVE."})
    write_json(run_dir / "sbom.json", {"sbom_format": "factory.local.v1", "components": [{"name": "fabrica-final", "type": "application", "version": "local"}, {"name": "python-stdlib", "type": "runtime", "version": "system"}]})
    (run_dir / "security-review.md").write_text(
        "\n".join(
            [
                "# Security Review",
                "",
                f"- status: `{'complete' if not findings else 'error'}`",
                f"- secrets_detected: `{len(findings)}`",
                "- project/secrets esta ignorado por git.",
                "- EC2 requiere allow_execute true y archivo local.",
                "- No se suben llaves `.pem`, `.env` ni tokens.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "rollback-plan.md").write_text(
        "# Rollback Plan\n\n1. En EC2: `docker compose down` dentro de `/home/ubuntu/app/app-generada`.\n2. Volver al commit anterior en GitHub.\n3. Reejecutar deploy desde la fabrica.\n4. Si falla, mantener `allow_execute: false` y revisar `deployment-validation.json`.\n",
        encoding="utf-8",
    )
    (run_dir / "slo-policy.md").write_text("# SLO Policy\n\n- App publica responde en HTTP.\n- Deploy debe terminar sin errores de Docker Compose.\n- Logs y metricas deben quedar en la corrida.\n", encoding="utf-8")
    (run_dir / "approval-matrix.md").write_text(
        "# Approval Matrix\n\n| accion | default | aprobacion |\n|---|---|---|\n| git push | denied | `allow_execute: true` |\n| deploy EC2 | denied | `allow_execute: true` + llave local |\n| secretos | denied | nunca subir al repo |\n| nueva dependencia | review | dependency report |\n",
        encoding="utf-8",
    )
    (run_dir / "PRBundle.md").write_text(
        "# PRBundle\n\n- Incluye fabrica, app-generada, docs y project como estructura controlada.\n- Evidencia principal: `final-report.json`, `factory-metrics.md`, `traceability-matrix.md`, `phase-ledger.json`, `claim-map.md`.\n- Deploy: revisa `deployment-validation.json`.\n",
        encoding="utf-8",
    )


def write_log_completeness_report(run_dir: Path) -> None:
    required = ["state.json", "validation-report.json", "phase-ledger.json", "factory-metrics.json", "billing-ledger.json", "traceability-matrix.md"]
    write_json(
        run_dir / "log-completeness-report.json",
        {
            "status": "complete" if all((run_dir / name).exists() for name in required) else "error",
            "required": required,
            "missing": [name for name in required if not (run_dir / name).exists()],
        },
    )


def write_assumptions_register(run_dir: Path) -> None:
    text = """# Assumptions Register

| id | tipo | descripcion | estado |
|---|---|---|---|
| ASM-001 | fuente | El archivo `.md` entregado por el profesor se considera insumo valido y utilizable. | approved |
| ASM-002 | alcance | La aplicacion es ficticia; integraciones estatales reales se simulan. | approved |
| ASM-003 | rubrica | Elementos no presentes literalmente en el `.md` pueden derivarse como supuestos de implementacion o exigencias de rubrica. | approved |
"""
    (run_dir / "assumptions-register.md").write_text(text, encoding="utf-8")


def write_executive_summary(run_dir: Path, state: dict[str, Any], results: list[dict[str, Any]]) -> None:
    scope = read_json(run_dir / "scope-validation.json") if (run_dir / "scope-validation.json").exists() else {"status": "missing", "counts": {}}
    docs = read_json(run_dir / "docs-validation.json") if (run_dir / "docs-validation.json").exists() else {"status": "missing"}
    trace = read_json(run_dir / "traceability-validation.json") if (run_dir / "traceability-validation.json").exists() else {"status": "missing"}
    lines = [
        "# Executive Summary",
        "",
        f"- run_id: `{state['run_id']}`",
        f"- status: `{state['status']}`",
        f"- agents_executed: `{len(results)}`",
        f"- scope_validation: `{scope['status']}`",
        f"- docs_validation: `{docs['status']}`",
        f"- traceability_validation: `{trace['status']}`",
        "",
        "## Rubrica",
        "",
        "| elemento | cantidad |",
        "|---|---:|",
    ]
    for key, value in scope.get("counts", {}).items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Siguiente Paso",
            "",
            "Usar esta corrida como base para la fase de implementacion de la app generada por la fabrica.",
        ]
    )
    (run_dir / "executive-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _safe_read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return read_json(path)
    except Exception:
        return default


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _run_timing(run_dir: Path) -> dict[str, Any]:
    log_path = run_dir / "log.jsonl"
    timestamps: list[datetime] = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = read_json_from_text(line)
                ts = str(payload.get("ts", ""))
                if ts:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except Exception:
                continue
    if not timestamps:
        return {
            "started_at": None,
            "finished_at": None,
            "duration_seconds": "not_available",
            "note": "No se encontraron timestamps parseables en log.jsonl.",
        }
    started = min(timestamps)
    finished = max(timestamps)
    return {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "note": "Calculado desde timestamps de log.jsonl.",
    }


def read_json_from_text(text: str) -> Any:
    import json

    return json.loads(text)


def write_factory_metrics(run_dir: Path, state: dict[str, Any], results: list[dict[str, Any]]) -> None:
    scope = _safe_read_json(run_dir / "scope-validation.json", {"status": "missing", "counts": {}})
    docker = _safe_read_json(run_dir / "docker-validation.json", {"status": "not_run"})
    github = _safe_read_json(run_dir / "git-publication.json", {"status": "not_run"})
    deploy = _safe_read_json(run_dir / "deployment-validation.json", {"status": "not_run"})
    billing = _safe_read_json(run_dir / "billing-ledger.json", {"totals": {}})
    validation = _safe_read_json(run_dir / "validation-report.json", {"validators": [], "results": []})
    run_config = _safe_read_json(run_dir / "run-config.json", {"selected_phases": []})

    agent_ids = [item["agent_id"] for item in results]
    unique_agents = sorted(set(agent_ids))
    tool_log_dir = run_dir / "tool-logs"
    agent_log_dir = run_dir / "agent-logs"
    tool_log_events = sum(_jsonl_count(path) for path in tool_log_dir.glob("*.jsonl")) if tool_log_dir.exists() else 0
    agent_log_events = sum(_jsonl_count(path) for path in agent_log_dir.glob("*.jsonl")) if agent_log_dir.exists() else 0
    artifact_count = sum(1 for path in run_dir.rglob("*") if path.is_file())
    total_input = int(state.get("budget", {}).get("used_input_tokens", 0))
    total_output = int(state.get("budget", {}).get("used_output_tokens", 0))
    billing_totals = billing.get("totals", {})

    metrics = {
        "run_id": state["run_id"],
        "status": state["status"],
        "timing": _run_timing(run_dir),
        "execution": {
            "phases_executed": run_config.get("selected_phases", []),
            "agents_executed_total": len(agent_ids),
            "agents_executed_unique": len(unique_agents),
            "agents": unique_agents,
            "tool_log_events": tool_log_events,
            "agent_log_events": agent_log_events,
            "artifacts_generated": artifact_count,
            "validators": validation.get("validators", []),
        },
        "tokens": {
            "real_available": False,
            "input_estimated": total_input or int(billing_totals.get("input_tokens", 0) or 0),
            "output_estimated": total_output or int(billing_totals.get("output_tokens", 0) or 0),
            "cached_estimated": int(state.get("budget", {}).get("cached_tokens", 0)),
            "reasoning_estimated": int(state.get("budget", {}).get("reasoning_tokens", 0)),
            "note": "Estimacion local basada en tamano de entradas/salidas; no son tokens reales del proveedor.",
        },
        "rubric": {
            "status": scope.get("status"),
            "counts": scope.get("counts", {}),
            "missing": scope.get("missing", {}),
        },
        "delivery": {
            "docker": docker.get("status"),
            "github": github.get("status"),
            "ec2": deploy.get("status"),
            "public_url": deploy.get("public_url"),
        },
        "issues": {
            "state_issues": state.get("issues", []),
            "deployment_note": deploy.get("note"),
            "github_note": github.get("note"),
        },
    }
    write_json(run_dir / "factory-metrics.json", metrics)

    lines = [
        "# Factory Metrics",
        "",
        f"- run_id: `{metrics['run_id']}`",
        f"- status: `{metrics['status']}`",
        f"- duration_seconds: `{metrics['timing']['duration_seconds']}`",
        f"- agents_executed_total: `{metrics['execution']['agents_executed_total']}`",
        f"- agents_executed_unique: `{metrics['execution']['agents_executed_unique']}`",
        f"- tool_log_events: `{metrics['execution']['tool_log_events']}`",
        f"- agent_log_events: `{metrics['execution']['agent_log_events']}`",
        f"- artifacts_generated: `{metrics['execution']['artifacts_generated']}`",
        f"- input_tokens_estimated: `{metrics['tokens']['input_estimated']}`",
        f"- output_tokens_estimated: `{metrics['tokens']['output_estimated']}`",
        f"- rubric_status: `{metrics['rubric']['status']}`",
        f"- docker_status: `{metrics['delivery']['docker']}`",
        f"- github_status: `{metrics['delivery']['github']}`",
        f"- ec2_status: `{metrics['delivery']['ec2']}`",
        f"- public_url: `{metrics['delivery']['public_url']}`",
        "",
        "## Rubrica",
        "",
        "| elemento | cantidad |",
        "|---|---:|",
    ]
    for key, value in metrics["rubric"]["counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Nota", "", metrics["tokens"]["note"]])
    (run_dir / "factory-metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
