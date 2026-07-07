from __future__ import annotations

from pathlib import Path
from typing import Any

from .rubric import validate_scope_inventory
from .utils import read_json, write_json


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
        "timing": {
            "started_at": None,
            "finished_at": None,
            "duration_seconds": "not_available",
            "note": "La version actual registra eventos, pero no persiste timestamps normalizados de inicio/fin en state.json.",
        },
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
