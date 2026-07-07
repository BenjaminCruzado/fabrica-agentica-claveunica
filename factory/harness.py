from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .agents import AGENT_FUNCTIONS, output_hash
from .context import ContextManager
from .memory import MemoryGate
from .observability import Observability
from .policy import PolicyEngine
from .registry import AgentSpec, agent_registry, tool_registry
from .schemas import SchemaError, validate_strict, CYCLE_STATE_SCHEMA
from .utils import sha256_text, stable_json, write_json
from .validators import ValidatorChain


class UnknownAgentError(ValueError):
    pass


class HarnessRunner:
    def __init__(self, *, factory_root: Path, project_dir: Path, run_dir: Path) -> None:
        self.factory_root = factory_root
        self.project_dir = project_dir
        self.run_dir = run_dir
        self.agents = agent_registry()
        self.tools = tool_registry()
        self.policy = PolicyEngine(self.tools)
        self.context = ContextManager(factory_root)
        self.memory = MemoryGate(factory_root, project_dir)
        self.validators = ValidatorChain()
        self.obs = Observability(run_dir)

    def _agent(self, agent_id: str) -> AgentSpec:
        try:
            return self.agents[agent_id]
        except KeyError as exc:
            raise UnknownAgentError(agent_id) from exc

    def run_agent(self, agent_id: str, state: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            validate_strict(CYCLE_STATE_SCHEMA, state)
        except SchemaError as exc:
            return self._error_result(agent_id, state, "schema_unrecoverable", str(exc))

        agent = self._agent(agent_id)
        policy_decision = self.policy.check_agent(agent)
        if policy_decision.status != "complete":
            return self._blocked_result(agent, state, policy_decision.status, policy_decision.code, policy_decision.message)

        side_effect_decision = self.policy.check_state_side_effects(state, agent)
        if side_effect_decision.status != "complete":
            return self._blocked_result(agent, state, side_effect_decision.status, side_effect_decision.code, side_effect_decision.message)

        self.memory.read_report(self.run_dir)
        context_pack = self.context.write_context_pack(self.run_dir, state.get("task_id", "") + " " + state.get("phase", ""))
        for tool_id in agent.allowed_tools:
            decision = self.policy.check_tool(agent, tool_id, state["approval"])
            self.obs.tool_event(
                tool_id,
                {
                    "run_id": state["run_id"],
                    "cycle_id": state["cycle_id"],
                    "tool_id": tool_id,
                    "caller_agent_id": agent_id,
                    "operation": "policy_check",
                    "status": "success" if decision.status == "complete" else "blocked",
                    "input_hash": state["input_hash"],
                    "output_hash": sha256_text(stable_json(decision.__dict__)),
                    "latency_ms": 0,
                    "cache_hit": False,
                    "side_effects": self.tools[tool_id].side_effects,
                    "sandbox": self.tools[tool_id].sandbox_required,
                    "source_ids": [],
                    "error_code": None if decision.status == "complete" else decision.code,
                },
            )
            if decision.status not in {"complete", "needs_user_input"}:
                return self._blocked_result(agent, state, decision.status, decision.code, decision.message)

        fn = AGENT_FUNCTIONS[agent_id]
        output = fn(agent, state, self.run_dir, context_pack)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        state["budget"]["tool_calls"] += min(len(agent.allowed_tools), state["budget"]["max_tool_calls"])
        state["budget"]["used_input_tokens"] += max(1, len(stable_json(state)) // 4)
        state["budget"]["used_output_tokens"] += max(1, len(stable_json(output)) // 4)

        validation_items = self.validators.validate_output(state=state, output=output, required_gates=agent.gates, run_dir=self.run_dir)
        status = self.validators.status_from_items(validation_items)
        result = {
            "run_id": state["run_id"],
            "cycle_id": state["cycle_id"],
            "agent_id": agent_id,
            "status": status,
            "output": output,
            "validation": self.validators.as_report(validation_items),
            "logs": {
                "input_hash": state["input_hash"],
                "output_hash": output_hash(output),
                "log_id": f"LOG-{state['cycle_id']}-{agent_id}",
            },
            "budget": state["budget"],
        }
        write_json(self.run_dir / "agent-results" / f"{state['cycle_id']}-{agent_id}.json", result)
        self.obs.agent_event(
            agent_id,
            {
                "run_id": state["run_id"],
                "cycle_id": state["cycle_id"],
                "agent_id": agent_id,
                "phase": state["phase"],
                "status": status,
                "input_hash": state["input_hash"],
                "output_hash": result["logs"]["output_hash"],
                "tool_calls": list(agent.allowed_tools),
                "evidence_ids": output.get("evidence_refs", []),
                "input_tokens": state["budget"]["used_input_tokens"],
                "output_tokens": state["budget"]["used_output_tokens"],
                "cached_tokens": state["budget"]["cached_tokens"],
                "reasoning_tokens": state["budget"]["reasoning_tokens"],
                "latency_ms": elapsed_ms,
                "estimated_cost_usd": state["budget"]["estimated_cost_usd"],
            },
        )
        self.obs.add_billing_phase(state, agent_id, output_tokens=max(1, len(stable_json(output)) // 4), tool_calls=len(agent.allowed_tools), latency_ms=elapsed_ms)
        self.obs.event(run_id=state["run_id"], cycle_id=state["cycle_id"], event="agent_finished", phase=state["phase"], agent_id=agent_id, status=status)
        return result

    def _blocked_result(self, agent: AgentSpec, state: dict[str, Any], status: str, code: str, message: str) -> dict[str, Any]:
        output = {
            "agent_id": agent.agent_id,
            "phase": state.get("phase", "intake"),
            "evidence_refs": [],
            "critical_claims": [],
            "policy_findings": [code],
            "artifacts": [],
            "error": message,
        }
        result = {
            "run_id": state.get("run_id", "RUN-TBD"),
            "cycle_id": state.get("cycle_id", "CYC-TBD"),
            "agent_id": agent.agent_id,
            "status": status,
            "output": output,
            "validation": {"status": status, "items": [{"validator": "PolicyValidator", "status": status, "code": code, "message": message}]},
            "logs": {
                "input_hash": state.get("input_hash", "sha256:TBD"),
                "output_hash": output_hash(output),
                "log_id": f"LOG-{state.get('cycle_id', 'CYC-TBD')}-{agent.agent_id}",
            },
            "budget": state.get("budget", {}),
        }
        write_json(self.run_dir / "agent-results" / f"{state.get('cycle_id', 'CYC-TBD')}-{agent.agent_id}.json", result)
        return result

    def _error_result(self, agent_id: str, state: dict[str, Any], code: str, message: str) -> dict[str, Any]:
        output = {
            "agent_id": agent_id,
            "phase": state.get("phase", "intake"),
            "evidence_refs": [],
            "critical_claims": [],
            "policy_findings": [code],
            "artifacts": [],
            "error": message,
        }
        return {
            "run_id": state.get("run_id", "RUN-TBD"),
            "cycle_id": state.get("cycle_id", "CYC-TBD"),
            "agent_id": agent_id,
            "status": "error",
            "output": output,
            "validation": {"status": "error", "items": [{"validator": "SchemaValidator", "status": "error", "code": code, "message": message}]},
            "logs": {
                "input_hash": state.get("input_hash", "sha256:TBD"),
                "output_hash": output_hash(output),
                "log_id": f"LOG-{state.get('cycle_id', 'CYC-TBD')}-{agent_id}",
            },
            "budget": state.get("budget", {}),
        }
