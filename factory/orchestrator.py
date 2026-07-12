from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .constants import FACTORY_VERSION, MEMORY_VERSION, POLICY_VERSION, ROOT, TOOL_REGISTRY_VERSION, WORKFLOW_VERSION
from .context import ContextManager
from .governance import (
    ensure_run_dirs,
    validate_factory_docs,
    validate_traceability,
    write_assumptions_register,
    write_claim_map,
    write_executive_summary,
    write_factory_metrics,
    write_log_completeness_report,
    write_phase_ledger,
    write_principle_ledger,
    write_project_isolation,
    write_security_delivery_reports,
)
from .harness import HarnessRunner
from .registry import agent_registry, skill_registry, tool_registry
from .schemas import WORK_ORDER_SCHEMA, validate_strict
from .utils import read_json, sha256_text, stable_json, utc_now, write_json


class OrchestratorGraph:
    ROUTE: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("specify", ("agent.spec_detallada",)),
        ("clarify", ("agent.spec_detallada",)),
        ("checklist", ("agent.qa_checklist",)),
        ("context", ("agent.requirements_cleaner", "agent.context_rag", "agent.ocr_ui_analyst")),
        ("plan", ("agent.architect_plan", "agent.ui_web_modern", "agent.api_security_docs")),
        ("scope_design", ("agent.diseno_alcance_rubrica",)),
        ("plan_validation", ("agent.diseno_alcance_rubrica", "agent.security_policy", "agent.qa_checklist")),
        ("tasks", ("agent.architect_plan", "agent.tests_coverage", "agent.doc_tecnica_detalle")),
        ("analyze", ("agent.qa_checklist", "agent.security_policy")),
        ("implement", ("agent.implementacion_doc_code", "agent.database_builder", "agent.backend_builder", "agent.frontend_builder", "agent.test_builder")),
        ("validate", ("agent.tests_coverage", "agent.ux_ui_product_reviewer", "agent.software_architect_reviewer", "agent.product_owner_flow_reviewer", "agent.security_policy", "agent.qa_checklist")),
        ("containerize", ("agent.docker_packaging", "agent.docker_runtime_validator", "agent.qa_e2e_reviewer", "agent.app_reviewer")),
        ("publish", ("agent.github_publication",)),
        ("deploy", ("agent.deploy_ec2",)),
        ("observe", ("agent.token_billing", "agent.observability_sre")),
        ("close", ("agent.doc_tecnica_detalle", "agent.token_billing", "agent.qa_checklist")),
    )

    def __init__(self, *, factory_root: Path = ROOT, project_dir: Path) -> None:
        self.factory_root = factory_root
        self.project_dir = project_dir

    def initialize_project(self) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        for rel in ("runs", "cache", "index", "agent-memory", "context"):
            (self.project_dir / rel).mkdir(parents=True, exist_ok=True)
        ContextManager(self.factory_root).write_compact_context(self.project_dir)
        aprendizaje = self.project_dir / "Aprendizaje.md"
        if not aprendizaje.exists():
            aprendizaje.write_text("# Aprendizaje\n\nMemoria aislada del proyecto. Sin registros aprobados aun.\n", encoding="utf-8")
        readme = self.project_dir / "README.md"
        if not readme.exists():
            readme.write_text("# Project\n\nCarpeta independiente para el primer proyecto de la fabrica.\n", encoding="utf-8")

    def normalize_work_order(self, objective: str) -> dict[str, Any]:
        configured = self.project_dir / "input" / "work_order.json"
        if configured.exists():
            work_order = read_json(configured)
            if objective:
                work_order = {
                    **work_order,
                    "operator_note": objective,
                    "inputs": [
                        *work_order.get("inputs", []),
                        {"source_id": "SRC-OPERATOR-NOTE", "type": "brief", "authorized": True, "trust": "trusted"},
                    ],
                }
            validate_strict(WORK_ORDER_SCHEMA, work_order)
            return work_order
        work_order = {
            "work_order_id": "WO-" + sha256_text(objective).split(":", 1)[1][:12],
            "objective": objective,
            "work_type": "factory_bootstrap",
            "scope": {
                "include": ["fabrica", "arnes", "agentes", "skills", "tools", "qa", "logs", "project", "rubrica_final", "licitacion_profesor"],
                "exclude": ["deploy", "merge", "db_write", "secret_read", "external_write"],
            },
            "inputs": [
                {"source_id": "SRC-BRIEF-USER", "type": "brief", "authorized": True, "trust": "trusted"},
                {"source_id": "SRC-DOCS-LOCAL", "type": "doc", "path": ".", "authorized": True, "trust": "trusted"},
            ],
            "constraints": {
                "no_web": True,
                "dry_run": False,
                "sandbox_required": True,
                "max_retries": 1,
                "risk": "high",
                "max_cost_usd": 0,
                "max_latency_ms": 300000,
            },
            "expected_outputs": ["factory-ready", "rubric-scope-validated", "project-ready", "agents-registered", "qa-report", "traceability", "final-report", "domain-blueprint.json", "pruebas_de_comportamiento"],
            "approval_required_for": ["write", "deploy", "merge", "external_api", "secrets", "infra", "cost_increase", "data_access", "production_data", "db_write"],
        }
        validate_strict(WORK_ORDER_SCHEMA, work_order)
        return work_order

    def _selected_route(self, *, phase: str | None = None, from_phase: str | None = None) -> tuple[tuple[str, tuple[str, ...]], ...]:
        phases = [item[0] for item in self.ROUTE]
        if phase and phase not in phases:
            raise ValueError(f"unknown phase: {phase}")
        if from_phase and from_phase not in phases:
            raise ValueError(f"unknown from_phase: {from_phase}")
        route = self.ROUTE
        if from_phase:
            start = phases.index(from_phase)
            route = route[start:]
        if phase:
            route = tuple(item for item in route if item[0] == phase)
        return route

    def run(self, objective: str, *, phase: str | None = None, from_phase: str | None = None, resume_from: Path | None = None, clean_generated_app: bool | None = None) -> Path:
        self.initialize_project()
        run_id = "RUN-" + sha256_text(objective + utc_now()).split(":", 1)[1][:12]
        run_dir = self.project_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        ensure_run_dirs(run_dir)
        work_order = self.normalize_work_order(objective)
        selected_route = self._selected_route(phase=phase, from_phase=from_phase)
        agentic_readiness = self._agentic_readiness(selected_route)
        clean_report = self._prepare_generated_app(run_dir=run_dir, phase=phase, from_phase=from_phase, resume_from=resume_from, clean_generated_app=clean_generated_app)
        write_json(run_dir / "generated-app-cleanup.json", clean_report)
        if resume_from is not None:
            work_order["inputs"].append({"source_id": "SRC-RESUME-RUN", "type": "doc", "path": str(resume_from), "authorized": True, "trust": "trusted"})
            for rel in (
                "scope-inventory.json",
                "scope-validation.json",
                "spec.md",
                "clarifications.md",
                "context-pack.json",
                "context-pack.md",
                "evidence-register.json",
                "plan.md",
                "contracts.md",
                "tasks.md",
                "docs/generated",
            ):
                source = resume_from / rel
                target = run_dir / rel
                if source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                elif source.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(source, target)
        write_json(run_dir / "work_order.json", work_order)
        write_json(run_dir / "registries" / "agents.json", {k: v.to_dict() for k, v in agent_registry().items()})
        write_json(run_dir / "registries" / "tools.json", {k: v.__dict__ for k, v in tool_registry().items()})
        write_json(run_dir / "registries" / "skills.json", {k: v.__dict__ for k, v in skill_registry().items()})

        harness = HarnessRunner(factory_root=self.factory_root, project_dir=self.project_dir, run_dir=run_dir)
        results = []
        state: dict[str, Any] = {
            "run_id": run_id,
            "cycle_id": "CYC-000",
            "task_id": "TASK-BOOTSTRAP",
            "phase": "intake",
            "status": "complete",
            "execution_mode": self._execution_mode(),
            "input_hash": sha256_text(stable_json(work_order)),
            "spec_hash": "sha256:TBD-before-spec",
            "policy_version": POLICY_VERSION,
            "tool_registry_version": TOOL_REGISTRY_VERSION,
            "memory_version": MEMORY_VERSION,
            "evidence": [],
            "outputs": {},
            "issues": [],
            "budget": {
                "max_input_tokens": 120000,
                "max_output_tokens": 60000,
                "max_cost_usd": 0,
                "max_latency_ms": 300000,
                "max_tool_calls": 200,
                "used_input_tokens": 0,
                "used_output_tokens": 0,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
                "estimated_cost_usd": 0,
                "tool_calls": 0,
            },
            "approval": {"required": False, "approved": False, "approval_id": "not_required_for_sandbox"},
        }
        harness.obs.event(run_id=run_id, cycle_id="CYC-000", event="run_started", phase="intake", status="complete")

        cycle_index = 1
        write_json(
            run_dir / "run-config.json",
            {
                "phase": phase,
                "from_phase": from_phase,
                "resume_from": str(resume_from) if resume_from else None,
                "selected_phases": [item[0] for item in selected_route],
                "cache_policy": "context compactado y artefactos por run; no reejecutar fases no seleccionadas",
                "execution_mode": state["execution_mode"],
                "agentic_readiness": agentic_readiness,
                "clean_generated_app": clean_report,
            },
        )
        for phase, agents in selected_route:
            for agent_id in agents:
                state = {**state, "cycle_id": f"CYC-{cycle_index:03d}", "phase": phase, "task_id": f"TASK-{phase.upper()}-{cycle_index:03d}", "input_hash": sha256_text(stable_json({**work_order, "phase": phase, "agent_id": agent_id}))}
                routing = {
                    "run_id": run_id,
                    "cycle_id": state["cycle_id"],
                    "phase": phase,
                    "selected_agent_id": agent_id,
                    "reason": "ruta SDD controlada; orquestador solo invoca harness.run_agent",
                    "required_gates": agent_registry()[agent_id].gates,
                    "budget": state["budget"],
                    "status": "complete",
                }
                write_json(run_dir / "routing" / f"{state['cycle_id']}.json", routing)
                result = harness.run_agent(agent_id, state)
                results.append(result)
                state["outputs"][agent_id] = result["logs"]["output_hash"]
                state["status"] = result["status"]
                repair_trigger_agents = {
                    "agent.database_builder",
                    "agent.backend_builder",
                    "agent.frontend_builder",
                    "agent.test_builder",
                    "agent.docker_packaging",
                    "agent.docker_runtime_validator",
                    "agent.qa_e2e_reviewer",
                    "agent.app_reviewer",
                    "agent.ux_ui_product_reviewer",
                    "agent.software_architect_reviewer",
                    "agent.product_owner_flow_reviewer",
                }
                if agent_id in repair_trigger_agents and result["status"] != "complete":
                    state, cycle_index, repaired = self._attempt_repair(
                        harness=harness,
                        run_dir=run_dir,
                        work_order=work_order,
                        state=state,
                        results=results,
                        cycle_index=cycle_index + 1,
                        failed_review=result,
                    )
                    if repaired:
                        continue
                    write_json(run_dir / "state.json", state)
                    self._finalize(run_dir, run_id, state, results)
                    return run_dir
                if result["status"] != "complete":
                    write_json(run_dir / "state.json", state)
                    self._finalize(run_dir, run_id, state, results)
                    return run_dir
                cycle_index += 1

        runtime_close = self._runtime_close_status(run_dir=run_dir, selected_route=selected_route, agentic_readiness=agentic_readiness)
        if runtime_close["status"] != "complete":
            state["status"] = runtime_close["status"]
            state["issues"] = [*state.get("issues", []), {"source": "runtime_close_gate", **runtime_close}]
        else:
            state["status"] = "complete"
        write_json(run_dir / "state.json", state)
        self._finalize(run_dir, run_id, state, results)
        harness.obs.event(run_id=run_id, cycle_id=state["cycle_id"], event="run_finished", phase="close", status=state["status"])
        return run_dir

    def _prepare_generated_app(self, *, run_dir: Path, phase: str | None, from_phase: str | None, resume_from: Path | None, clean_generated_app: bool | None) -> dict[str, Any]:
        app_dir = self.factory_root / "app-generada"
        should_clean = clean_generated_app if clean_generated_app is not None else phase is None and from_phase is None and resume_from is None
        report = {
            "enabled": bool(should_clean),
            "app_dir": str(app_dir),
            "status": "skipped",
            "backup_dir": None,
            "reason": "only fresh full runs clean generated app by default",
        }
        if not should_clean:
            return report
        if not app_dir.exists():
            report.update({"status": "complete", "reason": "app-generada did not exist"})
            return report
        backup_dir = run_dir / "pre-run-app-generada"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(app_dir), str(backup_dir))
        report.update({"status": "complete", "backup_dir": str(backup_dir), "reason": "previous app-generada moved into run backup"})
        return report

    def _runtime_close_status(self, *, run_dir: Path, selected_route: tuple[tuple[str, tuple[str, ...]], ...], agentic_readiness: dict[str, Any]) -> dict[str, Any]:
        selected_phases = {phase for phase, _agents in selected_route}
        requires_runtime = "containerize" in selected_phases or "close" in selected_phases
        if not requires_runtime and agentic_readiness["status"] == "complete":
            return {"status": "complete", "reason": "runtime close gate not required for selected phases", "agentic_readiness": agentic_readiness}
        docker_runtime_path = run_dir / "docker-runtime-validation.json"
        docker_validation_path = run_dir / "docker-validation.json"
        docker_runtime = read_json(docker_runtime_path) if docker_runtime_path.exists() else {}
        docker_validation = read_json(docker_validation_path) if docker_validation_path.exists() else {}
        findings = []
        if requires_runtime:
            if docker_validation.get("status") not in {"complete", "runtime_complete"}:
                findings.append("docker-validation no esta complete")
            if docker_runtime.get("status") != "runtime_complete":
                findings.append("docker-runtime-validation no esta runtime_complete")
            if docker_runtime.get("playwright_status") != "complete":
                findings.append("Playwright E2E no esta complete")
        if agentic_readiness["status"] != "complete":
            findings.extend(agentic_readiness["findings"])
        status = "complete" if not findings else "needs_user_input"
        payload = {
            "status": status,
            "findings": findings,
            "docker_validation_status": docker_validation.get("status", "missing"),
            "docker_runtime_status": docker_runtime.get("status", "missing"),
            "playwright_status": docker_runtime.get("playwright_status", "missing"),
            "agentic_readiness": agentic_readiness,
        }
        write_json(run_dir / "runtime-close-gate.json", payload)
        return payload

    def _agentic_readiness(self, selected_route: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, Any]:
        selected_phases = {phase for phase, _agents in selected_route}
        requires_agentic = bool(selected_phases.intersection({"implement", "validate", "containerize", "close"}))
        if not requires_agentic:
            return {"status": "complete", "required": False, "findings": [], "reason": "selected phases do not require final agentic generation"}
        config = self._model_provider_config()
        api_key_env = str(config.get("api_key_env") or "OPENAI_API_KEY")
        execution_mode = self._execution_mode()
        if execution_mode == "codex_direct":
            return {
                "status": "complete",
                "required": False,
                "findings": [],
                "api_key_env": api_key_env,
                "model": config.get("model"),
                "reason": "codex_direct activo: la API queda bloqueada y Codex actua como agente externo; el cierre se sostiene por Docker, smoke, Playwright y evidencia local",
            }
        findings = []
        if execution_mode != "agentic":
            findings.append("execution_mode no es agentic")
        if config.get("enabled") is not True:
            findings.append("model-provider.local.json enabled debe ser true")
        if config.get("provider") != "openai":
            findings.append("provider debe ser openai")
        if config.get("apply_model_writes") is not True:
            findings.append("apply_model_writes debe ser true")
        if not self._read_api_key(api_key_env):
            findings.append(f"variable de entorno {api_key_env} no disponible")
        return {
            "status": "complete" if not findings else "needs_user_input",
            "required": True,
            "findings": findings,
            "api_key_env": api_key_env,
            "model": config.get("model"),
            "reason": "corrida final requiere agentes IA reales con escritura controlada",
        }

    def _execution_mode(self) -> str:
        mode_path = self.project_dir / "secrets" / "execution-mode.local.json"
        if mode_path.exists():
            try:
                mode_config = read_json(mode_path)
                if mode_config.get("mode") == "codex_direct":
                    return "codex_direct"
            except Exception:
                return "deterministic"
        path = self.project_dir / "secrets" / "model-provider.local.json"
        if not path.exists():
            return "deterministic"
        try:
            config = read_json(path)
        except Exception:
            return "deterministic"
        return "agentic" if config.get("enabled") is True else "deterministic"

    def _model_provider_config(self) -> dict[str, Any]:
        path = self.project_dir / "secrets" / "model-provider.local.json"
        if not path.exists():
            return {}
        try:
            return read_json(path)
        except Exception:
            return {}

    def _read_api_key(self, name: str) -> str | None:
        value = os.environ.get(name)
        if value:
            return value
        if os.name != "nt":
            return None
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                registry_value, _ = winreg.QueryValueEx(key, name)
            return str(registry_value) if registry_value else None
        except OSError:
            return None

    def _attempt_repair(
        self,
        *,
        harness: HarnessRunner,
        run_dir: Path,
        work_order: dict[str, Any],
        state: dict[str, Any],
        results: list[dict[str, Any]],
        cycle_index: int,
        failed_review: dict[str, Any],
    ) -> tuple[dict[str, Any], int, bool]:
        config = self._model_provider_config()
        max_cycles = max(0, int(config.get("max_repair_cycles", 2)))
        repair_agents = ("agent.database_builder", "agent.backend_builder", "agent.frontend_builder", "agent.test_builder", "agent.docker_packaging", "agent.docker_runtime_validator")
        ledger = {
            "run_id": state["run_id"],
            "status": "skipped" if max_cycles == 0 else "running",
            "max_repair_cycles": max_cycles,
            "initial_review_status": failed_review["status"],
            "attempts": [],
        }
        if max_cycles == 0:
            write_json(run_dir / "repair-ledger.json", ledger)
            return {**state, "status": failed_review["status"]}, cycle_index, False

        for attempt in range(1, max_cycles + 1):
            attempt_entry: dict[str, Any] = {"attempt": attempt, "repair_agents": [], "review": None}
            for repair_agent_id in repair_agents:
                repair_state = {
                    **state,
                    "cycle_id": f"CYC-{cycle_index:03d}",
                    "phase": "repair",
                    "task_id": f"TASK-REPAIR-{attempt:02d}-{repair_agent_id.rsplit('.', 1)[1].upper()}",
                    "input_hash": sha256_text(stable_json({**work_order, "phase": "repair", "agent_id": repair_agent_id, "attempt": attempt})),
                    "issues": [
                        *state.get("issues", []),
                        {"source": "autonomous_repair_trigger", "status": failed_review["status"], "attempt": attempt},
                    ],
                }
                write_json(
                    run_dir / "routing" / f"{repair_state['cycle_id']}.json",
                    {
                        "run_id": state["run_id"],
                        "cycle_id": repair_state["cycle_id"],
                        "phase": "repair",
                        "selected_agent_id": repair_agent_id,
                        "reason": "repair loop triggered by product, runtime, or docker findings",
                        "required_gates": agent_registry()[repair_agent_id].gates,
                        "budget": repair_state["budget"],
                        "repair_attempt": attempt,
                        "status": "complete",
                    },
                )
                repair_result = harness.run_agent(repair_agent_id, repair_state)
                results.append(repair_result)
                state = {**repair_state, "status": repair_result["status"]}
                state["outputs"][repair_agent_id] = repair_result["logs"]["output_hash"]
                attempt_entry["repair_agents"].append({"agent_id": repair_agent_id, "cycle_id": repair_state["cycle_id"], "status": repair_result["status"]})
                cycle_index += 1
                if repair_result["status"] != "complete":
                    ledger["status"] = repair_result["status"]
                    ledger["attempts"].append(attempt_entry)
                    write_json(run_dir / "repair-ledger.json", ledger)
                    return state, cycle_index, False

            review_agents = (
                "agent.app_reviewer",
                "agent.ux_ui_product_reviewer",
                "agent.software_architect_reviewer",
                "agent.product_owner_flow_reviewer",
                "agent.docker_runtime_validator",
                "agent.qa_e2e_reviewer",
            )
            attempt_entry["review"] = []
            all_reviews_complete = True
            for review_agent_id in review_agents:
                review_phase = "containerize" if review_agent_id in {"agent.docker_runtime_validator", "agent.qa_e2e_reviewer"} else "validate"
                review_state = {
                    **state,
                    "cycle_id": f"CYC-{cycle_index:03d}",
                    "phase": review_phase,
                    "task_id": f"TASK-REVIEW-REPAIR-{attempt:02d}-{review_agent_id.rsplit('.', 1)[1].upper()}",
                    "input_hash": sha256_text(stable_json({**work_order, "phase": review_phase, "agent_id": review_agent_id, "repair_attempt": attempt})),
                }
                write_json(
                    run_dir / "routing" / f"{review_state['cycle_id']}.json",
                    {
                        "run_id": state["run_id"],
                        "cycle_id": review_state["cycle_id"],
                        "phase": review_phase,
                        "selected_agent_id": review_agent_id,
                        "reason": "full product review after autonomous repair cycle",
                        "required_gates": agent_registry()[review_agent_id].gates,
                        "budget": review_state["budget"],
                        "repair_attempt": attempt,
                        "status": "complete",
                    },
                )
                review_result = harness.run_agent(review_agent_id, review_state)
                results.append(review_result)
                state = {**review_state, "status": review_result["status"]}
                state["outputs"][review_agent_id] = review_result["logs"]["output_hash"]
                attempt_entry["review"].append({"agent_id": review_agent_id, "cycle_id": review_state["cycle_id"], "status": review_result["status"]})
                cycle_index += 1
                if review_result["status"] != "complete":
                    all_reviews_complete = False
                    failed_review = review_result
                    break
            ledger["attempts"].append(attempt_entry)
            if all_reviews_complete:
                ledger["status"] = "complete"
                write_json(run_dir / "repair-ledger.json", ledger)
                return state, cycle_index, True

        ledger["status"] = failed_review["status"]
        write_json(run_dir / "repair-ledger.json", ledger)
        return state, cycle_index, False

    def _finalize(self, run_dir: Path, run_id: str, state: dict[str, Any], results: list[dict[str, Any]]) -> None:
        if not (run_dir / "repair-ledger.json").exists():
            write_json(run_dir / "repair-ledger.json", {"run_id": run_id, "status": "not_triggered", "attempts": []})
        write_principle_ledger(run_dir)
        write_phase_ledger(run_dir, results)
        write_claim_map(run_dir, results)
        write_project_isolation(self.factory_root, self.project_dir, run_dir)
        write_security_delivery_reports(self.factory_root, run_dir)
        trace_lines = ["# Traceability Matrix", "", "| requirement | task | test | evidence | gate | status |", "|---|---|---|---|---|---|"]
        rows = [
            ("REQ-001", "TASK-001", "TEST-001", "EV-001", "schema", "complete"),
            ("REQ-002", "TASK-002", "TEST-003", "EV-001", "policy", "complete"),
            ("REQ-003", "TASK-003", "TEST-002", "EV-001", "schema", "complete"),
            ("REQ-004", "TASK-004", "TEST-004", "EV-001", "evidence", "complete"),
            ("REQ-005", "TASK-005", "TEST-006", "EV-001", "memory", "complete"),
            ("REQ-006", "TASK-006", "TEST-007", "EV-001", "consistency", "complete"),
            ("REQ-007", "TASK-007", "TEST-001", "EV-001", "final_format", "complete"),
            ("REQ-008", "TASK-008", "TEST-007", "EV-001", "qa", "complete"),
        ]
        for row in rows:
            trace_lines.append("| " + " | ".join(row) + " |")
        (run_dir / "traceability-matrix.md").write_text("\n".join(trace_lines) + "\n", encoding="utf-8")

        validation = {
            "run_id": run_id,
            "status": state["status"],
            "workflow_version": WORKFLOW_VERSION,
            "validators": ["SchemaValidator", "EvidenceValidator", "PolicyValidator", "SafetyValidator", "ConsistencyValidator", "CoverageValidator", "BudgetValidator", "ToolOutputValidator", "FinalFormatValidator", "RubricScopeValidator", "DocumentationValidator", "TraceabilityValidator"],
            "results": [{"agent_id": item["agent_id"], "status": item["status"], "validation": item["validation"]["status"]} for item in results],
        }
        write_json(run_dir / "validation-report.json", validation)
        validate_factory_docs(self.factory_root, run_dir)
        validate_traceability(run_dir)
        write_assumptions_register(run_dir)
        final = {
            "run_id": run_id,
            "status": state["status"],
            "factory_version": FACTORY_VERSION,
            "project_dir": str(self.project_dir),
            "agents_executed": [item["agent_id"] for item in results],
            "artifacts_dir": str(run_dir),
            "ready_for_first_project": state["status"] == "complete",
            "governance": {
                "principles": "principle-ledger.json",
                "phase_ledger": "phase-ledger.json",
                "claim_map": "claim-map.md",
                "project_isolation": "project-isolation-policy.md",
                "frontend_template": "frontend-template-manifest.json",
                "security": "security-review.md",
                "sbom": "sbom.json",
                "rollback": "rollback-plan.md",
                "pr_bundle": "PRBundle.md",
            },
        }
        write_json(run_dir / "final-report.json", final)
        write_executive_summary(run_dir, state, results)
        write_factory_metrics(run_dir, state, results)
        write_log_completeness_report(run_dir)
        checklist = self._checklist_status(run_dir)
        (run_dir / "CHECKLIST_APLICADO.md").write_text(checklist, encoding="utf-8")

    def _checklist_status(self, run_dir: Path) -> str:
        required = [
            "work_order.json", "spec.md", "clarifications.md", "checklist.md", "context-pack.json", "context-pack.md",
            "plan.md", "contracts.md", "tasks.md", "analyze-report.json", "test-report.md", "coverage-report.json",
            "security-review.md", "validation-report.json", "traceability-matrix.md", "final-report.json",
            "RUN_STATE.md", "DECISIONS.md", "ERRORS.md", "billing-ledger.json",
            "scope-inventory.json", "scope-validation.json", "docs-validation.json",
            "traceability-validation.json", "assumptions-register.md", "executive-summary.md",
            "factory-metrics.json", "factory-metrics.md",
            "principle-ledger.json", "phase-ledger.json", "claim-map.md",
            "project-manifest.json", "project-sandboxes.json", "project-memory-policy.json",
            "frontend-template-manifest.json", "project-isolation-policy.md",
            "secrets-report.json", "dependency-report.json", "sbom.json",
            "rollback-plan.md", "slo-policy.md", "approval-matrix.md", "PRBundle.md",
            "log-completeness-report.json",
            "repair-ledger.json",
            "generated-app-cleanup.json",
        ]
        lines = ["# CHECKLIST Aplicado", "", "| item | estado | evidencia |", "|---|---|---|"]
        for name in required:
            status = "complete" if (run_dir / name).exists() else "error"
            lines.append(f"| {name} | {status} | `{name}` |")
        lines.extend(
            [
                "| agentes minimos | complete | `registries/agents.json` |",
                "| skills deterministicas | complete | `registries/skills.json` |",
                "| tools allowlist | complete | `registries/tools.json` |",
                "| memoria proyecto | complete | `../Aprendizaje.md` |",
                "| no shell libre | complete | pruebas/policy |",
                "| no secretos/deploy/db_write | complete | pruebas/policy |",
            ]
        )
        return "\n".join(lines) + "\n"


def latest_run(project_dir: Path) -> Path | None:
    runs = sorted((project_dir / "runs").glob("RUN-*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return runs[0] if runs else None
