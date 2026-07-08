from __future__ import annotations

from pathlib import Path
import json

import pytest

from factory.context import ContextManager
from factory.harness import HarnessRunner, UnknownAgentError
from factory.memory import MemoryGate
from factory.orchestrator import OrchestratorGraph
from factory.policy import PolicyEngine
from factory.principles import PRINCIPLES, validate_principles
from factory.registry import agent_registry, skill_registry, tool_registry
from factory.schemas import WORK_ORDER_SCHEMA, SchemaError, validate_strict
from factory.utils import sha256_text, stable_json
from factory.validators import ValidatorChain


def _state() -> dict:
    return {
        "run_id": "RUN-TEST",
        "cycle_id": "CYC-001",
        "task_id": "TASK-TEST",
        "phase": "specify",
        "status": "complete",
        "input_hash": "sha256:test",
        "spec_hash": "sha256:test",
        "policy_version": "arnes-policy.v1",
        "tool_registry_version": "tool-registry.v1",
        "memory_version": "memory-governance.v1",
        "evidence": [],
        "outputs": {},
        "issues": [],
        "budget": {
            "max_input_tokens": 1000,
            "max_output_tokens": 1000,
            "max_cost_usd": 0,
            "max_latency_ms": 10000,
            "max_tool_calls": 10,
            "used_input_tokens": 0,
            "used_output_tokens": 0,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "estimated_cost_usd": 0,
            "tool_calls": 0,
        },
        "approval": {"required": False, "approved": False, "approval_id": "none"},
    }


def test_work_order_schema_blocks_extra_properties() -> None:
    data = {
        "work_order_id": "WO-1",
        "objective": "Objetivo verificable suficientemente largo",
        "work_type": "feature",
        "scope": {"include": [], "exclude": []},
        "inputs": [],
        "constraints": {"no_web": True, "dry_run": True, "sandbox_required": True, "max_retries": 1, "risk": "high", "max_cost_usd": 0, "max_latency_ms": 1000},
        "expected_outputs": [],
        "approval_required_for": [],
        "extra": True,
    }
    with pytest.raises(SchemaError):
        validate_strict(WORK_ORDER_SCHEMA, data)


def test_registries_include_required_agents_skills_tools() -> None:
    agents = agent_registry()
    for agent_id in {
        "agent.spec_detallada",
        "agent.doc_tecnica_detalle",
        "agent.tests_coverage",
        "agent.implementacion_doc_code",
        "agent.diseno_alcance_rubrica",
        "agent.ocr_ui_analyst",
        "agent.api_security_docs",
        "agent.qa_checklist",
        "agent.token_billing",
        "agent.security_policy",
        "agent.observability_sre",
    }:
        assert agent_id in agents
    assert "skill.retrieve_context" in skill_registry()
    assert "tool.files.read" in tool_registry()
    assert "shell.free" not in tool_registry()


def test_rubric_scope_agent_generates_inventory(tmp_path: Path) -> None:
    run_dir = tmp_path / "project" / "runs" / "RUN-TEST"
    run_dir.mkdir(parents=True)
    harness = HarnessRunner(factory_root=Path.cwd(), project_dir=tmp_path / "project", run_dir=run_dir)
    state = _state()
    state["phase"] = "scope_design"
    result = harness.run_agent("agent.diseno_alcance_rubrica", state)
    assert result["status"] == "complete"
    assert (run_dir / "scope-inventory.json").exists()
    assert (run_dir / "scope-validation.json").exists()


def test_implementation_agent_generates_executable_app(tmp_path: Path) -> None:
    run_dir = tmp_path / "project" / "runs" / "RUN-TEST"
    run_dir.mkdir(parents=True)
    harness = HarnessRunner(factory_root=Path.cwd(), project_dir=tmp_path / "project", run_dir=run_dir)
    state = _state()
    state["phase"] = "implement"
    result = harness.run_agent("agent.implementacion_doc_code", state)
    app_dir = tmp_path / "app-generada"
    assert result["status"] == "complete"
    for rel in {
        "package.json",
        "server.mjs",
        "public/index.html",
        "public/app.js",
        "data/scope.json",
        "data/implementation-ledger.json",
        "data/api-catalog.json",
        "data/seed.json",
        "data/public-state.json",
        "data/app-db.seed.json",
        "data/app-db.json",
        "data/schema.sql",
        "tests/smoke.mjs",
        "Dockerfile",
        "docker-compose.yml",
    }:
        assert (app_dir / rel).exists(), rel
    scope = json.loads((app_dir / "data" / "scope.json").read_text(encoding="utf-8"))
    ledger = json.loads((app_dir / "data" / "implementation-ledger.json").read_text(encoding="utf-8"))
    seed_db = json.loads((app_dir / "data" / "app-db.seed.json").read_text(encoding="utf-8"))
    schema_sql = (app_dir / "data" / "schema.sql").read_text(encoding="utf-8")
    assert len({screen["summary"] for screen in scope["screens"]}) >= 28
    assert len({screen["layout"] for screen in scope["screens"]}) >= 24
    assert len({screen["fingerprint"] for screen in scope["screens"]}) == 30
    assert len(scope["requirements"]) == 90
    assert scope["apiCatalog"]["endpoint_count"] == 40
    assert ledger["summary"]["implementation_status"] == "implemented_pending_web_validation"
    assert "CREATE TABLE citizens" in schema_sql
    assert "CREATE TABLE procedures" in schema_sql
    assert len(seed_db["procedures"]) >= 3
    assert len(seed_db["notifications"]) >= 3
    public_app = (app_dir / "public" / "app.js").read_text(encoding="utf-8")
    public_data = (app_dir / "public" / "data.js").read_text(encoding="utf-8")
    assert 'fetch("/api/v1/app-state")' in public_app
    assert 'fetch("/api/v1/actions"' in public_app
    for forbidden in {
        "Contrato y trazabilidad",
        "Endpoint mock",
        "Fingerprint UI",
        "Validaciones de la vista",
        "REQ_UI_",
        "REQ_FLOW_",
        "REQ_VAL_",
        "trazabilidad de fabrica",
        "Flujo simulado por la fabrica",
    }:
        assert forbidden not in public_app
        assert forbidden not in public_data


def test_policy_blocks_tool_not_allowlisted() -> None:
    agents = agent_registry()
    decision = PolicyEngine(tool_registry()).check_tool(agents["agent.spec_detallada"], "tool.security.gitleaks", {"approved": False})
    assert decision.status == "error"
    assert decision.code == "blocked_by_policy"


def test_validator_blocks_missing_critical_evidence(tmp_path: Path) -> None:
    items = ValidatorChain().validate_output(
        state=_state(),
        output={"critical_claims": [{"claim": "x", "evidence_id": ""}], "evidence_refs": [], "policy_findings": []},
        required_gates=("evidence",),
        run_dir=tmp_path,
    )
    assert ValidatorChain.status_from_items(items) == "not_answerable"


def test_validator_blocks_budget_exceeded(tmp_path: Path) -> None:
    state = _state()
    state["budget"]["tool_calls"] = 11
    items = ValidatorChain().validate_output(
        state=state,
        output={"critical_claims": [], "evidence_refs": [], "policy_findings": []},
        required_gates=("budget",),
        run_dir=tmp_path,
    )
    assert ValidatorChain.status_from_items(items) == "error"


def test_memory_is_project_scoped(tmp_path: Path) -> None:
    factory_root = tmp_path / "factory"
    project_dir = tmp_path / "project"
    factory_root.mkdir()
    gate = MemoryGate(factory_root, project_dir)
    gate.initialize()
    assert (factory_root / "Aprendizaje.md").exists()
    assert (project_dir / "Aprendizaje.md").exists()
    assert (project_dir / "agent-memory").exists()


def test_context_pack_is_deterministic() -> None:
    ctx = ContextManager()
    a = ctx.retrieve("arnes harness policy", limit=5)
    b = ctx.retrieve("arnes harness policy", limit=5)
    comparable_a = [(item["source_id"], item["chunk_id"], item["hash"], item["rerank_score"]) for item in a["chunks"]]
    comparable_b = [(item["source_id"], item["chunk_id"], item["hash"], item["rerank_score"]) for item in b["chunks"]]
    assert comparable_a == comparable_b
    assert a["corpus_hash"] == b["corpus_hash"]


def test_harness_unknown_agent_raises(tmp_path: Path) -> None:
    run_dir = tmp_path / "project" / "runs" / "RUN-TEST"
    run_dir.mkdir(parents=True)
    harness = HarnessRunner(factory_root=Path.cwd(), project_dir=tmp_path / "project", run_dir=run_dir)
    with pytest.raises(UnknownAgentError):
        harness.run_agent("agent.nope", _state())


def test_orchestrator_bootstrap_run(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_dir = OrchestratorGraph(project_dir=project).run("Preparar fabrica ARNES SDD para pruebas")
    assert (run_dir / "final-report.json").exists()
    assert (run_dir / "traceability-matrix.md").exists()
    assert (project / "Aprendizaje.md").exists()


def test_principles_catalog_is_complete() -> None:
    assert list(PRINCIPLES) == [f"P{i:02d}" for i in range(1, 13)]
    assert validate_principles() == []


def test_orchestrator_generates_governance_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_dir = OrchestratorGraph(project_dir=project).run("Preparar fabrica con evidencia gobernada")
    for name in {
        "principle-ledger.json",
        "phase-ledger.json",
        "claim-map.md",
        "project-manifest.json",
        "project-sandboxes.json",
        "frontend-template-manifest.json",
        "secrets-report.json",
        "dependency-report.json",
        "sbom.json",
        "rollback-plan.md",
        "PRBundle.md",
    }:
        assert (run_dir / name).exists(), name
    assert (project / "workspaces" / "claveunica-licitacion" / "sandboxes" / "DEV" / "sandbox-manifest.json").exists()
    assert (project / "workspaces" / "claveunica-licitacion" / "sandboxes" / "QA" / "sandbox-manifest.json").exists()
