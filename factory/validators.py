from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import FINAL_STATUSES
from .rubric import write_scope_validation
from .schemas import AGENT_RESULT_SCHEMA, CYCLE_STATE_SCHEMA, SchemaError, validate_strict


@dataclass(frozen=True)
class ValidationItem:
    validator: str
    status: str
    code: str
    message: str


class ValidatorChain:
    order = (
        "SchemaValidator",
        "EvidenceValidator",
        "PolicyValidator",
        "SafetyValidator",
        "ConsistencyValidator",
        "CoverageValidator",
        "BudgetValidator",
        "ToolOutputValidator",
        "FinalFormatValidator",
    )
    stop_on = {
        "policy_denied",
        "missing_critical_evidence",
        "unsafe_action",
        "budget_exceeded",
        "schema_unrecoverable",
    }

    def validate_state(self, state: dict[str, Any]) -> list[ValidationItem]:
        try:
            validate_strict(CYCLE_STATE_SCHEMA, state)
        except SchemaError as exc:
            return [ValidationItem("SchemaValidator", "error", "schema_unrecoverable", str(exc))]
        return [ValidationItem("SchemaValidator", "complete", "schema_valid", "CycleState valido.")]

    def validate_agent_result(self, result: dict[str, Any]) -> list[ValidationItem]:
        try:
            validate_strict(AGENT_RESULT_SCHEMA, result)
        except SchemaError as exc:
            return [ValidationItem("SchemaValidator", "error", "schema_unrecoverable", str(exc))]
        return [ValidationItem("SchemaValidator", "complete", "schema_valid", "AgentResult valido.")]

    def validate_output(
        self,
        *,
        state: dict[str, Any],
        output: dict[str, Any],
        required_gates: tuple[str, ...],
        run_dir: Path,
    ) -> list[ValidationItem]:
        items: list[ValidationItem] = []
        items.extend(self.validate_state(state))
        if any(item.code in self.stop_on for item in items):
            return items

        evidence_refs = output.get("evidence_refs", [])
        critical_claims = output.get("critical_claims", [])
        missing = [claim for claim in critical_claims if not claim.get("evidence_id")]
        if missing:
            items.append(ValidationItem("EvidenceValidator", "not_answerable", "missing_critical_evidence", "Hay claims criticos sin evidence_id."))
        elif critical_claims and not evidence_refs:
            items.append(ValidationItem("EvidenceValidator", "not_answerable", "missing_critical_evidence", "Claims criticos sin evidence_refs."))
        else:
            items.append(ValidationItem("EvidenceValidator", "complete", "evidence_valid", "Evidencia suficiente o fase no critica."))

        policy_codes = output.get("policy_findings", [])
        if any(code in {"policy_denied", "secret_detected", "unsafe_action"} for code in policy_codes):
            items.append(ValidationItem("PolicyValidator", "error", "policy_denied", "Policy finding bloqueante."))
        else:
            items.append(ValidationItem("PolicyValidator", "complete", "policy_valid", "Policy sin bloqueos."))

        unsafe_markers = ("BEGIN RSA PRIVATE KEY", "OPENAI_API_KEY", "password=", "Authorization: Bearer")
        serialized = str(output)
        if any(marker in serialized for marker in unsafe_markers):
            items.append(ValidationItem("SafetyValidator", "error", "unsafe_action", "Posible secreto detectado."))
        else:
            items.append(ValidationItem("SafetyValidator", "complete", "safety_valid", "Sin secretos obvios ni acciones inseguras."))

        if output.get("drift_detected"):
            items.append(ValidationItem("ConsistencyValidator", "error", "consistency_drift", "Drift entre spec/plan/tasks."))
        else:
            items.append(ValidationItem("ConsistencyValidator", "complete", "consistency_valid", "Artefactos consistentes."))

        if "rubric_scope" in required_gates:
            scope_validation = write_scope_validation(run_dir)
            if scope_validation["status"] != "complete":
                missing = ", ".join(f"{key}:{value}" for key, value in scope_validation["missing"].items())
                items.append(ValidationItem("CoverageValidator", "error", "rubric_scope_incomplete", f"Faltan minimos de rubrica: {missing}"))
            else:
                items.append(ValidationItem("CoverageValidator", "complete", "rubric_scope_valid", "Minimos de rubrica documentados."))

        coverage = output.get("coverage")
        if coverage == "blocked":
            items.append(ValidationItem("CoverageValidator", "error", "coverage_blocked", "Cobertura insuficiente."))
        else:
            items.append(ValidationItem("CoverageValidator", "complete", "coverage_valid", "Cobertura trazable o no aplica."))

        budget = state["budget"]
        if budget["tool_calls"] > budget["max_tool_calls"] or budget["estimated_cost_usd"] > budget["max_cost_usd"]:
            items.append(ValidationItem("BudgetValidator", "error", "budget_exceeded", "Presupuesto excedido."))
        else:
            items.append(ValidationItem("BudgetValidator", "complete", "budget_valid", "Presupuesto dentro de limite."))

        items.append(ValidationItem("ToolOutputValidator", "complete", "tool_output_valid", "Outputs de tools normalizados."))

        if "final_format" in required_gates and output.get("enforce_final_format") is True:
            required = ("final-report.json", "RUN_STATE.md", "traceability-matrix.md", "validation-report.json", "billing-ledger.json")
            missing_files = [name for name in required if not (run_dir / name).exists()]
            if missing_files:
                items.append(ValidationItem("FinalFormatValidator", "error", "format_invalid", f"Faltan artefactos: {', '.join(missing_files)}"))
            else:
                items.append(ValidationItem("FinalFormatValidator", "complete", "format_valid", "Formato final completo."))
        else:
            items.append(ValidationItem("FinalFormatValidator", "complete", "format_not_applicable", "Formato final no aplica en esta fase."))

        return items

    @staticmethod
    def status_from_items(items: list[ValidationItem]) -> str:
        for item in items:
            if item.status in FINAL_STATUSES and item.status != "complete":
                return item.status
        return "complete"

    @staticmethod
    def as_report(items: list[ValidationItem]) -> dict[str, Any]:
        return {
            "status": ValidatorChain.status_from_items(items),
            "items": [item.__dict__ for item in items],
        }
