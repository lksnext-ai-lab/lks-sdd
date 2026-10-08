"""Local-only schema validation for the v3 contract."""
from functools import lru_cache
import json
from pathlib import Path
from v2_contract import ContractError


@lru_cache(maxsize=8)
def validator(name, version="3.0"):
    if name not in {"project", "element", "collaboration"} or version not in {"3.0", "3.1"}: raise ContractError("Schema desconocido")
    from jsonschema import Draft202012Validator, FormatChecker
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / (name + "-" + version + ".schema.json")).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(name, value, version="3.0"):
    errors = list(validator(name, version).iter_errors(value))
    if errors: raise ContractError("Contrato " + version + " inválido: " + "; ".join(e.message for e in errors[:8]))
