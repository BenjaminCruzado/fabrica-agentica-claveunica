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
