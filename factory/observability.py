from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import MODEL_SNAPSHOT
from .utils import append_jsonl, read_json, stable_json, utc_now, write_json


class Observability:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    def event(self, **payload: Any) -> None:
        base = {
            "ts": utc_now(),
            "run_id": payload.get("run_id", "RUN-TBD"),
            "cycle_id": payload.get("cycle_id", "CYC-TBD"),
            "event": payload.get("event", "event"),
            "status": payload.get("status", "complete"),
        }
        base.update(payload)
        append_jsonl(self.run_dir / "log.jsonl", base)

    def agent_event(self, agent_id: str, payload: dict[str, Any]) -> None:
        append_jsonl(self.run_dir / "agent-logs" / f"{agent_id}.jsonl", {"ts": utc_now(), **payload})

    def tool_event(self, tool_id: str, payload: dict[str, Any]) -> None:
        append_jsonl(self.run_dir / "tool-logs" / f"{tool_id.replace('/', '_')}.jsonl", {"ts": utc_now(), **payload})

    def add_billing_phase(self, state: dict[str, Any], agent_id: str, *, output_tokens: int, tool_calls: int, latency_ms: int) -> None:
        path = self.run_dir / "billing-ledger.json"
        if path.exists():
            ledger = read_json(path)
        else:
            ledger = {
                "run_id": state["run_id"],
                "currency": "USD",
                "pricing": "TBD-no-pricing-config",
                "phases": [],
                "totals": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "reasoning_tokens": 0,
                    "tool_calls": 0,
                    "estimated_cost": 0,
                },
            }
        input_tokens = max(1, len(stable_json(state)) // 4)
        phase = {
            "phase": state["phase"],
            "agent_id": agent_id,
            "model": MODEL_SNAPSHOT,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "tool_calls": tool_calls,
            "latency_ms": latency_ms,
            "estimated_cost": 0,
        }
        ledger["phases"].append(phase)
        totals = ledger["totals"]
        totals["input_tokens"] += phase["input_tokens"]
        totals["output_tokens"] += phase["output_tokens"]
        totals["cached_tokens"] += phase["cached_tokens"]
        totals["reasoning_tokens"] += phase["reasoning_tokens"]
        totals["tool_calls"] += phase["tool_calls"]
        totals["estimated_cost"] += phase["estimated_cost"]
        write_json(path, ledger)
