from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

from ..policy import PolicyEngine
from ..registry import AgentSpec, ToolSpec
from ..utils import sha256_text, stable_json


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_id: str
    status: str
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    duration_ms: int
    output_hash: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolExecutor:
    def __init__(self, *, tools: dict[str, ToolSpec], policy: PolicyEngine, workspace: Path) -> None:
        self.tools = tools
        self.policy = policy
        self.workspace = workspace

    def preflight(self, agent: AgentSpec, tool_id: str, approval: dict[str, Any]) -> ToolExecutionResult:
        decision = self.policy.check_tool(agent, tool_id, approval)
        command = self._command_for(tool_id)
        if decision.status != "complete":
            return self._result(tool_id, decision.status, command, None, "", "", 0, decision.message)
        executable = command[0] if command else ""
        if executable and shutil.which(executable) is None:
            return self._result(tool_id, "warning", command, None, "", "", 0, f"{executable} no disponible")
        return self._result(tool_id, "complete", command, None, "", "", 0, "tool preflight ok")

    def execute(self, agent: AgentSpec, tool_id: str, approval: dict[str, Any], cwd: Path | None = None) -> ToolExecutionResult:
        preflight = self.preflight(agent, tool_id, approval)
        if preflight.status != "complete":
            return preflight
        command = preflight.command
        if not command:
            return self._result(tool_id, "complete", command, None, "", "", 0, "logical tool has no command")
        started = time.perf_counter()
        proc = subprocess.run(command, cwd=cwd or self.workspace, text=True, capture_output=True, timeout=self.tools[tool_id].timeout_ms / 1000)
        duration_ms = int((time.perf_counter() - started) * 1000)
        status = "complete" if proc.returncode == 0 else "error"
        return self._result(tool_id, status, command, proc.returncode, proc.stdout, proc.stderr, duration_ms, "")

    def _command_for(self, tool_id: str) -> tuple[str, ...]:
        if tool_id == "tool.test.pytest":
            return ("pytest",)
        if tool_id in {"tool.test.vitest", "tool.lint.eslint", "tool.security.npm_audit"}:
            return ("npm",)
        if tool_id == "tool.typecheck.tsc":
            return ("npm",)
        if tool_id == "tool.test.playwright":
            return ("npx", "playwright", "test")
        if tool_id == "tool.test.maven":
            return ("mvn", "test")
        if tool_id == "tool.docker.compose":
            return ("docker", "compose", "up", "-d", "--build")
        if tool_id == "tool.runtime.healthcheck":
            return ("curl", "-fsS", "http://localhost:8080/api/v1/health")
        if tool_id == "tool.api.openapi.validate":
            return ()
        if tool_id == "tool.sql.parse":
            return ()
        if tool_id.startswith("tool.files.") or tool_id.startswith("tool.cache.") or tool_id.startswith("tool.index."):
            return ()
        spec = self.tools.get(tool_id)
        if spec and spec.available_command:
            return (spec.available_command,)
        return ()

    def _result(
        self,
        tool_id: str,
        status: str,
        command: tuple[str, ...],
        returncode: int | None,
        stdout: str,
        stderr: str,
        duration_ms: int,
        reason: str,
    ) -> ToolExecutionResult:
        payload = {
            "tool_id": tool_id,
            "status": status,
            "command": command,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "reason": reason,
        }
        return ToolExecutionResult(tool_id, status, command, returncode, stdout, stderr, duration_ms, sha256_text(stable_json(payload)), reason)
