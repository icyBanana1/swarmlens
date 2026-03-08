from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REQUIRED = {
    "accounts": ["account_id", "username"],
    "posts": ["post_id", "account_id", "timestamp", "text"],
    "interactions": ["source_account_id", "target_account_id", "interaction_type", "timestamp"],
}


def _read_table(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "rows", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        raise ValueError(f"Unsupported JSON structure in {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_case(case_dir: str | Path) -> dict[str, list[dict[str, Any]]]:
    case_dir = Path(case_dir)
    resolved = {}
    for name in ("accounts", "posts", "interactions"):
        for ext in (".csv", ".json"):
            candidate = case_dir / f"{name}{ext}"
            if candidate.exists():
                resolved[name] = _read_table(candidate)
                break
        else:
            resolved[name] = []
    return resolved


def validate_case(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    counts = {k: len(v) for k, v in data.items()}
    for section, required_fields in REQUIRED.items():
        rows = data.get(section, [])
        if rows:
            missing = [field for field in required_fields if field not in rows[0]]
            if missing:
                issues.append(f"{section} missing required fields: {', '.join(missing)}")
        elif section != "interactions":
            warnings.append(f"{section} is empty")
    account_ids = [str(r.get("account_id", "")).strip() for r in data.get("accounts", [])]
    unique = {x for x in account_ids if x}
    if len(unique) != len([x for x in account_ids if x]):
        warnings.append("duplicate account_id values detected")
    if unique:
        unknown_post_refs = sorted({str(r.get("account_id", "")).strip() for r in data.get("posts", []) if str(r.get("account_id", "")).strip() not in unique})
        if unknown_post_refs:
            issues.append(f"posts reference unknown account_id values: {', '.join(unknown_post_refs[:10])}")
    return {"ok": not issues, "issues": issues, "warnings": warnings, "counts": counts}
