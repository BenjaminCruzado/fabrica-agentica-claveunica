from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils import utc_now


@dataclass
class AgentSession:
    run_id: str
    cycle_id: str
    agent_id: str
    execution_mode: str
    contract_hash: str
    started_at: str = field(default_factory=utc_now)
    steps: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def add_step(self, kind: str, status: str, detail: str, **extra: Any) -> None:
        self.steps.append(
            {
                "ts": utc_now(),
                "kind": kind,
                "status": status,
                "detail": detail,
                **extra,
            }
        )

    def add_finding(self, severity: str, area: str, message: str, **extra: Any) -> None:
        self.findings.append(
            {
                "ts": utc_now(),
                "severity": severity,
                "area": area,
                "message": message,
                **extra,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "cycle_id": self.cycle_id,
            "agent_id": self.agent_id,
            "execution_mode": self.execution_mode,
            "contract_hash": self.contract_hash,
            "started_at": self.started_at,
            "steps": self.steps,
            "findings": self.findings,
        }
