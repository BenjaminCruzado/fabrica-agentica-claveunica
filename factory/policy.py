from __future__ import annotations

from dataclasses import dataclass

from .registry import AgentSpec, ToolSpec


@dataclass(frozen=True)
class PolicyDecision:
    status: str
    code: str
    message: str


class PolicyEngine:
    def __init__(self, tools: dict[str, ToolSpec]) -> None:
        self.tools = tools

    def check_agent(self, agent: AgentSpec) -> PolicyDecision:
        if agent.permissions.get("deploy"):
            return PolicyDecision("error", "deploy_permission_denied", "Ningun agente puede desplegar.")
        if agent.permissions.get("read_secrets"):
            return PolicyDecision("error", "secret_permission_denied", "Ningun agente puede leer secretos.")
        for tool_id in agent.allowed_tools:
            if tool_id not in self.tools:
                return PolicyDecision("error", "unknown_tool", f"Tool no registrada: {tool_id}")
            if tool_id in agent.forbidden_tools:
                return PolicyDecision("error", "forbidden_tool_allowlisted", f"Tool prohibida en allowlist: {tool_id}")
        return PolicyDecision("complete", "policy_passed", "Agente cumple policy.")

    def check_tool(self, agent: AgentSpec, tool_id: str, approval: dict) -> PolicyDecision:
        if tool_id not in self.tools:
            return PolicyDecision("error", "unknown_tool", f"Tool no registrada: {tool_id}")
        if tool_id not in agent.allowed_tools:
            return PolicyDecision("error", "blocked_by_policy", f"Tool no allowlisted para {agent.agent_id}: {tool_id}")
        if tool_id in agent.forbidden_tools:
            return PolicyDecision("error", "blocked_by_policy", f"Tool prohibida para {agent.agent_id}: {tool_id}")
        tool = self.tools[tool_id]
        if tool_id in {"shell.free", "secrets.read", "deploy.direct", "db.write"}:
            return PolicyDecision("error", "blocked_by_policy", f"Tool globalmente prohibida: {tool_id}")
        if tool.side_effects in {"write", "external"} and not approval.get("approved"):
            return PolicyDecision("needs_user_input", "human_approval_required", f"Side effect requiere aprobacion: {tool.side_effects}")
        if tool.type == "test" and not tool.sandbox_required:
            return PolicyDecision("error", "sandbox_required", "Tests deben ejecutarse en sandbox.")
        return PolicyDecision("complete", "tool_allowed", "Tool permitida.")

    def check_state_side_effects(self, state: dict, agent: AgentSpec) -> PolicyDecision:
        if state["phase"] in {"pr_deploy"} and not state["approval"]["approved"]:
            return PolicyDecision("needs_user_input", "human_approval_required", "PR/deploy requiere aprobacion humana.")
        if not state["approval"]["approved"] and agent.permissions.get("external_api"):
            return PolicyDecision("needs_user_input", "human_approval_required", "API externa requiere aprobacion.")
        return PolicyDecision("complete", "side_effect_policy_passed", "Side effects contenidos.")
