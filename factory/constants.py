from __future__ import annotations

from pathlib import Path


FACTORY_NAME = "Fabrica_Agentica_Evaluacion_Final"
FACTORY_VERSION = "1.1.0-final-integrador"
SCHEMA_VERSION = "arnes-sdd.schema.v1"
POLICY_VERSION = "arnes-policy.v1"
TOOL_REGISTRY_VERSION = "tool-registry.v1"
MEMORY_VERSION = "memory-governance.v1"
WORKFLOW_VERSION = "sdd-rubrica-final-15phases.v1"
INDEX_VERSION = "index.v1"
RERANKER_VERSION = "fixed-rerank-v1"
MODEL_SNAPSHOT = "GPT-5.5-or-fixed-snapshot"
MODEL_SEED = 12345
FINAL_STATUSES = ("complete", "needs_user_input", "not_answerable", "error")

ROOT = Path(__file__).resolve().parents[1]
DESIGN_DOCS = (
    "project/input/product_generation_brief.md",
    "project/context/product-generation-policy.md",
    "project/context/requirements-clean.md",
    "01_Constitucion_y_Especificacion_Fabrica.md",
    "02_Arquitectura_Stack_y_Flujos_SDD.md",
    "03_Agentes_Skills_Herramientas_y_Permisos.md",
    "04_Orquestador_Ciclo_12_Pasos_Operabilidad.md",
    "arnes.md",
    "buenas_practicas.md",
    "CHECKLIST.md",
)

EVIDENCE_FALLBACK_DOCS = (
    "factory/harness.py",
    "factory/orchestrator.py",
    "factory/policy.py",
    "factory/registry.py",
    "factory/validators.py",
    "factory/agents.py",
)

SDD_PHASES = (
    "intake",
    "specify",
    "clarify",
    "checklist",
    "context",
    "plan",
    "scope_design",
    "plan_validation",
    "tasks",
    "analyze",
    "implement",
    "repair",
    "validate",
    "containerize",
    "publish",
    "pr_deploy",
    "deploy",
    "observe",
    "close",
)

APPROVAL_REQUIRED_FOR = (
    "write",
    "deploy",
    "merge",
    "external_api",
    "secrets",
    "infra",
    "cost_increase",
    "data_access",
    "production_data",
    "db_write",
)
