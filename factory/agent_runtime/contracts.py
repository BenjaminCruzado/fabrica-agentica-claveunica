from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..registry import AgentSpec
from ..utils import sha256_text, stable_json


@dataclass(frozen=True)
class AgentContract:
    agent_id: str
    role: str
    phase_scope: tuple[str, ...]
    max_steps: int
    allowed_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    gates: tuple[str, ...]
    permissions: dict[str, bool]
    escalation_policy: str
    correction_policy: str
    source: str

    @classmethod
    def from_agent_spec(cls, agent: AgentSpec) -> "AgentContract":
        return cls(
            agent_id=agent.agent_id,
            role=agent.single_responsibility,
            phase_scope=agent.use_when,
            max_steps=max(3, int(agent.budget.get("max_tool_calls", 3)) + 3),
            allowed_tools=agent.allowed_tools,
            forbidden_tools=agent.forbidden_tools,
            inputs=("work_order.json", "context-pack.json", "evidence-register.json"),
            outputs=("agent-result.json",),
            gates=agent.gates,
            permissions=agent.permissions,
            escalation_policy="return needs_user_input when permissions, context or runtime approval are insufficient",
            correction_policy="retry only inside max_steps and only using allowed tools with evidence",
            source="registry",
        )

    @property
    def contract_hash(self) -> str:
        return sha256_text(stable_json(self.to_dict()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_yaml(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"agent_id: {self.agent_id}",
            f"role: {self.role}",
            "phase_scope:",
            *[f"  - {item}" for item in self.phase_scope],
            f"max_steps: {self.max_steps}",
            "allowed_tools:",
            *[f"  - {item}" for item in self.allowed_tools],
            "forbidden_tools:",
            *[f"  - {item}" for item in self.forbidden_tools],
            "inputs:",
            *[f"  - {item}" for item in self.inputs],
            "outputs:",
            *[f"  - {item}" for item in self.outputs],
            "gates:",
            *[f"  - {item}" for item in self.gates],
            "permissions:",
            *[f"  {key}: {str(value).lower()}" for key, value in sorted(self.permissions.items())],
            f"escalation_policy: {self.escalation_policy}",
            f"correction_policy: {self.correction_policy}",
            f"contract_hash: {self.contract_hash}",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
