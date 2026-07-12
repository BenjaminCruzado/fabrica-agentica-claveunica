from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..observability import Observability
from ..policy import PolicyEngine
from ..registry import AgentSpec, ToolSpec
from ..utils import write_json
from .contracts import AgentContract
from .model_client import ModelClient
from .safe_writer import SafeFileWriter
from .session import AgentSession
from .tool_executor import ToolExecutor


AgentFunction = Callable[[AgentSpec, dict[str, Any], Path, dict[str, Any]], dict[str, Any]]

CRITICAL_AGENTIC_AGENTS = {
    "agent.implementacion_doc_code",
    "agent.database_builder",
    "agent.backend_builder",
    "agent.frontend_builder",
    "agent.test_builder",
    "agent.docker_packaging",
    "agent.docker_runtime_validator",
    "agent.app_reviewer",
    "agent.ux_ui_product_reviewer",
    "agent.software_architect_reviewer",
    "agent.qa_e2e_reviewer",
    "agent.product_owner_flow_reviewer",
}

FALLBACK_ADAPTERS = {
    "adapter_error",
    "missing_api_key",
    "not_configured",
    "unsupported_provider",
    "cost_guard",
}


class AgentRuntime:
    def __init__(self, *, run_dir: Path, workspace: Path, tools: dict[str, ToolSpec], policy: PolicyEngine, observability: Observability) -> None:
        self.run_dir = run_dir
        self.workspace = workspace
        self.project_dir = run_dir.parent.parent
        self.tools = tools
        self.policy = policy
        self.obs = observability
        self.model_client = ModelClient(project_dir=self.project_dir)
        self.tool_executor = ToolExecutor(tools=tools, policy=policy, workspace=workspace)
        self.safe_writer = SafeFileWriter(repo_root=workspace, run_dir=run_dir)

    def run(self, *, agent: AgentSpec, state: dict[str, Any], context_pack: dict[str, Any], fn: AgentFunction) -> dict[str, Any]:
        contract = AgentContract.from_agent_spec(agent)
        contracts_dir = self.run_dir / "agent-contracts"
        contract.write_yaml(contracts_dir / f"{agent.agent_id}.yaml")
        session = AgentSession(
            run_id=state["run_id"],
            cycle_id=state["cycle_id"],
            agent_id=agent.agent_id,
            execution_mode=state.get("execution_mode", "deterministic"),
            contract_hash=contract.contract_hash,
        )
        plan = self.model_client.plan(contract=contract.to_dict(), context_pack=context_pack, state=state)
        session.add_step("plan", plan.status, "runtime plan created", adapter=plan.adapter, steps=list(plan.steps), actions=[item.to_dict() for item in plan.actions])

        tool_preflights = []
        for tool_id in agent.allowed_tools:
            result = self.tool_executor.preflight(agent, tool_id, state["approval"])
            tool_preflights.append(result.to_dict())
            session.add_step("tool_preflight", result.status, result.reason or "checked", tool_id=tool_id, command=list(result.command))
            self.obs.tool_event(
                tool_id,
                {
                    "run_id": state["run_id"],
                    "cycle_id": state["cycle_id"],
                    "tool_id": tool_id,
                    "caller_agent_id": agent.agent_id,
                    "operation": "runtime_preflight",
                    "status": result.status,
                    "input_hash": state["input_hash"],
                    "output_hash": result.output_hash,
                    "latency_ms": result.duration_ms,
                    "cache_hit": False,
                    "side_effects": self.tools[tool_id].side_effects,
                    "sandbox": self.tools[tool_id].sandbox_required,
                    "source_ids": [],
                    "error_code": None if result.status in {"complete", "warning", "needs_user_input"} else result.status,
                },
            )
            if result.status == "error":
                session.add_finding("error", "tool_policy", f"Tool {tool_id} failed preflight: {result.reason}")

        model_action_results = self._run_model_actions(agent=agent, state=state, plan=plan, session=session)
        output = fn(agent, state, self.run_dir, context_pack)
        ai_code_writer = self._ai_code_writer_summary(agent=agent, state=state, plan=plan, model_action_results=model_action_results)
        output["ai_code_writer"] = ai_code_writer
        if ai_code_writer["failed_writes"]:
            output.setdefault("policy_findings", []).append("model_file_policy_failed")
        if self._is_blocking_agentic_fallback(agent=agent, state=state, plan=plan):
            message = f"{agent.agent_id} es critico y no recibio plan IA valido ({plan.adapter})."
            output["coverage"] = "blocked"
            output.setdefault("policy_findings", []).append("critical_agentic_fallback")
            output.setdefault("runtime_findings", []).append(
                {
                    "severity": "error",
                    "area": "agent_runtime",
                    "message": message,
                    "adapter": plan.adapter,
                    "error": plan.error,
                }
            )
            session.add_finding("error", "critical_agentic_fallback", message, adapter=plan.adapter, error=plan.error)
        output["execution_mode"] = state.get("execution_mode", "deterministic")
        output["agent_contract"] = {
            "path": str(contracts_dir / f"{agent.agent_id}.yaml"),
            "hash": contract.contract_hash,
            "source": contract.source,
        }
        output["runtime_plan"] = plan.to_dict()
        output["tool_preflights"] = tool_preflights
        output["model_action_results"] = model_action_results
        usage = plan.usage or {}
        if usage:
            output["model_usage"] = usage
            output["model_estimated_cost_usd"] = plan.estimated_cost_usd
        if session.findings:
            output.setdefault("runtime_findings", []).extend(session.findings)

        session.add_step("execute", output.get("coverage", "unknown"), "agent function executed", artifacts=output.get("artifacts", []))
        write_json(self.run_dir / "agent-sessions" / f"{state['cycle_id']}-{agent.agent_id}.json", session.to_dict())
        self._write_ai_code_writer_ledger(agent=agent, state=state, summary=ai_code_writer, model_action_results=model_action_results)
        return output

    def _is_blocking_agentic_fallback(self, *, agent: AgentSpec, state: dict[str, Any], plan: Any) -> bool:
        return (
            state.get("execution_mode") == "agentic"
            and agent.agent_id in CRITICAL_AGENTIC_AGENTS
            and plan.adapter in FALLBACK_ADAPTERS
        )

    def _run_model_actions(self, *, agent: AgentSpec, state: dict[str, Any], plan: Any, session: AgentSession) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        if not plan.actions:
            session.add_step("model_actions", "skipped", "no model actions requested")
            return results

        for action in plan.actions:
            if action.action == "finish":
                session.add_step("model_action", "complete", action.reason or "model finished", action=action.to_dict())
                continue
            if action.action == "needs_user_input":
                session.add_finding("needs_user_input", "model_action", action.reason or "model requested user input")
                session.add_step("model_action", "needs_user_input", action.reason or "model requested user input", action=action.to_dict())
                continue
            if action.action != "tool":
                if action.action in {"write_file", "patch_file"}:
                    result = self._run_file_action(action=action, plan=plan, session=session)
                    results.append(result)
                    continue
                session.add_finding("warning", "model_action", f"Unknown model action ignored: {action.action}")
                continue

            if not plan.execute_tools:
                session.add_step("model_tool", "skipped", "model tool execution disabled by local config", action=action.to_dict())
                results.append({"action": action.to_dict(), "status": "skipped", "reason": "execute_tools=false"})
                continue

            decision = self.policy.check_tool(agent, action.tool_id, state["approval"])
            if decision.status != "complete":
                session.add_finding(decision.status, "model_tool_policy", decision.message)
                session.add_step("model_tool", decision.status, decision.message, action=action.to_dict())
                results.append({"action": action.to_dict(), "status": decision.status, "reason": decision.message})
                continue

            result = self.tool_executor.execute(agent, action.tool_id, state["approval"], cwd=self.workspace)
            item = result.to_dict()
            item["action"] = action.to_dict()
            results.append(item)
            session.add_step("model_tool", result.status, result.reason or action.reason or "tool executed", tool_id=action.tool_id, output_hash=result.output_hash)
            self.obs.tool_event(
                action.tool_id,
                {
                    "run_id": state["run_id"],
                    "cycle_id": state["cycle_id"],
                    "tool_id": action.tool_id,
                    "caller_agent_id": agent.agent_id,
                    "operation": "model_action_execute",
                    "status": result.status,
                    "input_hash": state["input_hash"],
                    "output_hash": result.output_hash,
                    "latency_ms": result.duration_ms,
                    "cache_hit": False,
                    "side_effects": self.tools[action.tool_id].side_effects,
                    "sandbox": self.tools[action.tool_id].sandbox_required,
                    "source_ids": [],
                    "error_code": None if result.status in {"complete", "warning", "needs_user_input"} else result.status,
                },
            )

        if results:
            write_json(self.run_dir / "tool-results" / f"{state['cycle_id']}-{agent.agent_id}.json", results)
        return results

    def _run_file_action(self, *, action: Any, plan: Any, session: AgentSession) -> dict[str, Any]:
        if not plan.apply_writes:
            session.add_step("model_file", "skipped", "model file writes disabled by local config", action=action.to_dict())
            return {"action": action.to_dict(), "status": "skipped", "reason": "apply_model_writes=false"}
        if action.action == "write_file":
            result = self.safe_writer.write_file(relative_path=action.path, content=action.content)
        else:
            result = self.safe_writer.patch_file(relative_path=action.path, content=action.content)
        payload = result.to_dict()
        payload["model_action"] = action.to_dict()
        session.add_step("model_file", result.status, result.reason, path=action.path, output_hash=result.output_hash)
        if result.status != "complete":
            session.add_finding(result.status, "model_file_policy", result.reason, path=action.path)
        return payload

    def _ai_code_writer_summary(self, *, agent: AgentSpec, state: dict[str, Any], plan: Any, model_action_results: list[dict[str, Any]]) -> dict[str, Any]:
        file_actions = [item for item in model_action_results if self._model_result_action_name(item) in {"write_file", "patch_file"}]
        applied = [item for item in file_actions if item.get("status") == "complete"]
        skipped = [item for item in file_actions if item.get("status") == "skipped"]
        failed = [item for item in file_actions if item.get("status") not in {"complete", "skipped"}]
        return {
            "mode": "ai_code_writer_controlled",
            "agent_id": agent.agent_id,
            "execution_mode": state.get("execution_mode", "deterministic"),
            "model_adapter": plan.adapter,
            "model_status": plan.status,
            "enabled": state.get("execution_mode") == "agentic" and plan.adapter == "openai-responses",
            "apply_writes": bool(plan.apply_writes),
            "execute_tools": bool(plan.execute_tools),
            "allowed_write_roots": [
                "app-generada",
                f"project/runs/{state.get('run_id')}/ai-generated",
                f"project/runs/{state.get('run_id')}/docs/generated",
            ],
            "file_actions": len(file_actions),
            "applied_writes": len(applied),
            "skipped_writes": len(skipped),
            "failed_writes": len(failed),
            "blocked_by_policy": [item.get("reason", "") for item in failed],
            "requires_safe_writer": True,
        }

    @staticmethod
    def _model_result_action_name(item: dict[str, Any]) -> str:
        action = item.get("action")
        if isinstance(action, dict):
            return str(action.get("action") or "")
        if isinstance(action, str):
            return action
        model_action = item.get("model_action")
        if isinstance(model_action, dict):
            return str(model_action.get("action") or "")
        return ""

    def _write_ai_code_writer_ledger(self, *, agent: AgentSpec, state: dict[str, Any], summary: dict[str, Any], model_action_results: list[dict[str, Any]]) -> None:
        write_json(
            self.run_dir / "ai-code-writer-ledger" / f"{state['cycle_id']}-{agent.agent_id}.json",
            {
                "summary": summary,
                "model_action_results": model_action_results,
            },
        )
