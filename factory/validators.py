from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .constants import FINAL_STATUSES
from .rubric import write_scope_validation
from .schemas import AGENT_RESULT_SCHEMA, CYCLE_STATE_SCHEMA, SchemaError, validate_strict
from .utils import read_json


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
        blocking_policy_codes = {
            "policy_denied",
            "secret_detected",
            "unsafe_action",
            "critical_agentic_fallback",
            "app_review_failed",
            "docker_validation_failed",
            "docker_runtime_failed",
            "ux_review_failed",
            "architecture_review_failed",
            "qa_e2e_failed",
            "product_owner_review_failed",
            "model_file_policy_failed",
        }
        if any(code in blocking_policy_codes for code in policy_codes):
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

        if "agent_runtime" in required_gates:
            contract = output.get("agent_contract", {})
            runtime_plan = output.get("runtime_plan", {})
            tool_preflights = output.get("tool_preflights", [])
            runtime_errors = []
            if not contract.get("hash") or not contract.get("path"):
                runtime_errors.append("contrato operativo ausente")
            if not runtime_plan.get("steps"):
                runtime_errors.append("plan runtime ausente")
            if not isinstance(tool_preflights, list):
                runtime_errors.append("preflight de herramientas ausente")
            if runtime_errors:
                items.append(ValidationItem("RuntimeValidator", "error", "agent_runtime_invalid", "; ".join(runtime_errors)))
            else:
                items.append(ValidationItem("RuntimeValidator", "complete", "agent_runtime_valid", "Agente paso por contrato, plan runtime y preflight de herramientas."))

        if "ai_code_writer" in required_gates:
            writer = output.get("ai_code_writer", {})
            writer_errors = []
            if not isinstance(writer, dict) or writer.get("mode") != "ai_code_writer_controlled":
                writer_errors.append("bitacora ai_code_writer ausente")
            else:
                if output.get("execution_mode") == "agentic" and writer.get("model_adapter") == "openai-responses" and writer.get("apply_writes") is not True:
                    writer_errors.append("apply_model_writes debe estar activo para agentes codificadores en modo agentic")
                if int(writer.get("failed_writes") or 0) > 0:
                    writer_errors.append("la IA intento escribir archivos bloqueados por SafeFileWriter")
                roots = writer.get("allowed_write_roots", [])
                if not isinstance(roots, list) or "app-generada" not in roots:
                    writer_errors.append("raices permitidas de escritura no declaradas")
            if writer_errors:
                items.append(ValidationItem("RuntimeValidator", "error", "ai_code_writer_invalid", "; ".join(writer_errors)))
            else:
                items.append(ValidationItem("RuntimeValidator", "complete", "ai_code_writer_valid", "Escritura IA gobernada por SafeFileWriter y ledger."))

        if "rubric_scope" in required_gates:
            scope_validation = write_scope_validation(run_dir)
            if scope_validation["status"] != "complete":
                missing = ", ".join(f"{key}:{value}" for key, value in scope_validation["missing"].items())
                items.append(ValidationItem("CoverageValidator", "error", "rubric_scope_incomplete", f"Faltan minimos de rubrica: {missing}"))
            else:
                items.append(ValidationItem("CoverageValidator", "complete", "rubric_scope_valid", "Minimos de rubrica documentados."))

        if "scope_realism" in required_gates:
            scope_path = run_dir / "scope-inventory.json"
            scope_errors = []
            if not scope_path.exists():
                scope_errors.append("scope-inventory.json no existe")
            else:
                scope = json.loads(scope_path.read_text(encoding="utf-8"))
                endpoints = scope.get("api_endpoints", [])
                tables = scope.get("tables", [])
                screens = scope.get("screens", [])
                rules = scope.get("business_rules", [])
                checks = scope.get("validations_checks", [])
                traceability = scope.get("traceability", [])
                endpoint_paths = [item.get("path", "") for item in endpoints if isinstance(item, dict)]
                table_names = [item.get("table", "") for item in tables if isinstance(item, dict)]
                screen_routes = [item.get("route", "") for item in screens if isinstance(item, dict)]
                rule_text = "\n".join(item.get("rule", "") for item in rules if isinstance(item, dict))
                check_text = "\n".join(item.get("check", "") for item in checks if isinstance(item, dict))
                if not endpoint_paths or any("/recurso-" in path or "{module}" in path for path in endpoint_paths):
                    scope_errors.append("endpoints genericos en alcance")
                if not table_names or any(name.endswith(tuple(f"_{index:02d}" for index in range(1, 41))) for name in table_names):
                    scope_errors.append("tablas de alcance genericas")
                if len(set(screen_routes)) < 30 or any("/vista-" in route for route in screen_routes):
                    scope_errors.append("pantallas de alcance genericas o clonadas")
                if "Regla funcional" in rule_text or "Validacion 0" in check_text:
                    scope_errors.append("reglas/checks numericos sin dominio")
                if len(traceability) < 40:
                    scope_errors.append("trazabilidad scope->pantalla->endpoint->tabla insuficiente")
                if scope.get("domain_blueprint", {}).get("quality_bar") != "local_functional_app":
                    scope_errors.append("domain_blueprint sin quality_bar local_functional_app")
            if scope_errors:
                items.append(ValidationItem("CoverageValidator", "error", "scope_realism_failed", "; ".join(scope_errors)))
            else:
                items.append(ValidationItem("CoverageValidator", "complete", "scope_realism_valid", "Alcance deriva de dominio, pantallas, endpoints, tablas y trazabilidad real."))

        coverage = output.get("coverage")
        if coverage == "blocked":
            items.append(ValidationItem("CoverageValidator", "error", "coverage_blocked", "Cobertura insuficiente."))
        elif coverage == "needs_user_input":
            items.append(ValidationItem("CoverageValidator", "needs_user_input", "coverage_needs_runtime", "Cobertura requiere ejecutar build/runtime autorizado para cerrar como complete."))
        else:
            items.append(ValidationItem("CoverageValidator", "complete", "coverage_valid", "Cobertura trazable o no aplica."))

        if "app_realism" in required_gates:
            app_dir = run_dir.parents[2] / "app-generada"
            pages_dir = app_dir / "frontend" / "src" / "app" / "pages"
            controller_path = app_dir / "backend" / "src" / "main" / "java" / "cl" / "benjamin" / "claveunica" / "controller" / "PortalController.java"
            service_path = app_dir / "backend" / "src" / "main" / "java" / "cl" / "benjamin" / "claveunica" / "service" / "PortalWorkflowService.java"
            integration_test_path = app_dir / "backend" / "src" / "test" / "java" / "cl" / "benjamin" / "claveunica" / "PortalWorkflowServiceTest.java"
            migration_path = app_dir / "backend" / "src" / "main" / "resources" / "db" / "migration" / "V1__init_claveunica_domain.sql"
            schema_path = app_dir / "database" / "schema.sql"
            openapi_path = app_dir / "data" / "openapi.yaml"
            features_dir = app_dir / "frontend" / "src" / "app" / "features"
            feature_api_path = app_dir / "frontend" / "src" / "app" / "services" / "feature-api.service.ts"
            portal_api_path = app_dir / "frontend" / "src" / "app" / "services" / "portal-api.service.ts"
            html_files = sorted(pages_dir.glob("*.component.html")) if pages_dir.exists() else []
            html_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in html_files}
            html_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in html_files)
            controller = controller_path.read_text(encoding="utf-8") if controller_path.exists() else ""
            service = service_path.read_text(encoding="utf-8") if service_path.exists() else ""
            integration_test = integration_test_path.read_text(encoding="utf-8") if integration_test_path.exists() else ""
            migration = migration_path.read_text(encoding="utf-8") if migration_path.exists() else ""
            openapi = openapi_path.read_text(encoding="utf-8") if openapi_path.exists() else ""
            feature_api = feature_api_path.read_text(encoding="utf-8") if feature_api_path.exists() else ""
            portal_api = portal_api_path.read_text(encoding="utf-8") if portal_api_path.exists() else ""
            schema_sql = schema_path.read_text(encoding="utf-8") if schema_path.exists() else ""
            feature_dirs = [path for path in features_dir.iterdir() if path.is_dir()] if features_dir.exists() else []
            realism_errors = []
            if len(html_files) < 30 or len(html_hashes) < 20:
                realism_errors.append("pantallas clonadas o insuficientes")
            if "PortalWorkflowService" not in controller or "@Valid" not in controller or "@Transactional" not in service or "jdbc.update" not in service:
                realism_errors.append("API sin persistencia verificable")
            if len(feature_dirs) < 6 or "runFeatureAction" not in feature_api:
                realism_errors.append("frontend sin features/API por dominio")
            if feature_dirs and not all((path / "models").exists() and (path / "services").exists() and (path / "components").exists() for path in feature_dirs):
                realism_errors.append("features frontend sin models/services/components")
            if "Testcontainers" not in integration_test or "createProcedurePersistsAndUpdatesDashboard" not in integration_test:
                realism_errors.append("backend sin prueba de integracion persistente")
            if "CREATE TABLE citizens" not in migration or "INSERT INTO citizens" not in migration:
                realism_errors.append("migracion Flyway ausente o incompleta")
            if "openapi: 3.1.0" not in openapi or "/api/v1/procedures" not in openapi:
                realism_errors.append("contrato OpenAPI no generado desde catalogo")
            if "endpoint01()" in controller or 'Map.of("screen"' in controller:
                realism_errors.append("endpoints decorativos detectados")
            if "metadata JSONB NOT NULL DEFAULT '{}'" in schema_sql:
                realism_errors.append("tablas genericas de relleno detectadas")
            if "CREATE INDEX" not in schema_sql or "CHECK (status IN" not in schema_sql:
                realism_errors.append("schema sin constraints o indices de dominio")
            debug_markers = ("<h2>Validaciones</h2>", "Actividad reciente", "implementa campos", "ejecutado desde Angular", "screen.records")
            if any(marker in html_text or marker in feature_api or marker in portal_api for marker in debug_markers):
                realism_errors.append("frontend expone artefactos de generador o datos estaticos")
            frontend_text = "\n".join([html_text, feature_api, portal_api])
            if re.search(r"\b(CU|FUN|FT|RN|CH|EX|ACT|REQ)_[A-Z0-9_]*\b", frontend_text) or re.search(r"traceability|trazabilidad", frontend_text, re.IGNORECASE):
                realism_errors.append("frontend expone IDs o trazabilidad interna de requisitos")
            if "state().db.events" in html_text:
                realism_errors.append("audit log global visible fuera de pantallas de auditoria")
            if "/api/v1/actions" in feature_api or "runAction(screenRoute" in portal_api:
                realism_errors.append("acciones frontend dependen de endpoint generico")
            if "rowsForFeature" not in portal_api or "statusMessageForFeature" not in portal_api:
                realism_errors.append("frontend no deriva datos visibles desde estado API")
            traceability_path = app_dir / "data" / "traceability-matrix.json"
            requirements_model_path = app_dir / "data" / "requirements-model.json"
            traceability = read_json(traceability_path) if traceability_path.exists() else []
            requirements_model = read_json(requirements_model_path) if requirements_model_path.exists() else {}
            if not isinstance(traceability, list) or len(traceability) < 30:
                realism_errors.append("trazabilidad interna requisito->pantalla->accion->endpoint->tabla->test insuficiente")
            elif not all(item.get("ui_visibility") == "internal_only" for item in traceability if isinstance(item, dict)):
                realism_errors.append("trazabilidad interna sin marca internal_only")
            if (requirements_model.get("coverage_policy") or {}).get("frontend_must_not_render_requirement_ids") is not True:
                realism_errors.append("modelo de requisitos no bloquea IDs visibles en frontend")
            if state.get("phase") == "containerize":
                docker_validation = read_json(run_dir / "docker-validation.json") if (run_dir / "docker-validation.json").exists() else {}
                if docker_validation.get("status") not in {"complete", "runtime_complete"}:
                    realism_errors.append("docker compose no validado para el stack generado")
                docker_runtime = read_json(run_dir / "docker-runtime-validation.json") if (run_dir / "docker-runtime-validation.json").exists() else {}
                if docker_runtime.get("status") != "runtime_complete":
                    realism_errors.append("docker runtime build/up/health/e2e no ejecutado correctamente")
                if docker_runtime.get("playwright_status") != "complete":
                    realism_errors.append("Playwright E2E no ejecutado correctamente")
            if realism_errors:
                items.append(ValidationItem("CoverageValidator", "error", "app_realism_failed", "; ".join(realism_errors)))
            else:
                items.append(ValidationItem("CoverageValidator", "complete", "app_realism_valid", "App local con UI diferenciada, API persistente y schema de dominio."))

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
