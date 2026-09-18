"""Offline schema validation of v2 data. No remote schema resolution."""
from functools import lru_cache
import json
from pathlib import Path


@lru_cache(maxsize=8)
def validator(name):
    if name not in {"project", "element", "verification-evidence", "migration-receipt"}:
        raise ValueError("Unknown local schema")
    from jsonschema import Draft202012Validator, FormatChecker
    raw = (Path(__file__).resolve().parents[1] / "schemas" / (name + "-2.0.schema.json")).read_text(encoding="utf-8")
    schema = json.loads(raw)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(name, value):
    from v2_contract import ContractError
    errors = list(validator(name).iter_errors(value))
    if errors:
        raise ContractError("Invalid " + name + " 2.0: " + "; ".join(str(list(e.path)) + ": " + e.message for e in errors[:8]))
