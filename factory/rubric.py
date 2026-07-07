from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import read_json, write_json


RUBRIC_MINIMUMS: dict[str, int] = {
    "use_cases": 10,
    "features_or_flows": 30,
    "tables": 40,
    "api_endpoints": 40,
    "screens": 30,
    "business_rules": 60,
    "validations_checks": 100,
}


@dataclass(frozen=True)
class RubricScopeResult:
    status: str
    counts: dict[str, int]
    missing: dict[str, int]


def validate_scope_inventory(path: Path) -> RubricScopeResult:
    if not path.exists():
        return RubricScopeResult(
            status="error",
            counts={key: 0 for key in RUBRIC_MINIMUMS},
            missing=dict(RUBRIC_MINIMUMS),
        )

    payload = read_json(path)
    counts = {key: int(payload.get("counts", {}).get(key, 0)) for key in RUBRIC_MINIMUMS}
    missing = {key: minimum - counts[key] for key, minimum in RUBRIC_MINIMUMS.items() if counts[key] < minimum}
    return RubricScopeResult(status="complete" if not missing else "error", counts=counts, missing=missing)


def write_scope_validation(run_dir: Path) -> dict[str, Any]:
    result = validate_scope_inventory(run_dir / "scope-inventory.json")
    payload = {
        "status": result.status,
        "minimums": RUBRIC_MINIMUMS,
        "counts": result.counts,
        "missing": result.missing,
    }
    write_json(run_dir / "scope-validation.json", payload)
    return payload
