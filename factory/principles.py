from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Principle:
    principle_id: str
    name: str
    control: str
    gates: tuple[str, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


PRINCIPLES: dict[str, Principle] = {
    "P01": Principle("P01", "Reproducibilidad", "Workflow versionado, hashes y rutas de corrida cerradas.", ("schema", "budget", "final_format"), ("state.json", "workflow.yaml", "factory-metrics.json")),
    "P02": Principle("P02", "No invencion", "Claims criticos deben apuntar a evidencia o quedar bloqueados.", ("evidence", "context"), ("evidence-register.json", "claim-map.md")),
    "P03": Principle("P03", "Contexto limpio", "Context pack compacto, cacheado y sin secretos.", ("context", "safety", "secrets"), ("context-pack.json", "secrets-report.json")),
    "P04": Principle("P04", "RAG/cache", "Indice local con hashes y cache por entrada.", ("context", "budget"), ("context-pack.json", "cache-report.json")),
    "P05": Principle("P05", "Arnes y agentes", "Todo agente corre por HarnessRunner y registro allowlist.", ("policy", "schema"), ("registries/agents.json", "agent-manifest.json")),
    "P06": Principle("P06", "Tools deterministicas", "Tools allowlist con logs y presupuesto.", ("tool-output", "tests"), ("registries/tools.json", "tool-logs")),
    "P07": Principle("P07", "Aprendizaje gobernado", "Memoria de proyecto separada y propuesta, no activacion automatica.", ("memory", "human_approval"), ("../Aprendizaje.md", "memory-report.json")),
    "P08": Principle("P08", "Gates por fase", "Cada fase deja estado, validacion y evidencia.", ("coverage", "consistency"), ("phase-ledger.json", "validation-report.json")),
    "P09": Principle("P09", "Trazabilidad", "Relacion entre requisitos, tareas, pruebas, evidencia y metricas.", ("observability",), ("traceability-matrix.md", "log-completeness-report.json")),
    "P10": Principle("P10", "SDD completo", "Spec, plan, tasks, implementacion, validacion, deploy y cierre.", ("plan", "tasks", "final_format"), ("spec.md", "plan.md", "tasks.md", "final-report.json")),
    "P11": Principle("P11", "Publicacion gobernada", "GitHub y EC2 solo con configuracion local y aprobacion explicita.", ("human_approval", "policy"), ("git-publication.json", "deployment-validation.json", "approval-matrix.md")),
    "P12": Principle("P12", "Seguridad operacional", "Secret scan, dependencias, SBOM, rollback y SLOs.", ("security", "dependency", "rollback"), ("security-review.md", "dependency-report.json", "sbom.json", "rollback-plan.md")),
}


def ordered_principles() -> list[Principle]:
    return [PRINCIPLES[f"P{i:02d}"] for i in range(1, 13)]


def validate_principles() -> list[str]:
    errors: list[str] = []
    expected = [f"P{i:02d}" for i in range(1, 13)]
    if list(PRINCIPLES) != expected:
        errors.append("Principios P01-P12 incompletos o fuera de orden.")
    for principle in PRINCIPLES.values():
        if not principle.gates:
            errors.append(f"{principle.principle_id} sin gates.")
        if not principle.evidence:
            errors.append(f"{principle.principle_id} sin evidencia.")
    return errors
