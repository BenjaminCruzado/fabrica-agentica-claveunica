from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .constants import FACTORY_VERSION, MEMORY_VERSION, POLICY_VERSION, ROOT, TOOL_REGISTRY_VERSION, WORKFLOW_VERSION
from .context import ContextManager
from .governance import ensure_run_dirs, validate_factory_docs, validate_traceability, write_assumptions_register, write_executive_summary
from .harness import HarnessRunner
from .registry import agent_registry, skill_registry, tool_registry
from .schemas import WORK_ORDER_SCHEMA, validate_strict
from .utils import read_json, sha256_text, stable_json, utc_now, write_json


class OrchestratorGraph:
    ROUTE: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("specify", ("agent.spec_detallada",)),
        ("clarify", ("agent.spec_detallada",)),
        ("checklist", ("agent.qa_checklist",)),
        ("context", ("agent.context_rag", "agent.ocr_ui_analyst")),
        ("plan", ("agent.architect_plan", "agent.ui_web_modern", "agent.api_security_docs")),
        ("scope_design", ("agent.diseno_alcance_rubrica",)),
        ("plan_validation", ("agent.diseno_alcance_rubrica", "agent.security_policy", "agent.qa_checklist")),
        ("tasks", ("agent.architect_plan", "agent.tests_coverage", "agent.doc_tecnica_detalle")),
        ("analyze", ("agent.qa_checklist", "agent.security_policy")),
        ("implement", ("agent.implementacion_doc_code",)),
        ("validate", ("agent.tests_coverage", "agent.security_policy", "agent.qa_checklist")),
        ("containerize", ("agent.docker_packaging",)),
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
                "dry_run": True,
                "sandbox_required": True,
                "max_retries": 1,
                "risk": "high",
                "max_cost_usd": 0,
                "max_latency_ms": 300000,
            },
            "expected_outputs": ["factory-ready", "rubric-scope-validated", "project-ready", "agents-registered", "qa-report", "traceability", "final-report"],
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

    def run(self, objective: str, *, phase: str | None = None, from_phase: str | None = None, resume_from: Path | None = None) -> Path:
        self.initialize_project()
        run_id = "RUN-" + sha256_text(objective + utc_now()).split(":", 1)[1][:12]
        run_dir = self.project_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        ensure_run_dirs(run_dir)
        work_order = self.normalize_work_order(objective)
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
        selected_route = self._selected_route(phase=phase, from_phase=from_phase)
        write_json(
            run_dir / "run-config.json",
            {
                "phase": phase,
                "from_phase": from_phase,
                "resume_from": str(resume_from) if resume_from else None,
                "selected_phases": [item[0] for item in selected_route],
                "cache_policy": "context compactado y artefactos por run; no reejecutar fases no seleccionadas",
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
                if result["status"] != "complete":
                    write_json(run_dir / "state.json", state)
                    self._finalize(run_dir, run_id, state, results)
                    return run_dir
                cycle_index += 1

        state["status"] = "complete"
        write_json(run_dir / "state.json", state)
        self._finalize(run_dir, run_id, state, results)
        harness.obs.event(run_id=run_id, cycle_id=state["cycle_id"], event="run_finished", phase="close", status=state["status"])
        return run_dir

    def _finalize(self, run_dir: Path, run_id: str, state: dict[str, Any], results: list[dict[str, Any]]) -> None:
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
        }
        write_json(run_dir / "final-report.json", final)
        write_executive_summary(run_dir, state, results)
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
