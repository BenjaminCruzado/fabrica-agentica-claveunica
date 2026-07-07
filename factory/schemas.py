from __future__ import annotations

from typing import Any

from .constants import APPROVAL_REQUIRED_FOR, FINAL_STATUSES, SDD_PHASES


class SchemaError(ValueError):
    pass


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def validate_strict(schema: dict[str, Any], data: Any, path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type and _type_name(data) != expected_type:
        if not (expected_type == "number" and _type_name(data) == "integer"):
            raise SchemaError(f"{path}: expected {expected_type}, got {_type_name(data)}")

    if "enum" in schema and data not in schema["enum"]:
        raise SchemaError(f"{path}: invalid enum value {data!r}")

    if expected_type == "object":
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            extra = set(data) - allowed
            if extra:
                raise SchemaError(f"{path}: additional properties {sorted(extra)}")
        for key in schema.get("required", []):
            if key not in data:
                raise SchemaError(f"{path}: missing required property {key}")
        for key, subschema in schema.get("properties", {}).items():
            if key in data:
                validate_strict(subschema, data[key], f"{path}.{key}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(data):
                validate_strict(item_schema, item, f"{path}[{index}]")


WORK_ORDER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["work_order_id", "objective", "work_type", "scope", "inputs", "constraints", "expected_outputs", "approval_required_for"],
    "properties": {
        "work_order_id": {"type": "string"},
        "objective": {"type": "string"},
        "work_type": {"type": "string", "enum": ["feature", "bugfix", "refactor", "migration", "doc", "test", "security", "performance", "incident", "factory_bootstrap"]},
        "scope": {
            "type": "object",
            "additionalProperties": False,
            "required": ["include", "exclude"],
            "properties": {
                "include": {"type": "array", "items": {"type": "string"}},
                "exclude": {"type": "array", "items": {"type": "string"}},
            },
        },
        "inputs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["source_id", "type", "authorized", "trust"],
                "properties": {
                    "source_id": {"type": "string"},
                    "type": {"type": "string", "enum": ["brief", "repo", "doc", "ticket", "log", "db", "image", "memory", "other"]},
                    "path": {"type": "string"},
                    "authorized": {"type": "boolean"},
                    "hash": {"type": "string"},
                    "trust": {"type": "string", "enum": ["trusted", "semi_trusted", "untrusted"]},
                },
            },
        },
        "constraints": {
            "type": "object",
            "additionalProperties": False,
            "required": ["no_web", "dry_run", "sandbox_required", "max_retries", "risk", "max_cost_usd", "max_latency_ms"],
            "properties": {
                "no_web": {"type": "boolean"},
                "dry_run": {"type": "boolean"},
                "sandbox_required": {"type": "boolean"},
                "max_retries": {"type": "integer"},
                "risk": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "max_cost_usd": {"type": "number"},
                "max_latency_ms": {"type": "integer"},
            },
        },
        "expected_outputs": {"type": "array", "items": {"type": "string"}},
        "approval_required_for": {"type": "array", "items": {"type": "string", "enum": list(APPROVAL_REQUIRED_FOR)}},
    },
}


CYCLE_STATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["run_id", "cycle_id", "task_id", "phase", "status", "input_hash", "spec_hash", "policy_version", "tool_registry_version", "memory_version", "evidence", "outputs", "issues", "budget", "approval"],
    "properties": {
        "run_id": {"type": "string"},
        "cycle_id": {"type": "string"},
        "task_id": {"type": "string"},
        "phase": {"type": "string", "enum": list(SDD_PHASES)},
        "status": {"type": "string", "enum": list(FINAL_STATUSES)},
        "input_hash": {"type": "string"},
        "spec_hash": {"type": "string"},
        "policy_version": {"type": "string"},
        "tool_registry_version": {"type": "string"},
        "memory_version": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "outputs": {"type": "object"},
        "issues": {"type": "array"},
        "budget": {
            "type": "object",
            "additionalProperties": False,
            "required": ["max_input_tokens", "max_output_tokens", "max_cost_usd", "max_latency_ms", "max_tool_calls", "used_input_tokens", "used_output_tokens", "cached_tokens", "reasoning_tokens", "estimated_cost_usd", "tool_calls"],
            "properties": {
                "max_input_tokens": {"type": "integer"},
                "max_output_tokens": {"type": "integer"},
                "max_cost_usd": {"type": "number"},
                "max_latency_ms": {"type": "integer"},
                "max_tool_calls": {"type": "integer"},
                "used_input_tokens": {"type": "integer"},
                "used_output_tokens": {"type": "integer"},
                "cached_tokens": {"type": "integer"},
                "reasoning_tokens": {"type": "integer"},
                "estimated_cost_usd": {"type": "number"},
                "tool_calls": {"type": "integer"},
            },
        },
        "approval": {
            "type": "object",
            "additionalProperties": False,
            "required": ["required", "approved", "approval_id"],
            "properties": {
                "required": {"type": "boolean"},
                "approved": {"type": "boolean"},
                "approval_id": {"type": "string"},
            },
        },
    },
}


AGENT_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["run_id", "cycle_id", "agent_id", "status", "output", "validation", "logs", "budget"],
    "properties": {
        "run_id": {"type": "string"},
        "cycle_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "status": {"type": "string", "enum": list(FINAL_STATUSES)},
        "output": {"type": "object"},
        "validation": {"type": "object"},
        "logs": {"type": "object"},
        "budget": {"type": "object"},
    },
}
