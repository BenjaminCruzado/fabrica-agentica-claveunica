from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import write_json


MEMORY_TEMPLATE = """# Aprendizaje

## Politica

- La memoria persistente requiere MemoryGate.
- Solo se inyecta memoria aprobada, vigente, limpia y relevante.
- La memoria de fabrica, proyecto y agente se mantiene separada.
- No puede modificar policy, permisos, prompt base ni alcance sin aprobacion formal.

## Propuestas

| memory_id | scope | content | source_id | evidence_id | ttl | confidence | risk | taint_status | approval_status | rollback_id |
|---|---|---|---|---|---|---:|---|---|---|---|
"""


class MemoryGate:
    def __init__(self, factory_root: Path, project_dir: Path) -> None:
        self.factory_root = factory_root
        self.project_dir = project_dir

    def initialize(self) -> None:
        factory_memory = self.factory_root / "Aprendizaje.md"
        project_memory = self.project_dir / "Aprendizaje.md"
        if not factory_memory.exists():
            factory_memory.write_text(MEMORY_TEMPLATE, encoding="utf-8")
        if not project_memory.exists():
            project_memory.parent.mkdir(parents=True, exist_ok=True)
            project_memory.write_text(MEMORY_TEMPLATE, encoding="utf-8")
        (self.project_dir / "agent-memory").mkdir(parents=True, exist_ok=True)

    def read_report(self, run_dir: Path) -> dict[str, Any]:
        self.initialize()
        report = {
            "factory_memory": str(self.factory_root / "Aprendizaje.md"),
            "project_memory": str(self.project_dir / "Aprendizaje.md"),
            "agent_memory_dir": str(self.project_dir / "agent-memory"),
            "loaded_records": [],
            "quarantined_records": [],
            "status": "complete",
        }
        write_json(run_dir / "memory-read-report.json", report)
        return report

    def propose(self, run_dir: Path, proposal: dict[str, Any]) -> dict[str, Any]:
        required = {"proposal_id", "content", "scope", "source_id", "evidence_id", "confidence", "ttl", "risk", "taint_status", "approval_status"}
        missing = sorted(required - set(proposal))
        if missing:
            result = {"status": "error", "code": "memory_schema_invalid", "missing": missing}
        elif proposal["approval_status"] != "approved":
            result = {"status": "needs_user_input", "code": "memory_approval_required", "proposal": proposal}
        elif proposal["taint_status"] != "clean":
            result = {"status": "error", "code": "memory_tainted", "proposal": proposal}
        else:
            result = {"status": "complete", "code": "memory_proposed", "proposal": proposal}
        write_json(run_dir / "memory-proposals.json", result)
        return result
