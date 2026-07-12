from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .constants import MODEL_SEED, MODEL_SNAPSHOT


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    name: str
    version: str
    purpose: str
    type: str
    permissions: tuple[str, ...]
    side_effects: str
    sandbox_required: bool
    idempotent: bool
    timeout_ms: int
    max_retries: int
    cost_class: str
    available_command: str | None = None


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    type: str
    purpose: str
    tool_id: str | None
    cache_key: str
    gates: tuple[str, ...]


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    agent_name: str
    version: str
    owner: str
    status: str
    purpose: str
    single_responsibility: str
    use_when: tuple[str, ...]
    do_not_use_when: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    permissions: dict[str, bool]
    model_policy: dict[str, Any]
    budget: dict[str, int]
    memory: dict[str, Any]
    gates: tuple[str, ...]
    rollback: str = "discard_agent_output"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BASE_FORBIDDEN_TOOLS = (
    "shell.free",
    "secrets.read",
    "deploy.direct",
    "memory.write_ungated",
    "external.write_unapproved",
    "db.write",
)


def _model_policy() -> dict[str, Any]:
    return {
        "model": MODEL_SNAPSHOT,
        "temperature": 0,
        "top_p": 1,
        "seed": MODEL_SEED,
        "parallel_tool_calls": False,
        "response_format": "strict_json_schema",
    }


def _budget(level: str) -> dict[str, int]:
    values = {
        "bajo": (4000, 1200, 2, 1, 30000),
        "medio": (8000, 2000, 3, 1, 45000),
        "alto": (12000, 3000, 5, 1, 90000),
    }[level]
    return {
        "max_input_tokens": values[0],
        "max_output_tokens": values[1],
        "max_tool_calls": values[2],
        "max_retries": values[3],
        "timeout_ms": values[4],
    }


def _permissions(**overrides: bool) -> dict[str, bool]:
    base = {
        "read_repo": False,
        "write_files": False,
        "run_tests": False,
        "external_api": False,
        "deploy": False,
        "read_secrets": False,
        "write_memory": False,
    }
    base.update(overrides)
    return base


def tool_registry() -> dict[str, ToolSpec]:
    specs = [
        ToolSpec("tool.files.read", "Files Read", "1.0.0", "Leer archivos autorizados.", "file_read", ("read",), "read", True, True, 10000, 1, "free"),
        ToolSpec("tool.files.write_dry_run", "Files Write Dry Run", "1.0.0", "Materializar artefactos dentro del proyecto sandbox.", "file_write_dry_run", ("write_sandbox",), "write_preview", True, True, 10000, 1, "free"),
        ToolSpec("tool.index.query", "Index Query", "1.0.0", "Consultar indice documental versionado.", "retrieval", ("read_index",), "read", True, True, 15000, 1, "free"),
        ToolSpec("tool.cache.get", "Cache Get", "1.0.0", "Leer cache no sensible.", "retrieval", ("read_cache",), "read", True, True, 2000, 0, "free"),
        ToolSpec("tool.cache.set", "Cache Set", "1.0.0", "Guardar cache no sensible.", "compute", ("write_cache",), "write", True, True, 2000, 0, "free"),
        ToolSpec("tool.repo.ast.parse", "AST Parse", "1.0.0", "Parsear simbolos de repos autorizados.", "retrieval", ("read_repo",), "read", True, True, 20000, 1, "free"),
        ToolSpec("tool.sql.parse", "SQL Parse", "1.0.0", "Parsear SQL estatico autorizado.", "retrieval", ("read_sql",), "read", True, True, 20000, 1, "free"),
        ToolSpec("tool.db.metadata.readonly", "DB Metadata Readonly", "1.0.0", "Leer metadata BD autorizada en read-only.", "retrieval", ("read_db_metadata",), "read", True, True, 30000, 1, "medium"),
        ToolSpec("tool.test.pytest", "Pytest", "1.0.0", "Ejecutar tests Python sandbox.", "test", ("run_tests",), "compute", True, True, 120000, 1, "free", "pytest"),
        ToolSpec("tool.test.vitest", "Vitest", "1.0.0", "Ejecutar tests frontend sandbox.", "test", ("run_tests",), "compute", True, True, 120000, 1, "free", "npm"),
        ToolSpec("tool.test.playwright", "Playwright", "1.0.0", "Ejecutar UI/E2E sandbox.", "test", ("run_tests",), "compute", True, True, 180000, 1, "free"),
        ToolSpec("tool.test.maven", "Maven Test", "1.0.0", "Ejecutar tests backend Maven/Spring sandbox.", "test", ("run_tests",), "compute", True, True, 240000, 1, "free", "mvn"),
        ToolSpec("tool.docker.compose", "Docker Compose", "1.0.0", "Levantar runtime local reproducible con Docker Compose cuando exista aprobacion.", "runtime", ("run_runtime",), "compute", True, False, 300000, 0, "medium", "docker"),
        ToolSpec("tool.runtime.healthcheck", "Runtime Healthcheck", "1.0.0", "Consultar endpoints health locales autorizados.", "runtime", ("run_runtime",), "read", True, True, 60000, 0, "free", "curl"),
        ToolSpec("tool.coverage.report", "Coverage Report", "1.0.0", "Consolidar cobertura.", "validator", ("read_reports",), "read", True, True, 10000, 0, "free"),
        ToolSpec("tool.lint.eslint", "ESLint", "1.0.0", "Lint frontend.", "validator", ("run_lint",), "compute", True, True, 60000, 1, "free", "npm"),
        ToolSpec("tool.lint.ruff", "Ruff", "1.0.0", "Lint backend.", "validator", ("run_lint",), "compute", True, True, 60000, 1, "free"),
        ToolSpec("tool.typecheck.tsc", "TSC", "1.0.0", "Typecheck TypeScript.", "validator", ("run_typecheck",), "compute", True, True, 120000, 1, "free", "npm"),
        ToolSpec("tool.typecheck.pyright", "Pyright", "1.0.0", "Typecheck Python.", "validator", ("run_typecheck",), "compute", True, True, 120000, 1, "free"),
        ToolSpec("tool.security.semgrep", "Semgrep", "1.0.0", "SAST.", "validator", ("run_security_scan",), "compute", True, True, 120000, 1, "free", "semgrep"),
        ToolSpec("tool.security.trivy", "Trivy", "1.0.0", "Container/dependency scan.", "validator", ("run_security_scan",), "compute", True, True, 180000, 1, "free", "trivy"),
        ToolSpec("tool.security.gitleaks", "Gitleaks", "1.0.0", "Secret scan.", "validator", ("run_security_scan",), "compute", True, True, 60000, 1, "free", "gitleaks"),
        ToolSpec("tool.security.pip_audit", "pip-audit", "1.0.0", "Python dependency audit.", "validator", ("run_security_scan",), "compute", True, True, 120000, 1, "free"),
        ToolSpec("tool.security.npm_audit", "npm audit", "1.0.0", "Node dependency audit.", "validator", ("run_security_scan",), "compute", True, True, 120000, 1, "free", "npm"),
        ToolSpec("tool.api.openapi.validate", "OpenAPI Validate", "1.0.0", "Validar OpenAPI.", "validator", ("read_artifact",), "compute", True, True, 30000, 1, "free"),
        ToolSpec("tool.ocr.screen", "OCR Screen", "1.0.0", "OCR/estructura de pantallas autorizadas.", "retrieval", ("read_image",), "read", True, True, 30000, 1, "medium"),
        ToolSpec("tool.obs.billing", "Billing", "1.0.0", "Consolidar billing.", "observability", ("read_logs",), "read", True, True, 10000, 0, "free"),
        ToolSpec("tool.validator.schema", "Schema Validator", "1.0.0", "Validar schemas estrictos.", "validator", ("compute",), "compute", True, True, 10000, 0, "free"),
        ToolSpec("tool.validator.final_format", "Final Format Validator", "1.0.0", "Validar cierre formal.", "validator", ("compute",), "compute", True, True, 10000, 0, "free"),
        ToolSpec("tool.memory.propose", "Memory Propose", "1.0.0", "Crear propuesta de memoria.", "observability", ("memory_propose",), "write_preview", True, True, 10000, 0, "free"),
    ]
    return {tool.tool_id: tool for tool in specs}


def skill_registry() -> dict[str, SkillSpec]:
    specs = [
        SkillSpec("skill.normalize_work_order", "compute", "Normalizar brief a WorkOrder.", None, "input_hash", ("schema",)),
        SkillSpec("skill.chunk_and_hash", "retrieval", "Chunking deterministico con hash.", "tool.files.read", "corpus_hash", ("evidence",)),
        SkillSpec("skill.retrieve_context", "retrieval", "Recuperacion con threshold, rerank fijo y dedupe.", "tool.index.query", "query_hash+corpus_hash", ("context",)),
        SkillSpec("skill.compact_context", "compute", "Compactar contexto con evidencia.", None, "context_pack_hash", ("budget",)),
        SkillSpec("skill.validate_schema", "validate", "Validar JSON schema estricto.", "tool.validator.schema", "artifact_hash", ("schema",)),
        SkillSpec("skill.validate_evidence", "validate", "Validar claims criticos.", "tool.validator.schema", "artifact_hash", ("evidence",)),
        SkillSpec("skill.plan_tests", "test", "Crear matriz de pruebas por riesgo.", None, "spec_hash+tasks_hash", ("coverage",)),
        SkillSpec("skill.run_unit_tests", "test", "Ejecutar unit tests sandbox.", "tool.test.pytest", "commit+suite+env", ("tests",)),
        SkillSpec("skill.run_e2e_tests", "test", "Ejecutar E2E UI.", "tool.test.playwright", "commit+suite+env", ("tests",)),
        SkillSpec("skill.scan_security", "validate", "Escaneo SAST/secrets/deps.", "tool.security.gitleaks", "artifact_hash", ("security",)),
        SkillSpec("skill.ocr_screen", "retrieval", "Analizar imagen autorizada.", "tool.ocr.screen", "image_hash", ("safety",)),
        SkillSpec("skill.generate_openapi", "compute", "Generar contrato OpenAPI.", "tool.api.openapi.validate", "spec_hash", ("contract",)),
        SkillSpec("skill.frontend_modern_angular", "frontend", "Construir Angular moderno con features, modelos, servicios, estados y componentes reutilizables.", "tool.typecheck.tsc", "ui_contract_hash", ("frontend", "accessibility", "tests")),
        SkillSpec("skill.backend_spring_boot_real_crud", "backend", "Construir API Spring Boot con DTOs, servicios transaccionales, validacion y persistencia real.", "tool.test.maven", "api_contract_hash", ("backend", "tests", "security")),
        SkillSpec("skill.postgres_domain_modeling", "database", "Modelar PostgreSQL con relaciones, constraints, indices, migraciones Flyway y seed coherente.", "tool.sql.parse", "schema_hash", ("database", "schema", "tests")),
        SkillSpec("skill.ux_product_quality", "frontend", "Evaluar usabilidad, estados vacios/carga/error y flujos completos de producto.", "tool.test.playwright", "ui_state_hash", ("frontend", "qa", "accessibility")),
        SkillSpec("skill.e2e_playwright_validation", "test", "Validar navegacion y flujos criticos con Playwright cuando runtime local este autorizado.", "tool.test.playwright", "runtime_hash", ("tests", "runtime", "qa")),
        SkillSpec("skill.docker_runtime_validation", "runtime", "Levantar Docker Compose local, consultar healthcheck y cerrar servicios con evidencia.", "tool.docker.compose", "compose_hash", ("runtime", "tests", "observability")),
        SkillSpec("skill.write_docs", "file_write_dry_run", "Escribir docs markdown.", "tool.files.write_dry_run", "doc_plan_hash", ("final_format",)),
        SkillSpec("skill.record_billing", "observe", "Consolidar ledger.", "tool.obs.billing", "run_id", ("budget",)),
        SkillSpec("skill.propose_memory", "observe", "Proponer memoria gobernada.", "tool.memory.propose", "evidence_hash", ("memory",)),
    ]
    return {skill.skill_id: skill for skill in specs}


def agent_registry() -> dict[str, AgentSpec]:
    common_not = (
        "La tarea puede resolverse con una skill deterministica.",
        "Falta evidencia obligatoria.",
        "Requiere permisos no concedidos.",
    )
    specs = [
        AgentSpec("agent.spec_detallada", "Especificacion Detallada", "1.0.0", "factory", "production", "Constitucion, RF/RNF, criterios y aclaraciones.", "Convertir WorkOrder en especificacion verificable.", ("specify", "clarify"), common_not, ("tool.files.read", "tool.index.query", "tool.cache.get", "tool.cache.set", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("schema", "spec", "evidence", "final_format")),
        AgentSpec("agent.requirements_cleaner", "Requirements Cleaner", "1.0.0", "factory", "production", "Limpiar requisitos extraidos antes de planificar o generar UI.", "Convertir contexto OCR/markdown ruidoso en requisitos compactos, internos y trazables.", ("context", "plan", "implement"), common_not, ("tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("project",), "write_allowed": False, "write_requires_approval": True}, ("context", "evidence", "consistency", "final_format")),
        AgentSpec("agent.context_rag", "Context RAG", "1.0.0", "factory", "production", "Recuperar evidencia minima.", "Construir context-pack y evidence-register.", ("context",), common_not, ("tool.files.read", "tool.index.query", "tool.cache.get", "tool.cache.set"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("context", "evidence", "safety", "budget")),
        AgentSpec("agent.architect_plan", "Arquitectura y Plan", "1.0.0", "factory", "production", "Plan tecnico, contratos y tareas.", "Crear plan y tasks atomicas trazables.", ("plan", "tasks"), common_not, ("tool.files.read", "tool.validator.schema", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("plan", "plan_validation", "consistency")),
        AgentSpec("agent.diseno_alcance_rubrica", "Diseno de Alcance Rubrica", "1.0.0", "factory", "production", "Formalizar cantidades exigidas por la evaluacion antes de codificar.", "Generar tablas, endpoints, pantallas, reglas y checks documentados con inventario contable.", ("scope_design", "plan_validation"), common_not, ("tool.files.read", "tool.validator.schema", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("rubric_scope", "scope_realism", "coverage", "consistency", "final_format")),
        AgentSpec("agent.ui_web_modern", "UI Web Moderna", "1.0.0", "factory", "production", "Diseno UI atractivo, accesible y usable.", "Aplicar buenas practicas UI web al plan.", ("plan", "ui"), common_not, ("tool.files.read", "tool.ocr.screen", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("accessibility", "qa", "evidence")),
        AgentSpec("agent.api_security_docs", "API Segura Docs", "1.0.0", "factory", "production", "APIs seguras con tokens y OpenAPI.", "Generar contratos API seguros y ejemplos no sensibles.", ("plan", "contracts"), common_not, ("tool.api.openapi.validate", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("security", "contract", "tests", "evidence")),
        AgentSpec("agent.implementacion_doc_code", "Implementacion Documentada", "1.0.0", "factory", "production", "Cambios de codigo con docs y tests.", "Materializar tasks aprobadas en sandbox.", ("implement",), common_not, ("tool.files.read", "tool.files.write_dry_run", "tool.repo.ast.parse", "tool.lint.ruff", "tool.test.pytest"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "sandbox", "schema", "tests", "coverage", "app_realism", "security", "dependency", "consistency")),
        AgentSpec("agent.database_builder", "Database Builder", "1.0.0", "factory", "production", "Generar y corregir modelo PostgreSQL, Flyway, seed e invariantes.", "Usar IA controlada para proponer artefactos de persistencia y validar schema real.", ("implement", "repair"), common_not, ("tool.files.read", "tool.sql.parse", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.backend_builder", "Backend Builder", "1.0.0", "factory", "production", "Generar y corregir Spring Boot, DTOs, servicios transaccionales y controllers.", "Usar IA controlada para proponer artefactos backend y cerrar findings del reviewer.", ("implement", "repair"), common_not, ("tool.files.read", "tool.repo.ast.parse", "tool.test.maven", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.frontend_builder", "Frontend Builder", "1.0.0", "factory", "production", "Generar y corregir Angular, rutas, estados, servicios y componentes por dominio.", "Usar IA controlada para proponer artefactos frontend y mejorar UX sin clonar pantallas.", ("implement", "repair"), common_not, ("tool.files.read", "tool.typecheck.tsc", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.test_builder", "Test Builder", "1.0.0", "factory", "production", "Generar smoke, contract tests, integration tests y evidencias de runtime local.", "Usar IA controlada para proponer pruebas y reforzar gates anti-app-falsa.", ("implement", "validate", "repair"), common_not, ("tool.files.read", "tool.test.vitest", "tool.test.maven", "tool.test.playwright", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.tests_coverage", "Tests y Cobertura", "1.0.0", "factory", "production", "Plan y ejecucion de pruebas.", "Cubrir requisitos, riesgos, permisos y errores.", ("validate", "tasks"), common_not, ("tool.test.pytest", "tool.test.vitest", "tool.test.playwright", "tool.coverage.report", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(run_tests=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "tests", "coverage", "consistency", "budget")),
        AgentSpec("agent.app_reviewer", "App Reviewer", "1.0.0", "factory", "production", "Revisar app generada como producto moderno real.", "Auditar frontend, backend, base, runtime, trazabilidad y deuda antes del cierre.", ("validate", "analyze"), common_not, ("tool.files.read", "tool.test.playwright", "tool.validator.schema", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.ux_ui_product_reviewer", "UX/UI Product Reviewer", "1.0.0", "factory", "production", "Bloquear UI que parezca plantilla o debug.", "Revisar copy, layout, estados de producto, evidencias Playwright y artefactos visuales.", ("validate", "analyze"), common_not, ("tool.files.read", "tool.test.playwright", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.software_architect_reviewer", "Software Architect Reviewer", "1.0.0", "factory", "production", "Bloquear arquitectura falsa o acoplada.", "Validar separacion Angular/Spring/Postgres, contratos, endpoints de dominio y persistencia real.", ("validate", "analyze"), common_not, ("tool.files.read", "tool.repo.ast.parse", "tool.sql.parse", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.product_owner_flow_reviewer", "Product Owner Flow Reviewer", "1.0.0", "factory", "production", "Bloquear pantallas sin proposito ciudadano.", "Verificar que acciones como iniciar tramite, marcar notificacion, revocar permiso y actualizar domicilio tengan sentido y endpoints.", ("validate", "analyze"), common_not, ("tool.files.read", "tool.validator.schema", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.qa_e2e_reviewer", "QA E2E Reviewer", "1.0.0", "factory", "production", "Bloquear botones sin efecto observable.", "Ejecutar/validar Playwright E2E contra app levantada y comprobar cambios de UI/API.", ("containerize", "validate", "repair"), common_not, ("tool.files.read", "tool.test.playwright", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.docker_packaging", "Docker Packaging", "1.0.0", "factory", "production", "Preparar contenedor reproducible para EC2.", "Generar Dockerfile, docker-compose y validacion de contenedor.", ("containerize",), common_not, ("tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "ai_code_writer", "coverage", "consistency", "final_format")),
        AgentSpec("agent.docker_runtime_validator", "Docker Runtime Validator", "1.0.0", "factory", "production", "Levantar Docker y validar health/smoke/e2e.", "Ejecutar docker compose build/up, healthchecks frontend/backend, smoke y Playwright antes de permitir complete.", ("containerize", "validate", "repair"), common_not, ("tool.files.read", "tool.docker.compose", "tool.test.playwright", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True, run_tests=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("agent_runtime", "app_realism", "coverage", "consistency")),
        AgentSpec("agent.github_publication", "GitHub Publication", "1.0.0", "factory", "production", "Publicar codigo y artefactos en GitHub si hay remoto configurado.", "Preparar commit/push y registrar evidencia de repo.", ("publish",), common_not, ("tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("coverage", "consistency", "final_format")),
        AgentSpec("agent.deploy_ec2", "Deploy EC2", "1.0.0", "factory", "production", "Desplegar la app en EC2 usando Docker cuando exista configuracion local segura.", "Leer configuracion local, ejecutar SSH autorizado, validar URL publica y registrar evidencia.", ("deploy",), common_not, ("tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("alto"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("coverage", "consistency", "final_format")),
        AgentSpec("agent.qa_checklist", "QA Checklist", "1.0.0", "factory", "production", "Validar buenas practicas y cierre.", "Aprobar o bloquear por checklist.", ("checklist", "analyze", "validate", "close"), common_not, ("tool.validator.schema", "tool.validator.final_format", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("checklist", "consistency", "coverage", "final_format")),
        AgentSpec("agent.doc_tecnica_detalle", "Documentacion Tecnica Detallada", "1.0.0", "factory", "production", "Docs tecnicas, ADR, RUN_STATE y handoff.", "Producir documentacion con evidencia.", ("close", "docs"), common_not, ("tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("schema", "evidence", "consistency", "final_format")),
        AgentSpec("agent.ocr_ui_analyst", "OCR UI Analyst", "1.0.0", "factory", "production", "Analizar pantallas autorizadas.", "Extraer texto/layout sin inferir negocio.", ("context", "ui"), common_not, ("tool.ocr.screen", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(write_files=True), _model_policy(), _budget("medio"), {"read_scopes": (), "write_allowed": False, "write_requires_approval": True}, ("safety", "evidence", "schema")),
        AgentSpec("agent.security_policy", "Security Policy", "1.0.0", "factory", "production", "Revisar policy, secretos, permisos y dependencias.", "Bloquear acciones inseguras.", ("plan_validation", "analyze", "validate"), common_not, ("tool.security.semgrep", "tool.security.trivy", "tool.security.gitleaks", "tool.security.pip_audit", "tool.security.npm_audit", "tool.validator.schema", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(run_tests=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("security", "secrets", "dependency", "policy")),
        AgentSpec("agent.token_billing", "Token Billing", "1.0.0", "factory", "production", "Contabilizar tokens, tools, latencia y costos.", "Consolidar ledger auditable.", ("observe", "close"), common_not, ("tool.obs.billing", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(write_files=True), _model_policy(), _budget("bajo"), {"read_scopes": (), "write_allowed": False, "write_requires_approval": True}, ("budget", "observability")),
        AgentSpec("agent.observability_sre", "Observabilidad SRE", "1.0.0", "factory", "production", "Validar logs, metricas, SLOs y runbooks.", "Asegurar operabilidad y trazas.", ("observe", "close"), common_not, ("tool.obs.billing", "tool.files.read", "tool.files.write_dry_run"), BASE_FORBIDDEN_TOOLS, _permissions(read_repo=True, write_files=True), _model_policy(), _budget("medio"), {"read_scopes": ("factory", "project"), "write_allowed": False, "write_requires_approval": True}, ("observability", "budget", "final_format")),
    ]
    return {agent.agent_id: agent for agent in specs}
