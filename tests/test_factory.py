from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pytest

from factory.agents import deploy_ec2, github_publication
from factory.agent_runtime.model_client import ModelClient
from factory.agent_runtime.safe_writer import SafeFileWriter
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
    scope = json.loads((run_dir / "scope-inventory.json").read_text(encoding="utf-8"))
    endpoint_paths = [item["path"] for item in scope["api_endpoints"]]
    table_names = [item["table"] for item in scope["tables"]]
    screen_routes = [item["route"] for item in scope["screens"]]
    rule_text = "\n".join(item["rule"] for item in scope["business_rules"])
    assert len(scope["traceability"]) >= 40
    assert all("/recurso-" not in path for path in endpoint_paths)
    assert all("{module}" not in path for path in endpoint_paths)
    assert all("/vista-" not in route for route in screen_routes)
    assert "Regla funcional" not in rule_text
    assert "procedures" in table_names


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
        "frontend/package.json",
        "frontend/angular.json",
        "frontend/src/app/app.routes.ts",
        "frontend/src/app/app.component.ts",
        "frontend/src/app/services/portal-api.service.ts",
        "frontend/src/app/services/feature-api.service.ts",
        "frontend/Dockerfile",
        "backend/pom.xml",
        "backend/src/main/java/cl/benjamin/claveunica/PortalApplication.java",
        "backend/src/main/java/cl/benjamin/claveunica/controller/PortalController.java",
        "backend/src/main/java/cl/benjamin/claveunica/controller/ApiExceptionHandler.java",
        "backend/src/main/java/cl/benjamin/claveunica/dto/ActionRequest.java",
        "backend/src/main/java/cl/benjamin/claveunica/dto/ProcedureRequest.java",
        "backend/src/main/java/cl/benjamin/claveunica/service/PortalWorkflowService.java",
        "backend/src/main/resources/db/migration/V1__init_claveunica_domain.sql",
        "backend/src/test/java/cl/benjamin/claveunica/PortalWorkflowServiceTest.java",
        "backend/Dockerfile",
        "database/schema.sql",
        "database/seed.sql",
        "database/domain-model.json",
        "data/scope.json",
        "data/implementation-ledger.json",
        "data/api-catalog.json",
        "data/openapi.yaml",
        "data/seed.json",
        "tests/smoke.mjs",
        "docker-compose.yml",
    }:
        assert (app_dir / rel).exists(), rel
    scope = json.loads((app_dir / "data" / "scope.json").read_text(encoding="utf-8"))
    ledger = json.loads((app_dir / "data" / "implementation-ledger.json").read_text(encoding="utf-8"))
    domain_model = json.loads((app_dir / "database" / "domain-model.json").read_text(encoding="utf-8"))
    schema_sql = (app_dir / "database" / "schema.sql").read_text(encoding="utf-8")
    routes_ts = (app_dir / "frontend" / "src" / "app" / "app.routes.ts").read_text(encoding="utf-8")
    controller_java = (app_dir / "backend" / "src" / "main" / "java" / "cl" / "benjamin" / "claveunica" / "controller" / "PortalController.java").read_text(encoding="utf-8")
    service_java = (app_dir / "backend" / "src" / "main" / "java" / "cl" / "benjamin" / "claveunica" / "service" / "PortalWorkflowService.java").read_text(encoding="utf-8")
    integration_test_java = (app_dir / "backend" / "src" / "test" / "java" / "cl" / "benjamin" / "claveunica" / "PortalWorkflowServiceTest.java").read_text(encoding="utf-8")
    migration_sql = (app_dir / "backend" / "src" / "main" / "resources" / "db" / "migration" / "V1__init_claveunica_domain.sql").read_text(encoding="utf-8")
    openapi_yaml = (app_dir / "data" / "openapi.yaml").read_text(encoding="utf-8")
    feature_api_ts = (app_dir / "frontend" / "src" / "app" / "services" / "feature-api.service.ts").read_text(encoding="utf-8")
    feature_dirs = [path for path in (app_dir / "frontend" / "src" / "app" / "features").iterdir() if path.is_dir()]
    html_files = sorted((app_dir / "frontend" / "src" / "app" / "pages").glob("*.component.html"))
    html_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in html_files}
    assert len({screen["summary"] for screen in scope["screens"]}) >= 28
    assert len({screen["layout"] for screen in scope["screens"]}) >= 24
    assert len({screen["fingerprint"] for screen in scope["screens"]}) == 30
    assert len(scope["requirements"]) == 90
    assert scope["apiCatalog"]["endpoint_count"] == 40
    assert scope["domainBlueprint"]["quality_bar"] == "local_functional_app"
    assert ledger["summary"]["implementation_status"] == "implemented_pending_web_validation"
    assert schema_sql.count("CREATE TABLE") == 40
    assert "metadata JSONB NOT NULL DEFAULT '{}'" not in schema_sql
    assert "CREATE INDEX" in schema_sql
    assert "CHECK (status IN" in schema_sql
    assert domain_model["table_count"] == 40
    assert domain_model["blueprint"]["anti_fake_gates"]
    assert routes_ts.count("loadComponent") == 30
    assert controller_java.count("Mapping(\"") >= 40
    assert len(html_hashes) >= 20
    assert "JdbcTemplate" in controller_java
    assert "PortalWorkflowService" in controller_java
    assert "@Valid" in controller_java
    assert "@Transactional" in service_java
    assert "jdbc.update" in service_java
    assert "Testcontainers" in integration_test_java
    assert "createProcedurePersistsAndUpdatesDashboard" in integration_test_java
    assert "CREATE TABLE citizens" in migration_sql
    assert "INSERT INTO citizens" in migration_sql
    assert "openapi: 3.1.0" in openapi_yaml
    assert "/api/v1/procedures" in openapi_yaml
    assert "runFeatureAction" in feature_api_ts
    assert "/api/v1/digital-addresses" in feature_api_ts
    assert len(feature_dirs) >= 6
    assert all((path / "models").exists() and (path / "services").exists() and (path / "components").exists() for path in feature_dirs)
    assert "endpoint01()" not in controller_java
    assert not (app_dir / "server.mjs").exists()
    assert not (app_dir / "public").exists()
    public_app = routes_ts + controller_java
    public_data = (app_dir / "frontend" / "src" / "app" / "app.component.html").read_text(encoding="utf-8")
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


def test_model_client_falls_back_without_local_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    secrets = project / "secrets"
    secrets.mkdir(parents=True)
    (secrets / "model-provider.local.json").write_text(
        json.dumps(
            {
                "enabled": True,
                "provider": "openai",
                "endpoint": "https://api.openai.com/v1/responses",
                "model": "gpt-5.5",
                "api_key_env": "OPENAI_API_KEY",
                "execute_tools": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    plan = ModelClient(project_dir=project).plan(contract={"allowed_tools": []}, context_pack={"chunks": []}, state={**_state(), "execution_mode": "agentic"})

    assert plan.status == "needs_adapter"
    assert plan.adapter == "missing_api_key"
    assert plan.actions == ()


def test_orchestrator_uses_agentic_mode_only_when_local_provider_enabled(tmp_path: Path) -> None:
    project = tmp_path / "project"
    secrets = project / "secrets"
    secrets.mkdir(parents=True)
    orchestrator = OrchestratorGraph(project_dir=project)

    assert orchestrator._execution_mode() == "deterministic"

    (secrets / "model-provider.local.json").write_text(json.dumps({"enabled": True, "provider": "openai"}), encoding="utf-8")

    assert orchestrator._execution_mode() == "agentic"


def test_orchestrator_codex_direct_mode_blocks_api_by_default(tmp_path: Path) -> None:
    project = tmp_path / "project"
    secrets = project / "secrets"
    secrets.mkdir(parents=True)
    (secrets / "model-provider.local.json").write_text(json.dumps({"enabled": True, "provider": "openai"}), encoding="utf-8")
    (secrets / "execution-mode.local.json").write_text(
        json.dumps({"mode": "codex_direct", "allow_openai_api_calls": False}),
        encoding="utf-8",
    )
    orchestrator = OrchestratorGraph(project_dir=project)

    assert orchestrator._execution_mode() == "codex_direct"


def test_safe_file_writer_blocks_secrets_and_paths_outside_app(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    run_dir = repo / "project" / "runs" / "RUN-TEST"
    run_dir.mkdir(parents=True)
    writer = SafeFileWriter(repo_root=repo, run_dir=run_dir)

    ok = writer.write_file(relative_path="app-generada/frontend/src/app/ai-note.ts", content="export const note = 'ok';\n")
    blocked_path = writer.write_file(relative_path="project/secrets/model-provider.local.json", content="{}")
    blocked_secret = writer.write_file(relative_path="app-generada/leak.txt", content="OPENAI_API_KEY=sk-proj-test")
    blocked_frontend_debug = writer.write_file(relative_path="app-generada/frontend/src/app/pages/demo.component.html", content="<h2>Validaciones</h2><p>REQ_UI_001</p>")

    assert ok.status == "complete"
    assert (repo / "app-generada" / "frontend" / "src" / "app" / "ai-note.ts").exists()
    assert blocked_path.status == "error"
    assert blocked_secret.status == "error"
    assert blocked_frontend_debug.status == "error"


def test_ai_code_writer_gate_blocks_failed_model_writes(tmp_path: Path) -> None:
    output = {
        "critical_claims": [],
        "evidence_refs": [],
        "policy_findings": ["model_file_policy_failed"],
        "execution_mode": "agentic",
        "agent_contract": {"hash": "sha256:test", "path": "contract.yaml"},
        "runtime_plan": {"steps": ["model plan"], "adapter": "openai-responses"},
        "tool_preflights": [],
        "ai_code_writer": {
            "mode": "ai_code_writer_controlled",
            "model_adapter": "openai-responses",
            "apply_writes": True,
            "allowed_write_roots": ["app-generada"],
            "failed_writes": 1,
        },
    }
    items = ValidatorChain().validate_output(state=_state(), output=output, required_gates=("agent_runtime", "ai_code_writer"), run_dir=tmp_path)
    assert ValidatorChain.status_from_items(items) == "error"
    assert any(item.code == "ai_code_writer_invalid" for item in items)


def test_harness_unknown_agent_raises(tmp_path: Path) -> None:
    run_dir = tmp_path / "project" / "runs" / "RUN-TEST"
    run_dir.mkdir(parents=True)
    harness = HarnessRunner(factory_root=Path.cwd(), project_dir=tmp_path / "project", run_dir=run_dir)
    with pytest.raises(UnknownAgentError):
        harness.run_agent("agent.nope", _state())


def test_deployment_freeze_blocks_push_and_ec2_even_when_allowed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_dir = project / "runs" / "RUN-TEST"
    secrets = project / "secrets"
    run_dir.mkdir(parents=True)
    secrets.mkdir(parents=True)
    (secrets / "deployment-freeze.local.json").write_text(json.dumps({"enabled": True, "reason": "test freeze"}), encoding="utf-8")
    (secrets / "deploy-target.local.json").write_text(
        json.dumps(
            {
                "allow_execute": True,
                "github_repo": "https://github.com/example/repo.git",
                "github_branch": "main",
                "host": "127.0.0.1",
                "user": "ubuntu",
                "ssh_key_path": str(tmp_path / "key.pem"),
                "remote_app_dir": "/home/ubuntu/app",
                "public_url": "http://127.0.0.1:3000",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "key.pem").write_text("dummy", encoding="utf-8")
    state = _state()

    github_publication(agent_registry()["agent.github_publication"], state, run_dir, {"chunks": []})
    deploy_ec2(agent_registry()["agent.deploy_ec2"], state, run_dir, {"chunks": []})

    git_report = json.loads((run_dir / "git-publication.json").read_text(encoding="utf-8"))
    deploy_report = json.loads((run_dir / "deployment-validation.json").read_text(encoding="utf-8"))
    assert git_report["status"] == "frozen"
    assert deploy_report["status"] == "frozen"
    assert git_report["allow_execute"] is False
    assert deploy_report["allow_execute"] is False
    assert git_report["commands"] == []
    assert deploy_report["commands"] == []


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
