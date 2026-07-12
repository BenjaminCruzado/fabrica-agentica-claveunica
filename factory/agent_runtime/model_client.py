from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from typing import Any

from ..utils import read_json, stable_json


ACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "steps", "actions", "final_message"],
    "properties": {
        "status": {"type": "string", "enum": ["ok", "needs_user_input", "not_answerable", "error"]},
        "steps": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 12},
        "actions": {
            "type": "array",
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "tool_id", "args", "path", "content", "reason"],
                "properties": {
                    "action": {"type": "string", "enum": ["tool", "write_file", "patch_file", "finish", "needs_user_input"]},
                    "tool_id": {"type": "string"},
                    "args": {"type": "object", "additionalProperties": False, "properties": {}},
                    "path": {"type": "string"},
                    "content": {"type": "string", "maxLength": 6000},
                    "reason": {"type": "string", "maxLength": 800},
                },
            },
        },
        "final_message": {"type": "string", "maxLength": 1200},
    },
}


@dataclass(frozen=True)
class AgentAction:
    action: str
    tool_id: str
    args: dict[str, Any]
    reason: str
    path: str = ""
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelPlan:
    status: str
    steps: tuple[str, ...]
    adapter: str
    actions: tuple[AgentAction, ...] = ()
    final_message: str = ""
    response_id: str | None = None
    execute_tools: bool = False
    apply_writes: bool = False
    usage: dict[str, int] | None = None
    estimated_cost_usd: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "adapter": self.adapter,
            "steps": list(self.steps),
            "actions": [action.to_dict() for action in self.actions],
            "final_message": self.final_message,
            "response_id": self.response_id,
            "execute_tools": self.execute_tools,
            "apply_writes": self.apply_writes,
            "usage": self.usage or {},
            "estimated_cost_usd": self.estimated_cost_usd,
            "error": self.error,
        }


class ModelClient:
    """Local-first adapter boundary for LLM-backed agent planning.

    Secrets are never read from the repository. The local config can only name an
    environment variable that holds the API key.
    """

    def __init__(self, *, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir

    def plan(self, *, contract: dict[str, Any], context_pack: dict[str, Any], state: dict[str, Any]) -> ModelPlan:
        mode = state.get("execution_mode", "deterministic")
        if mode != "agentic":
            return self._deterministic_plan()

        config = self._load_config()
        if not config.get("enabled"):
            return self._fallback_plan("not_configured", "model-provider.local.json no existe o enabled=false")
        if config.get("provider") != "openai":
            return self._fallback_plan("unsupported_provider", "solo provider=openai esta soportado")
        api_key_env = str(config.get("api_key_env") or "OPENAI_API_KEY")
        api_key = self._read_api_key(api_key_env)
        if not api_key:
            return self._fallback_plan("missing_api_key", f"variable de entorno {api_key_env} no definida")

        attempts = max(1, int(config.get("max_model_retries") or 2) + 1)
        errors: list[str] = []
        base_tokens = int(config.get("max_output_tokens") or 2000)
        for attempt in range(attempts):
            attempt_config = dict(config)
            attempt_config["max_output_tokens"] = min(12000, base_tokens + (attempt * 3000))
            try:
                return self._openai_plan(contract=contract, context_pack=context_pack, state=state, config=attempt_config, api_key=api_key)
            except Exception as exc:
                errors.append(self._safe_error(exc))
        return self._fallback_plan("adapter_error", " | ".join(errors[-3:]))

    def _deterministic_plan(self) -> ModelPlan:
        return ModelPlan(
            status="deterministic_plan",
            adapter="local-deterministic",
            steps=(
                "load contract and context",
                "check tool policy and budget",
                "execute registered builder/reviewer function",
                "validate output gates",
                "write session trace",
            ),
        )

    def _fallback_plan(self, adapter: str, reason: str) -> ModelPlan:
        return ModelPlan(
            status="needs_adapter",
            adapter=adapter,
            steps=(
                "agentic mode requested",
                reason,
                "fallback to deterministic execution with full trace",
            ),
            final_message=reason,
            error=reason,
        )

    def _load_config(self) -> dict[str, Any]:
        if not self.project_dir:
            return {}
        path = self.project_dir / "secrets" / "model-provider.local.json"
        if not path.exists():
            return {}
        return read_json(path)

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

    def _openai_plan(
        self,
        *,
        contract: dict[str, Any],
        context_pack: dict[str, Any],
        state: dict[str, Any],
        config: dict[str, Any],
        api_key: str,
    ) -> ModelPlan:
        endpoint = str(config.get("endpoint") or "https://api.openai.com/v1/responses")
        model = str(config.get("model") or "gpt-5.5")
        max_steps = int(config.get("max_steps") or 8)
        timeout = max(5, int(config.get("timeout_ms") or 60000) / 1000)
        execute_tools = bool(config.get("execute_tools", False))
        apply_writes = bool(config.get("apply_model_writes", False))
        agent_input = self._bounded_input(contract=contract, context_pack=context_pack, state=state, max_steps=max_steps)
        prompt_text = stable_json(agent_input)
        preflight_cost = self._estimate_cost(model, {"input_tokens": max(1, len(prompt_text) // 4), "output_tokens": int(config.get("max_output_tokens") or 2000), "cached_tokens": 0, "reasoning_tokens": 0})
        max_cost = float(config.get("max_estimated_cost_usd") or 2.0)
        if preflight_cost > max_cost:
            return ModelPlan(
                status="needs_user_input",
                adapter="cost_guard",
                steps=("agentic call blocked before model request", f"estimated request cost {preflight_cost} exceeds local max {max_cost}"),
                final_message="cost guard blocked model request",
                estimated_cost_usd=preflight_cost,
            )
        payload = {
            "model": model,
            "max_output_tokens": int(config.get("max_output_tokens") or 2000),
            "input": [
                {
                    "role": "developer",
                    "content": (
                        "You are a bounded software-factory agent. Return only JSON that matches the schema. "
                        "Return a concise execution plan. When useful, write code only through small targeted "
                        "write_file or patch_file actions. Never emit a full application or large source tree "
                        "inside this JSON response; large app generation is handled by the factory builder "
                        "after your bounded plan. "
                        "Use file actions only for files inside app-generada or the current run artifacts. "
                        "For patch_file on existing files, prefer exact search/replace blocks formatted as "
                        "<<<<<<< SEARCH\\nold text\\n=======\\nnew text\\n>>>>>>> REPLACE. "
                        "Never request secrets, deployment, git pushes, cloud changes, shell-free commands, "
                        "or tools outside the contract. Do not expose requirements ids, traceability, validation "
                        "matrices, generator debug panels, or internal audit logs in frontend UI. Buttons must "
                        "produce observable domain state changes, not just generic activity logs. Keep generated "
                        "files focused and under the configured limits. Prefer a finish action when the "
                        "deterministic builder should materialize the approved plan."
                    ),
                },
                {"role": "user", "content": prompt_text},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "agent_action_plan",
                    "schema": ACTION_SCHEMA,
                    "strict": True,
                }
            },
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        parsed = self._parse_response_json(data)
        actions = tuple(self._coerce_action(item) for item in parsed.get("actions", [])[:max_steps])
        steps = tuple(str(item) for item in parsed.get("steps", [])[:max_steps]) or ("model returned structured plan",)
        usage = self._usage(data)
        return ModelPlan(
            status=str(parsed.get("status") or "ok"),
            adapter="openai-responses",
            steps=steps,
            actions=actions,
            final_message=str(parsed.get("final_message") or ""),
            response_id=data.get("id"),
            execute_tools=execute_tools,
            apply_writes=apply_writes,
            usage=usage,
            estimated_cost_usd=self._estimate_cost(model, usage),
        )

    def _bounded_input(self, *, contract: dict[str, Any], context_pack: dict[str, Any], state: dict[str, Any], max_steps: int) -> dict[str, Any]:
        safe_state = {
            "run_id": state.get("run_id"),
            "cycle_id": state.get("cycle_id"),
            "phase": state.get("phase"),
            "task_id": state.get("task_id"),
            "input_hash": state.get("input_hash"),
            "spec_hash": state.get("spec_hash"),
            "budget": state.get("budget"),
            "approval": state.get("approval"),
        }
        chunks = context_pack.get("chunks", [])
        run_artifacts = self._run_artifacts_for_model(state)
        return {
            "contract": contract,
            "state": safe_state,
            "context": {
                "query": context_pack.get("query"),
                "corpus_hash": context_pack.get("corpus_hash"),
                "chunks": chunks[:8],
                "run_artifacts": run_artifacts,
            },
            "instructions": {
                "max_steps": max_steps,
                "allowed_tools_only": True,
                "local_only": True,
                "no_github_push": True,
                "no_ec2_deploy": True,
                "file_actions_require_runtime_validation": True,
                "ai_code_writer_controlled": True,
                "write_code_via_actions_only": True,
                "large_app_generation_policy": "do_not_emit_full_app_in_model_json_return_bounded_plan_and_finish",
                "patch_file_format": "<<<<<<< SEARCH\\nold text\\n=======\\nnew text\\n>>>>>>> REPLACE",
                "frontend_internal_requirements_policy": "internal_only_never_render_requirement_ids_or_traceability",
                "button_policy": "domain_actions_must_change_ui_api_or_database_state_not_only_log_activity",
                "fallback_policy": "critical_agentic_agents_block_on_missing_api_or_invalid_model_plan",
                "allowed_write_roots": [
                    "app-generada",
                    f"project/runs/{state.get('run_id')}/ai-generated",
                    f"project/runs/{state.get('run_id')}/docs/generated",
                ],
            },
        }

    def _parse_response_json(self, data: dict[str, Any]) -> dict[str, Any]:
        text = data.get("output_text")
        if not text:
            parts: list[str] = []
            for output in data.get("output", []):
                for content in output.get("content", []):
                    if isinstance(content, dict) and content.get("text"):
                        parts.append(str(content["text"]))
            text = "".join(parts)
        parsed = self._loads_model_json(text or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("model response is not a JSON object")
        return parsed

    def _run_artifacts_for_model(self, state: dict[str, Any]) -> dict[str, Any]:
        if not self.project_dir:
            return {}
        run_id = str(state.get("run_id") or "")
        run_dir = self.project_dir / "runs" / run_id
        if not run_id or not run_dir.exists():
            return {}
        artifacts: dict[str, Any] = {}
        for name in (
            "work_order.json",
            "context-pack.json",
            "evidence-register.json",
            "tasks.md",
            "plan.md",
            "scope-validation.json",
            "domain-blueprint.json",
            "openapi.yaml",
            "coverage-report.json",
            "docker-validation.json",
            "docker-runtime-validation.json",
            "review-findings/app-review.json",
            "review-findings/ux-ui-product-review.json",
            "review-findings/software-architecture-review.json",
            "review-findings/product-owner-flow-review.json",
            "review-findings/qa-e2e-review.json",
            "ai-code-writer-ledger",
        ):
            path = run_dir / name
            if path.exists() and path.is_dir():
                files = sorted(item for item in path.glob("*.json") if item.is_file())[:5]
                artifacts[name] = {
                    "exists": True,
                    "type": "directory",
                    "files": [item.name for item in files],
                    "content_excerpt": "\n".join(item.read_text(encoding="utf-8-sig", errors="replace")[:3000] for item in files),
                }
                continue
            if not path.exists() or not path.is_file():
                artifacts[name] = {"exists": False}
                continue
            content = path.read_text(encoding="utf-8-sig", errors="replace")
            artifacts[name] = {
                "exists": True,
                "bytes": len(content.encode("utf-8")),
                "content_excerpt": content[:12000],
                "truncated": len(content) > 12000,
            }
        return artifacts

    def _loads_model_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise

    def _coerce_action(self, item: Any) -> AgentAction:
        if not isinstance(item, dict):
            return AgentAction("finish", "", {}, "invalid action ignored")
        args = item.get("args")
        return AgentAction(
            action=str(item.get("action") or "finish"),
            tool_id=str(item.get("tool_id") or ""),
            args=args if isinstance(args, dict) else {},
            reason=str(item.get("reason") or ""),
            path=str(item.get("path") or ""),
            content=str(item.get("content") or ""),
        )

    def _usage(self, data: dict[str, Any]) -> dict[str, int]:
        usage = data.get("usage") or {}
        return {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "cached_tokens": int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0),
            "reasoning_tokens": int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0),
        }

    def _estimate_cost(self, model: str, usage: dict[str, int]) -> float:
        pricing = {
            "gpt-5.5": {"input": 5.0, "cached": 0.5, "output": 30.0},
            "gpt-5.4": {"input": 2.5, "cached": 0.25, "output": 15.0},
            "gpt-5.4-mini": {"input": 0.75, "cached": 0.075, "output": 4.5},
            "gpt-5.4-nano": {"input": 0.2, "cached": 0.02, "output": 1.25},
        }
        key = next((name for name in pricing if model.startswith(name)), "gpt-5.5")
        rates = pricing[key]
        cached = usage.get("cached_tokens", 0)
        input_tokens = max(0, usage.get("input_tokens", 0) - cached)
        output_tokens = usage.get("output_tokens", 0)
        return round(((input_tokens * rates["input"]) + (cached * rates["cached"]) + (output_tokens * rates["output"])) / 1_000_000, 6)

    def _safe_error(self, exc: Exception) -> str:
        if isinstance(exc, urllib.error.HTTPError):
            return f"openai http error {exc.code}"
        if isinstance(exc, urllib.error.URLError):
            return "openai connection error"
        message = str(exc).strip()
        if message:
            return f"{exc.__class__.__name__}: {message[:240]}"
        return exc.__class__.__name__
