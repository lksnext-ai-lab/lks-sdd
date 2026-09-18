#!/usr/bin/env python3
"""Run the reproducible LKS-SDD M4 quality and regression harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

# The harness must not make its own clean checkout dirty before preflight, and
# every child validator/test inherits the same no-bytecode rule.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from quality_execution import (
    load_performance_policy,
    performance_assessment,
    run_managed_command,
    runner_fingerprint,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
QUALITY_ROOT = PLUGIN_ROOT / "quality"
CATALOG_PATH = QUALITY_ROOT / "catalog.json"
CORPUS_PATH = QUALITY_ROOT / "corpora" / "activation.json"
DEFINITION_CORPUS_PATH = QUALITY_ROOT / "corpora" / "definition-v2.0.0.json"
FIXTURE_MANIFEST_PATH = QUALITY_ROOT / "fixture-manifest.json"
DEFAULT_BASELINE_PATH = QUALITY_ROOT / "baselines" / "v0.17.0.json"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PILOT_SUMMARY_SCHEMA_PATH = PLUGIN_ROOT / "schemas" / "pilot-summary.schema.json"
RELEASE_APPROVAL_SCHEMA_PATH = (
    PLUGIN_ROOT / "schemas" / "release-approval.schema.json"
)
# This is only an emergency ceiling for the child dispatcher.  Each selected
# suite applies its own blocking performance budget from
# quality/performance-policy.json and returns JSON evidence before this ceiling
# is relevant.  Keeping the two roles separate avoids an outer timeout
# suppressing the child's useful failure diagnostics.
UNIT_TEST_TIMEOUT_SECONDS = 900
ALLOWED_SKILLS = {
    "lks-sdd-help",
    "lks-sdd-define",
    "lks-sdd-adopt-existing",
    "lks-sdd-assess-readiness",
    "lks-sdd-implement",
    "lks-sdd-verify",
}
SCORE_KEYS = {
    "correctness",
    "completeness",
    "clarity",
    "verifiability",
    "traceability",
    "proportionality",
    "operational_utility",
    "audience_fit",
    "information_separation",
    "information_protection",
}
METRIC_DIRECTIONS = {
    "activation_precision": "higher",
    "activation_recall": "higher",
    "activation_samples": "neutral",
    "automated_catalog_cases": "neutral",
    "automated_catalog_cases_failed": "lower",
    "automated_catalog_cases_incomplete": "lower",
    "automated_catalog_cases_passed": "higher",
    "automated_eval_cases": "neutral",
    "automated_eval_pass_rate": "higher",
    "critical_failures": "lower",
    "document_review_average": "higher",
    "document_review_minimum": "higher",
    "document_review_samples": "neutral",
    "profile_complete_gate": "higher",
    "profile_structure_gate": "higher",
    "routing_accuracy": "higher",
    "unit_tests_executed": "neutral",
    "unit_tests_failed": "lower",
    "unit_tests_passed": "higher",
    "unit_tests_skipped": "lower",
    "unit_tests_total": "neutral",
}
_SCHEMA_ANNOTATION_KEYS = {"$id", "$schema", "description", "title"}
_SCHEMA_VALIDATION_KEYS = {
    "additionalProperties",
    "const",
    "enum",
    "items",
    "minimum",
    "properties",
    "required",
    "type",
    "uniqueItems",
}


class HarnessError(Exception):
    """Expected, actionable harness failure."""


def _definition_corpus_matches_plugin_line(
    corpus_version: Any, plugin_version: Any
) -> bool:
    """Allow compatible patches and the explicit stable lines retaining the corpus."""
    pattern = re.compile(
        r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
    )
    if not isinstance(corpus_version, str) or not isinstance(plugin_version, str):
        return False
    corpus_match = pattern.fullmatch(corpus_version)
    plugin_match = pattern.fullmatch(plugin_version)
    if corpus_match is None or plugin_match is None:
        return False
    corpus_parts = tuple(int(part) for part in corpus_match.groups())
    plugin_parts = tuple(int(part) for part in plugin_match.groups())
    same_compatible_line = (
        corpus_parts[:2] == plugin_parts[:2]
        and corpus_parts[2] <= plugin_parts[2]
    )
    stable_lines_retaining_definition_contract = (
        plugin_parts[:2] in {(1, 0), (1, 1)} and corpus_parts == (0, 18, 0)
    )
    return same_compatible_line or stable_lines_retaining_definition_contract


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"JSON ilegible {path}: {exc}") from exc


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HarnessError(f"{label} debe ser un objeto JSON.")
    return value


def _matches_json_type(value: Any, expected: str) -> bool:
    checks = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: type(item) is bool,
        "integer": lambda item: isinstance(item, int) and type(item) is not bool,
        "null": lambda item: item is None,
        "number": lambda item: (
            isinstance(item, (int, float)) and type(item) is not bool
        ),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
    }
    return expected in checks and checks[expected](value)


def _assert_supported_json_schema(
    schema: dict[str, Any], location: str = "$schema"
) -> None:
    """Fail closed if the pilot schema grows beyond the implemented vocabulary."""
    unsupported = sorted(
        set(schema) - _SCHEMA_ANNOTATION_KEYS - _SCHEMA_VALIDATION_KEYS
    )
    if unsupported:
        raise HarnessError(
            f"{location}: keywords JSON Schema no soportadas: {unsupported}"
        )
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise HarnessError(f"{location}.properties debe ser un objeto.")
    for name, child in properties.items():
        if not isinstance(child, dict):
            raise HarnessError(f"{location}.properties.{name} debe ser un schema.")
        _assert_supported_json_schema(child, f"{location}.properties.{name}")
    items = schema.get("items")
    if items is not None:
        if not isinstance(items, dict):
            raise HarnessError(f"{location}.items debe ser un schema.")
        _assert_supported_json_schema(items, f"{location}.items")


def _validate_json_schema(
    value: Any, schema: dict[str, Any], location: str = "$"
) -> list[str]:
    """Validate every validation keyword used by pilot-summary.schema.json."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not all(isinstance(option, str) for option in options):
            return [f"{location}: declaración de tipo inválida en el schema."]
        if not any(_matches_json_type(value, option) for option in options):
            return [f"{location}: tipo inválido; se esperaba {options}."]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: debe ser {schema['const']!r}.")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: valor {value!r} fuera del catálogo permitido.")
    if (
        "minimum" in schema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and value < schema["minimum"]
    ):
        errors.append(f"{location}: debe ser mayor o igual que {schema['minimum']}.")
    if isinstance(value, list):
        if schema.get("uniqueItems") is True:
            canonical_items = [
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(canonical_items) != len(set(canonical_items)):
                errors.append(f"{location}: contiene elementos duplicados.")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _validate_json_schema(item, item_schema, f"{location}[{index}]")
                )
    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list):
            errors.append(f"{location}: required inválido en el schema.")
            required = []
        for key in required:
            if key not in value:
                errors.append(f"{location}: falta la propiedad obligatoria {key!r}.")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{location}: propiedad no admitida {key!r}.")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    _validate_json_schema(value[key], child_schema, f"{location}.{key}")
                )
    return errors


def validate_pilot_summary(
    value: Any, schema_value: Any | None = None
) -> dict[str, Any]:
    summary = _require_object(value, "El resumen de piloto")
    schema = _require_object(
        schema_value
        if schema_value is not None
        else _load_json(PILOT_SUMMARY_SCHEMA_PATH),
        "El schema de resumen de piloto",
    )
    _assert_supported_json_schema(schema)
    errors = _validate_json_schema(summary, schema)
    if errors:
        raise HarnessError(
            "El resumen de piloto no cumple schemas/pilot-summary.schema.json: "
            + " | ".join(errors)
        )
    return summary


def validate_release_approval(
    value: Any,
    plugin_version: str,
    schema_value: Any | None = None,
) -> dict[str, Any]:
    """Validate a privacy-safe stable-release decision by the project owner."""
    approval = _require_object(value, "La aprobación de release")
    schema = _require_object(
        schema_value
        if schema_value is not None
        else _load_json(RELEASE_APPROVAL_SCHEMA_PATH),
        "El schema de aprobación de release",
    )
    _assert_supported_json_schema(schema)
    errors = _validate_json_schema(approval, schema)
    if errors:
        raise HarnessError(
            "La aprobación no cumple schemas/release-approval.schema.json: "
            + " | ".join(errors)
        )
    if approval.get("release_version") != plugin_version:
        raise HarnessError(
            "La aprobación del responsable no corresponde a la versión evaluada."
        )
    decision = approval["decision"]
    decided_on = str(decision.get("decided_on"))
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", decided_on):
        raise HarnessError("decision.decided_on debe usar YYYY-MM-DD.")
    try:
        date.fromisoformat(decided_on)
    except ValueError as exc:
        raise HarnessError("decision.decided_on no es una fecha válida.") from exc
    if not decision.get("rationale", "").strip():
        raise HarnessError("La decisión debe conservar una justificación no vacía.")
    if not approval.get("basis"):
        raise HarnessError("La aprobación debe declarar al menos una base de decisión.")
    if "project-owner-acceptance" not in approval["basis"]:
        raise HarnessError(
            "La aprobación stable debe declarar project-owner-acceptance."
        )
    status = decision.get("status")
    blockers = decision.get("blocking_findings", [])
    if status == "approved" and blockers:
        raise HarnessError(
            "Una release aprobada no puede conservar hallazgos bloqueantes."
        )
    return approval


def validate_catalog(value: Any) -> dict[str, Any]:
    catalog = _require_object(value, "El catálogo")
    if catalog.get("schema_version") != "1.0":
        raise HarnessError("El catálogo debe usar schema_version 1.0.")
    cases = catalog.get("cases")
    thresholds = catalog.get("thresholds")
    channels = catalog.get("channels")
    if not isinstance(cases, list) or not cases:
        raise HarnessError("El catálogo debe declarar casos.")
    if not isinstance(thresholds, dict) or not thresholds:
        raise HarnessError("El catálogo debe declarar umbrales calculables.")
    if not isinstance(channels, dict) or set(channels) != {"candidate", "stable"}:
        raise HarnessError("El catálogo debe declarar los canales candidate y stable.")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso del catálogo debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"FX-[0-9]{2}", case_id):
            raise HarnessError(f"ID de caso inválido: {case_id!r}")
        if case_id in ids:
            raise HarnessError(f"Caso duplicado: {case_id}")
        ids.add(case_id)
        if case.get("mode") not in {"automated", "semantic", "human", "pilot"}:
            raise HarnessError(f"Modo inválido en {case_id}.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
        evidence = case.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str)
            and re.fullmatch(r"(?:eval|test|profile):[A-Za-z0-9._-]+", item)
            for item in evidence
        ):
            raise HarnessError(f"Evidencia inválida en {case_id}.")
        if case.get("mode") == "automated" and not evidence:
            raise HarnessError(f"{case_id} es automatizado pero no declara evidencia.")
    expected = {f"FX-{index:02d}" for index in range(1, 20)}
    if ids != expected:
        raise HarnessError(
            f"El catálogo debe cubrir FX-01 a FX-19; diferencia: {sorted(ids ^ expected)}"
        )
    fx01 = next(case for case in cases if case["id"] == "FX-01")
    if fx01.get("mode") != "semantic" or fx01.get("evidence") != []:
        raise HarnessError(
            "FX-01 debe ser semántico y permanecer sin evidencia hasta una conversación controlada."
        )
    extension_cases = catalog.get("extension_cases")
    if not isinstance(extension_cases, list) or not extension_cases:
        raise HarnessError("El catálogo debe declarar casos de extensión versionados.")
    extension_ids: set[str] = set()
    for case in extension_cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso de extensión debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"FX-[0-9]{2}", case_id):
            raise HarnessError(f"ID de caso de extensión inválido: {case_id!r}")
        if case_id in ids or case_id in extension_ids:
            raise HarnessError(f"Caso de extensión duplicado: {case_id}")
        extension_ids.add(case_id)
        if case.get("mode") not in {"automated", "semantic", "human", "pilot"}:
            raise HarnessError(f"Modo inválido en {case_id}.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
        evidence = case.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str)
            and re.fullmatch(r"(?:eval|test|profile):[A-Za-z0-9._-]+", item)
            for item in evidence
        ):
            raise HarnessError(f"Evidencia inválida en {case_id}.")
        if case.get("mode") == "automated" and not evidence:
            raise HarnessError(f"{case_id} es automatizado pero no declara evidencia.")
        if case.get("mode") in {"semantic", "human"} and evidence:
            raise HarnessError(
                f"{case_id} no puede declarar evidencia antes de su ejecución controlada."
            )
    if extension_ids != {f"FX-{index:02d}" for index in range(20, 70)}:
        raise HarnessError("Las extensiones vigentes deben cubrir exactamente FX-20 a FX-69.")
    if "definition-conversation" not in channels["candidate"].get("optional", []):
        raise HarnessError(
            "Candidate debe mostrar definition-conversation como evidencia opcional."
        )
    known_channels = {
        "automated",
        "fixture-integrity",
        "profile-complete",
        "regression",
        "definition-conversation",
        "activation",
        "document-review",
        "pilot",
        "release-approval",
    }
    for channel_name, contract in channels.items():
        if not isinstance(contract, dict) or set(contract) != {"required", "optional"}:
            raise HarnessError(
                f"El canal {channel_name} debe declarar required y optional."
            )
        required = contract["required"]
        optional = contract["optional"]
        if (
            not isinstance(required, list)
            or not isinstance(optional, list)
            or len(required) != len(set(required))
            or len(optional) != len(set(optional))
            or set(required) & set(optional)
            or (set(required) | set(optional)) != known_channels
        ):
            raise HarnessError(
                f"El inventario de canales {channel_name} es inválido o incompleto."
            )
    if "release-approval" not in channels["stable"]["required"]:
        raise HarnessError(
            "Stable debe exigir la aprobación durable del responsable del proyecto."
        )
    for detailed_channel in (
        "definition-conversation",
        "activation",
        "document-review",
        "pilot",
    ):
        if detailed_channel not in channels["stable"]["optional"]:
            raise HarnessError(
                "Stable debe conservar los canales humanos detallados como "
                f"evidencia visible opcional: falta {detailed_channel}."
            )
    for name, threshold in thresholds.items():
        if not isinstance(threshold, dict):
            raise HarnessError(f"Umbral inválido: {name}")
        if threshold.get("direction") not in {"higher", "lower"}:
            raise HarnessError(f"Dirección de umbral inválida: {name}")
        if not isinstance(threshold.get("target"), (int, float)):
            raise HarnessError(f"Target de umbral inválido: {name}")
    return catalog


def validate_corpus(value: Any) -> dict[str, Any]:
    corpus = _require_object(value, "El corpus")
    if corpus.get("schema_version") != "1.0":
        raise HarnessError("El corpus debe usar schema_version 1.0.")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise HarnessError("El corpus de activación debe contener al menos diez casos.")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada entrada del corpus debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"ACT-[0-9]{3}", case_id):
            raise HarnessError(f"ID de activación inválido: {case_id!r}")
        if case_id in ids:
            raise HarnessError(f"Caso de activación duplicado: {case_id}")
        ids.add(case_id)
        expected = case.get("expected_skill")
        if expected is not None and expected not in ALLOWED_SKILLS:
            raise HarnessError(f"Skill esperada inválida en {case_id}: {expected!r}")
        if not isinstance(case.get("text"), str) or not case["text"].strip():
            raise HarnessError(f"Texto vacío en {case_id}.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
    return corpus


def validate_definition_corpus(value: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    corpus = _require_object(value, "El corpus de definición")
    if corpus.get("schema_version") != "1.0":
        raise HarnessError("El corpus de definición debe usar schema_version 1.0.")
    if corpus.get("execution_status") != "not-run" or corpus.get("evidence") != []:
        raise HarnessError(
            "El corpus de definición debe permanecer not-run y sin evidencia hasta una ejecución controlada."
        )
    cases = corpus.get("cases")
    if not isinstance(cases, list):
        raise HarnessError("El corpus de definición debe declarar casos.")
    corpus_version = corpus.get("plugin_version")
    version_match = re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
        corpus_version if isinstance(corpus_version, str) else "",
    )
    if version_match is None:
        raise HarnessError("El corpus de definición no declara una versión válida.")
    expected_ids = {"FX-01", "FX-20", "FX-21"}
    if tuple(int(part) for part in version_match.groups()[:2]) >= (0, 10):
        expected_ids.update(
            case["id"]
            for case in catalog["extension_cases"]
            if case.get("mode") in {"semantic", "human"}
            and tuple(int(part) for part in case.get("introduced_in", "0.0.0").split(".")) <= tuple(int(part) for part in version_match.groups())
        )
    ids: set[str] = set()
    allowed_dimensions = {
        "premise_control",
        "question_relevance",
        "coverage_clarity",
        "interaction_completeness",
        "visual_traceability",
        "human_validation",
        "information_protection",
        "tracking_authority",
        "degraded_mode_clarity",
        "milestone_experience",
    }
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso de definición debe ser un objeto.")
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or case_id in ids
            or case_id not in expected_ids
        ):
            raise HarnessError(f"Caso de definición inválido o duplicado: {case_id!r}")
        ids.add(case_id)
        if not isinstance(case.get("input"), str) or not case["input"].strip():
            raise HarnessError(f"{case_id} debe declarar una entrada sintética.")
        for field in ("expected", "forbidden", "review_dimensions"):
            items = case.get(field)
            if not isinstance(items, list) or not items:
                raise HarnessError(f"{case_id} debe declarar {field}.")
        dimensions = set(case["review_dimensions"])
        if not dimensions.issubset(allowed_dimensions):
            raise HarnessError(
                f"{case_id} contiene dimensiones de revisión desconocidas."
            )
    if ids != expected_ids:
        raise HarnessError(
            f"El corpus de definición no coincide con el catálogo: {sorted(ids ^ expected_ids)}"
        )
    evaluation = corpus.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation.get("required_review") != [
        "semantic",
        "human",
    ]:
        raise HarnessError(
            "El corpus de definición debe exigir revisión semántica y humana."
        )
    return corpus


def evaluate_definition_conversation(corpus: dict[str, Any]) -> dict[str, Any]:
    if corpus.get("execution_status") != "not-run" or corpus.get("evidence") != []:
        raise HarnessError(
            "No existe todavía un contrato de observaciones ejecutadas para el canal de definición."
        )
    return {
        "status": "not-run",
        "observed": 0,
        "total": len(corpus["cases"]),
        "corpus_id": corpus["corpus_id"],
        "required_review": corpus["evaluation"]["required_review"],
    }


def validate_fixture_manifest(
    plugin_root: Path = PLUGIN_ROOT, manifest_value: Any | None = None
) -> dict[str, Any]:
    manifest = _require_object(
        manifest_value
        if manifest_value is not None
        else _load_json(plugin_root / "quality" / "fixture-manifest.json"),
        "El manifiesto de fixtures",
    )
    errors: list[str] = []
    if manifest.get("schema_version") != "1.0":
        errors.append("El manifiesto de fixtures debe usar schema_version 1.0.")
    if manifest.get("classification") != "synthetic-only":
        errors.append("Los fixtures deben estar clasificados como synthetic-only.")
    relative_root = manifest.get("root")
    if relative_root != "tests/fixtures":
        errors.append("La raíz de fixtures debe ser tests/fixtures.")
        relative_root = "tests/fixtures"
    fixtures_root = (plugin_root / relative_root).resolve()
    declared: set[str] = set()
    entries = manifest.get("fixtures")
    if not isinstance(entries, list) or not entries:
        errors.append("El manifiesto debe declarar fixtures.")
        entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("Cada fixture declarado debe ser un objeto.")
            continue
        relative = entry.get("path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or Path(relative).suffix != ".json"
        ):
            errors.append(f"Ruta de fixture inválida: {relative!r}")
            continue
        if relative in declared:
            errors.append(f"Fixture duplicado: {relative}")
            continue
        declared.add(relative)
        path = fixtures_root / relative
        try:
            path.resolve().relative_to(fixtures_root)
        except ValueError:
            errors.append(f"Fixture fuera de la raíz: {relative}")
            continue
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            errors.append(f"Fixture enlazado no permitido: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Fixture ausente: {relative}")
            continue
        try:
            payload = _load_json(path)
        except HarnessError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict) or payload.get("id") != entry.get("id"):
            errors.append(f"ID no coincidente en {relative}.")
        expected_hash = entry.get("sha256")
        actual_hash = _sha256_file(path)
        if expected_hash != actual_hash:
            errors.append(
                f"Hash de fixture no coincidente en {relative}: {actual_hash}"
            )
    actual = {
        path.name
        for path in fixtures_root.glob("*.json")
        if path.is_file() and not path.is_symlink()
    }
    undeclared = sorted(actual - declared)
    missing = sorted(declared - actual)
    if undeclared:
        errors.append(f"Fixtures no declarados: {undeclared}")
    if missing:
        errors.append(f"Fixtures declarados ausentes: {missing}")
    return {
        "status": "passed" if not errors else "failed",
        "fixture_count": len(declared),
        "errors": errors,
    }


def validate_observations(value: Any, corpus: dict[str, Any]) -> dict[str, Any]:
    observations = _require_object(value, "Las observaciones")
    required = {
        "schema_version",
        "corpus_id",
        "corpus_sha256",
        "evaluator_context",
        "activation_results",
        "document_reviews",
    }
    if set(observations) != required:
        raise HarnessError(
            f"Campos de observaciones inválidos: {sorted(set(observations) ^ required)}"
        )
    if observations.get("schema_version") != "1.0":
        raise HarnessError("Las observaciones deben usar schema_version 1.0.")
    if observations.get("corpus_id") != corpus.get("corpus_id"):
        raise HarnessError("corpus_id no coincide con el corpus evaluado.")
    corpus_hash = _sha256_bytes(_canonical_bytes(corpus))
    if observations.get("corpus_sha256") != corpus_hash:
        raise HarnessError(
            "corpus_sha256 no coincide; las observaciones están obsoletas."
        )
    context = observations.get("evaluator_context")
    if not isinstance(context, dict) or set(context) != {
        "kind",
        "product",
        "executed_on",
        "evidence_reference",
    }:
        raise HarnessError("evaluator_context no respeta el contrato saneado.")
    if context.get("kind") not in {"controlled-codex-session", "human-review"}:
        raise HarnessError("kind de evaluador no soportado.")
    if context.get("product") != "Codex":
        raise HarnessError(
            "Las observaciones de esta implementación deben proceder de Codex."
        )
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", str(context.get("executed_on"))):
        raise HarnessError("executed_on debe ser una fecha ISO.")
    if (
        not isinstance(context.get("evidence_reference"), str)
        or len(context["evidence_reference"].strip()) < 3
    ):
        raise HarnessError("Falta una referencia de evidencia saneada.")
    activation_results = observations.get("activation_results")
    document_reviews = observations.get("document_reviews")
    if not isinstance(activation_results, list) or not isinstance(
        document_reviews, list
    ):
        raise HarnessError("activation_results y document_reviews deben ser listas.")
    seen: set[str] = set()
    for result in activation_results:
        if not isinstance(result, dict) or set(result) != {"case_id", "actual_skill"}:
            raise HarnessError("Resultado de activación inválido.")
        case_id = result.get("case_id")
        actual = result.get("actual_skill")
        if not isinstance(case_id, str) or not re.fullmatch(r"ACT-[0-9]{3}", case_id):
            raise HarnessError(f"case_id observado inválido: {case_id!r}")
        if case_id in seen:
            raise HarnessError(f"Observación duplicada: {case_id}")
        seen.add(str(case_id))
        if actual is not None and actual not in ALLOWED_SKILLS:
            raise HarnessError(f"Skill observada inválida en {case_id}: {actual!r}")
    for review in document_reviews:
        if not isinstance(review, dict) or set(review) != {
            "artifact_reference",
            "scores",
        }:
            raise HarnessError("Revisión documental inválida.")
        scores = review.get("scores")
        if (
            not isinstance(review.get("artifact_reference"), str)
            or len(review["artifact_reference"].strip()) < 3
        ):
            raise HarnessError("artifact_reference debe ser una referencia saneada.")
        if not isinstance(scores, dict) or set(scores) != SCORE_KEYS:
            raise HarnessError(
                "La revisión documental debe incluir las diez dimensiones."
            )
        if any(
            not isinstance(score, int) or not 1 <= score <= 5
            for score in scores.values()
        ):
            raise HarnessError(
                "Las puntuaciones documentales deben ser enteros entre 1 y 5."
            )
    return observations


def evaluate_activation(
    corpus: dict[str, Any],
    observations: dict[str, Any] | None,
    thresholds: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, float | int], list[str]]:
    if observations is None:
        return (
            {"status": "not-run", "observed": 0, "total": len(corpus["cases"])},
            {},
            [],
        )
    expected = {case["id"]: case for case in corpus["cases"]}
    actual = {
        result["case_id"]: result["actual_skill"]
        for result in observations["activation_results"]
    }
    unknown = sorted(set(actual) - set(expected))
    if unknown:
        raise HarnessError(f"Observaciones para casos inexistentes: {unknown}")
    correct_selected = 0
    predicted_selected = 0
    expected_selected = 0
    correct_routes = 0
    critical_failures: list[str] = []
    for case_id, result in actual.items():
        target = expected[case_id]["expected_skill"]
        if result is not None:
            predicted_selected += 1
        if target is not None:
            expected_selected += 1
        if result == target:
            correct_routes += 1
            if target is not None:
                correct_selected += 1
        elif expected[case_id]["critical"]:
            critical_failures.append(
                f"{case_id}: routing esperado {target!r}, observado {result!r}"
            )
    count = len(actual)
    precision = correct_selected / predicted_selected if predicted_selected else 0.0
    recall = correct_selected / expected_selected if expected_selected else 0.0
    accuracy = correct_routes / count if count else 0.0
    metrics: dict[str, float | int] = {
        "activation_samples": count,
        "activation_precision": round(precision, 6),
        "activation_recall": round(recall, 6),
        "routing_accuracy": round(accuracy, 6),
    }
    complete = count == len(expected)
    failures: list[str] = []
    for name in ("activation_precision", "activation_recall", "routing_accuracy"):
        rule = thresholds[name]
        if count < rule.get("minimum_samples", 0):
            failures.append(f"{name}: muestra insuficiente ({count})")
        elif metrics[name] < rule["target"]:
            failures.append(f"{name}: {metrics[name]} < {rule['target']}")
    status = (
        "passed"
        if complete and not failures and not critical_failures
        else "failed"
        if critical_failures or (complete and failures)
        else "incomplete"
    )
    return (
        {
            "status": status,
            "observed": count,
            "total": len(expected),
            "failures": failures,
        },
        metrics,
        critical_failures,
    )


def evaluate_document_reviews(
    observations: dict[str, Any] | None, thresholds: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, float | int]]:
    if observations is None or not observations["document_reviews"]:
        return {"status": "not-run", "reviewed": 0}, {}
    artifact_averages = [
        sum(review["scores"].values()) / len(review["scores"])
        for review in observations["document_reviews"]
    ]
    average = round(sum(artifact_averages) / len(artifact_averages), 6)
    minimum = round(min(artifact_averages), 6)
    metrics: dict[str, float | int] = {
        "document_review_samples": len(artifact_averages),
        "document_review_average": average,
        "document_review_minimum": minimum,
    }
    failures = []
    if average < thresholds["document_review_average"]["target"]:
        failures.append("La media documental no alcanza 4 sobre 5.")
    if minimum < thresholds["document_review_minimum"]["target"]:
        failures.append("Existe un documento con media inferior a 3 sobre 5.")
    return {
        "status": "passed" if not failures else "failed",
        "reviewed": len(artifact_averages),
        "failures": failures,
    }, metrics


def evaluate_pilot(summary: dict[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {"status": "not-run", "decision": "not-evaluated"}
    summary = validate_pilot_summary(summary)
    decision = summary["decision"]
    status = decision.get("status")
    if status == "go":
        channel_status = "passed"
    elif status in {"not-evaluated", "go-conditioned"}:
        channel_status = "incomplete"
    elif status in {"no-go", "withdrawal"}:
        channel_status = "failed"
    else:
        raise HarnessError(f"Decisión de piloto no soportada: {status!r}")
    return {
        "status": channel_status,
        "decision": status,
        "project_count": summary.get("project_count"),
        "participant_count": summary.get("participant_count"),
        "sample_sufficient": summary.get("sample_sufficient"),
    }


def evaluate_release_approval(
    approval: dict[str, Any] | None,
    plugin_version: str,
) -> dict[str, Any]:
    if approval is None:
        return {"status": "not-run", "decision": "not-evaluated"}
    approval = validate_release_approval(approval, plugin_version)
    decision = approval["decision"]
    status = decision["status"]
    channel_status = (
        "passed"
        if status == "approved"
        else "incomplete"
        if status == "deferred"
        else "failed"
    )
    return {
        "status": channel_status,
        "decision": status,
        "authority_role": decision["authority_role"],
        "basis": approval["basis"],
        "evidence_handling": approval["evidence_handling"],
    }


def _run_command(
    check_id: str, command: list[str], json_output: bool = False, timeout: int = 600
) -> tuple[dict[str, Any], Any | None, str]:
    process = run_managed_command(
        command,
        cwd=PLUGIN_ROOT,
        timeout=timeout,
        label=check_id,
    )
    combined = f"{process.stdout}\n{process.stderr}".strip()
    payload: Any | None = None
    parse_error = ""
    if json_output and process.stdout.strip():
        try:
            payload = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            parse_error = f"salida JSON inválida: {exc}"
    passed = process.returncode == 0 and not process.timed_out and not parse_error
    summary = "exit=0" if passed else (
        f"timeout={timeout}s" if process.timed_out else f"exit={process.returncode}"
    )
    if parse_error:
        summary = f"{summary}; {parse_error}"
    elif not passed and isinstance(payload, dict):
        failed_checks = [
            check
            for check in payload.get("checks", [])
            if isinstance(check, dict) and check.get("status") == "failed"
        ]
        if failed_checks:
            failures = ",".join(
                f"{check.get('name', 'unknown')}(exit={check.get('exit_code', '?')})"
                for check in failed_checks[:3]
            )
            summary = f"{summary}; failed={failures}"
        else:
            failed_results = [
                result
                for result in payload.get("results", [])
                if isinstance(result, dict) and result.get("status") == "failed"
            ]
            if failed_results:
                failures = ",".join(
                    str(result.get("name") or result.get("id") or "unknown")
                    for result in failed_results[:3]
                )
                summary = f"{summary}; failed={failures}"
    return (
        {
            "id": check_id,
            "status": "passed" if passed else "failed",
            "critical": True,
            "summary": summary,
            "duration_seconds": process.duration_seconds,
            "timeout_seconds": timeout,
            "termination": process.termination,
            "process_cleanup": process.process_cleanup,
            "reproduce": " ".join(command),
        },
        payload,
        combined,
    )


def _result_index(
    payload: dict[str, Any] | None,
    *,
    source: str,
    allow_short_name: bool,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    if payload is None:
        return {}, []
    results = payload.get("results")
    if not isinstance(results, list):
        return {}, [f"{source}: falta la lista estructurada results"]
    index: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    for position, result in enumerate(results, 1):
        if not isinstance(result, dict):
            errors.append(f"{source}: resultado {position} no es un objeto")
            continue
        result_id = result.get("id")
        status = result.get("status")
        if not isinstance(result_id, str) or not result_id:
            errors.append(f"{source}: resultado {position} sin id")
            continue
        if status is None and isinstance(result.get("passed"), bool):
            status = "passed" if result["passed"] else "failed"
        if status not in {"passed", "failed", "skipped"}:
            errors.append(f"{source}: estado inválido en {result_id}: {status!r}")
            continue
        normalized = {**result, "id": result_id, "status": status}
        keys = {result_id}
        if allow_short_name:
            name = result.get("name")
            if isinstance(name, str) and name:
                keys.add(name)
            keys.add(result_id.rsplit(".", 1)[-1])
        for key in keys:
            index.setdefault(key, []).append(normalized)
    return index, errors


def evaluate_automated_evidence(
    catalog: dict[str, Any],
    unit_payload: dict[str, Any] | None,
    eval_payload: dict[str, Any] | None,
    profile_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve every automated catalog claim to one concrete executed result."""

    test_index, errors = _result_index(
        unit_payload, source="unit-tests", allow_short_name=True
    )
    eval_index, eval_errors = _result_index(
        eval_payload, source="deterministic-evals", allow_short_name=False
    )
    errors.extend(eval_errors)
    cases: list[dict[str, Any]] = []
    failures = list(errors)
    critical_incomplete: list[str] = []
    for case in [*catalog["cases"], *catalog.get("extension_cases", [])]:
        if case.get("mode") != "automated":
            continue
        outcomes: list[dict[str, Any]] = []
        for reference in case["evidence"]:
            kind, evidence_id = reference.split(":", 1)
            matches: list[dict[str, Any]] = []
            if kind == "test":
                matches = test_index.get(evidence_id, [])
                unavailable = unit_payload is None
            elif kind == "eval":
                matches = eval_index.get(evidence_id, [])
                unavailable = eval_payload is None
            else:
                unavailable = profile_payload is None
                if evidence_id != "complete-gate":
                    outcomes.append(
                        {
                            "reference": reference,
                            "status": "failed",
                            "reason": "profile-evidence-unknown",
                        }
                    )
                    continue
                if profile_payload is not None:
                    outcomes.append(
                        {
                            "reference": reference,
                            "status": "passed"
                            if profile_payload.get("complete_gate") is True
                            else "failed",
                            "resolved_id": "complete-gate",
                            "reason": None
                            if profile_payload.get("complete_gate") is True
                            else "complete-gate-failed",
                        }
                    )
                    continue
            if unavailable:
                outcomes.append(
                    {
                        "reference": reference,
                        "status": "not-run",
                        "reason": f"{kind}-results-unavailable",
                    }
                )
            elif len(matches) == 1:
                match = matches[0]
                outcomes.append(
                    {
                        "reference": reference,
                        "status": match["status"],
                        "resolved_id": match["id"],
                        **(
                            {"reason": f"{kind}-{match['status']}"}
                            if match["status"] != "passed"
                            else {}
                        ),
                    }
                )
            else:
                outcomes.append(
                    {
                        "reference": reference,
                        "status": "failed",
                        "reason": "evidence-not-found"
                        if not matches
                        else "evidence-ambiguous",
                    }
                )
        failed = [item for item in outcomes if item["status"] == "failed"]
        pending = [
            item for item in outcomes if item["status"] in {"skipped", "not-run"}
        ]
        case_status = "failed" if failed else "incomplete" if pending else "passed"
        case_result = {
            "id": case["id"],
            "critical": case["critical"],
            "status": case_status,
            "evidence": outcomes,
        }
        cases.append(case_result)
        if failed:
            failures.extend(
                f"{case['id']}: {item['reference']} ({item.get('reason', 'failed')})"
                for item in failed
            )
        if case["critical"] and case_status == "incomplete":
            critical_incomplete.append(case["id"])
    failed_cases = [case["id"] for case in cases if case["status"] == "failed"]
    incomplete_cases = [case["id"] for case in cases if case["status"] == "incomplete"]
    status = (
        "failed"
        if failures or failed_cases
        else "incomplete"
        if critical_incomplete
        else "passed"
    )
    return {
        "status": status,
        "cases": cases,
        "counts": {
            "total": len(cases),
            "passed": sum(case["status"] == "passed" for case in cases),
            "failed": len(failed_cases),
            "incomplete": len(incomplete_cases),
        },
        "critical_incomplete": sorted(critical_incomplete),
        "pending": sorted(incomplete_cases),
        "failures": sorted(set(failures)),
    }


def _unit_test_metrics(payload: dict[str, Any] | None) -> dict[str, int]:
    if payload is None or not isinstance(payload.get("results"), list):
        return {}
    statuses = [
        result.get("status")
        for result in payload["results"]
        if isinstance(result, dict)
    ]
    passed = statuses.count("passed")
    skipped = statuses.count("skipped")
    failed = statuses.count("failed")
    return {
        "unit_tests_total": len(statuses),
        "unit_tests_executed": passed + failed,
        "unit_tests_passed": passed,
        "unit_tests_skipped": skipped,
        "unit_tests_failed": failed,
    }


def _merge_unit_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not payloads:
        return None
    results = [
        result
        for payload in payloads
        for result in payload.get("results", [])
        if isinstance(result, dict)
    ]
    ids = [str(result.get("id")) for result in results]
    if len(ids) != len(set(ids)):
        raise HarnessError("Las suites unitarias produjeron resultados duplicados.")
    return {
        "schema_version": "1.0",
        "suite": "LKS-SDD unittest",
        "selected_suite": "all",
        "passed": all(payload.get("passed") is True for payload in payloads),
        "duration_seconds": round(
            sum(float(payload.get("duration_seconds", 0)) for payload in payloads), 3
        ),
        "counts": {
            "total": len(results),
            "passed": sum(result.get("status") == "passed" for result in results),
            "skipped": sum(result.get("status") == "skipped" for result in results),
            "failed": sum(result.get("status") == "failed" for result in results),
        },
        "results": sorted(results, key=lambda item: str(item.get("id"))),
    }


def run_automated(
    catalog: dict[str, Any], profile_mode: str | bool, evaluated_on: str = "2026-08-26"
) -> tuple[
    list[dict[str, Any]],
    dict[str, float | int],
    list[str],
    dict[str, Any],
]:
    if isinstance(profile_mode, bool):
        profile_mode = "execute" if profile_mode else "not-run"
    checks: list[dict[str, Any]] = []
    metrics: dict[str, float | int] = {}
    critical_failures: list[str] = []
    fixture_started = time.monotonic()
    fixture_result = validate_fixture_manifest()
    checks.append(
        {
            "id": "fixture-integrity",
            "status": fixture_result["status"],
            "critical": True,
            "summary": f"fixtures={fixture_result['fixture_count']}",
            "duration_seconds": round(time.monotonic() - fixture_started, 3),
            "timeout_seconds": None,
            "termination": "normal",
            "process_cleanup": "not-required",
            "reproduce": f"{sys.executable} scripts/validate_fixture_manifest.py .",
        }
    )
    if fixture_result["errors"]:
        critical_failures.extend(fixture_result["errors"])
    commands = [
        (
            "plugin-contract",
            [sys.executable, "-X", "utf8", "scripts/validate_plugin_contract.py", "."],
            False,
            120,
        ),
        (
            "reference-profile-structure",
            [
                sys.executable,
                "-X",
                "utf8",
                "scripts/validate_reference_profile.py",
                "--all",
                "--allow-unvalidated",
            ],
            False,
            120,
        ),
        *[
            (
                f"unit-tests-{suite}",
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "tests/run_unit_tests.py",
                    "--suite",
                    suite,
                ],
                True,
                UNIT_TEST_TIMEOUT_SECONDS,
            )
            for suite in ("fast", "integration", "package", "profile")
        ],
        (
            "deterministic-evals",
            [sys.executable, "-X", "utf8", "tests/run_evals.py"],
            True,
            600,
        ),
    ]
    if profile_mode == "reuse":
        commands.append(
            (
                "reference-profile-complete",
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "scripts/verify_profile_certifications.py",
                    "--date",
                    evaluated_on,
                    "--max-age-days",
                    "90",
                    "--json",
                ],
                True,
                120,
            )
        )
    elif profile_mode == "execute":
        commands.append(
            (
                "reference-profile-complete",
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "scripts/run_reference_profile_gate.py",
                    "--profile",
                    "WEB-FASTAPI-REACT-KEYCLOAK-PG",
                    "--runtime",
                    "docker",
                    "--containers",
                    "--json",
                ],
                True,
                1800,
            )
        )
    unit_payloads: list[dict[str, Any]] = []
    eval_payload: dict[str, Any] | None = None
    profile_payload: dict[str, Any] | None = None
    for check_id, command, json_output, timeout in commands:
        check, payload, _output = _run_command(check_id, command, json_output, timeout)
        checks.append(check)
        if check_id.startswith("unit-tests-") and isinstance(payload, dict):
            unit_payloads.append(payload)
        elif check_id == "deterministic-evals" and isinstance(payload, dict):
            eval_payload = payload
        elif check_id == "reference-profile-complete" and isinstance(payload, dict):
            profile_payload = payload
        if check["status"] != "passed":
            critical_failures.append(f"{check_id}: {check['summary']}")
            break
        if check_id == "reference-profile-structure":
            metrics["profile_structure_gate"] = 1
        elif check_id == "deterministic-evals" and isinstance(payload, dict):
            results = payload.get("results", [])
            passed_count = sum(1 for result in results if result.get("passed") is True)
            total = len(results)
            metrics["automated_eval_cases"] = total
            metrics["automated_eval_pass_rate"] = (
                round(passed_count / total, 6) if total else 0.0
            )
            for result in results:
                if result.get("passed") is not True:
                    critical_failures.append(
                        f"Eval determinista fallida: {result.get('id')}"
                    )
        elif check_id == "reference-profile-complete" and isinstance(payload, dict):
            metrics["profile_complete_gate"] = (
                1 if payload.get("complete_gate") is True else 0
            )
            if payload.get("complete_gate") is not True:
                critical_failures.append(
                    "El gate completo del perfil no quedó acreditado."
                )
    unit_payload = _merge_unit_payloads(unit_payloads)
    metrics.update(_unit_test_metrics(unit_payload))
    automated_evidence = evaluate_automated_evidence(
        catalog, unit_payload, eval_payload, profile_payload
    )
    critical_failures.extend(automated_evidence["failures"])
    metrics.update(
        {
            "automated_catalog_cases": automated_evidence["counts"]["total"],
            "automated_catalog_cases_passed": automated_evidence["counts"]["passed"],
            "automated_catalog_cases_failed": automated_evidence["counts"]["failed"],
            "automated_catalog_cases_incomplete": automated_evidence["counts"][
                "incomplete"
            ],
        }
    )
    critical_failures = sorted(set(critical_failures))
    metrics["critical_failures"] = len(critical_failures)
    return checks, metrics, critical_failures, automated_evidence


def _git_output(arguments: list[str]) -> str:
    try:
        process = subprocess.run(
            ["git", *arguments],
            cwd=PLUGIN_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError(f"No se pudo consultar Git: {exc}") from exc
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise HarnessError(
            f"Git no pudo vincular el reporte ({' '.join(arguments)}): {detail}"
        )
    return process.stdout.strip()


def _git_bytes(arguments: list[str]) -> bytes:
    """Run a Git query without losing NUL-delimited path information."""
    try:
        process = subprocess.run(
            ["git", *arguments],
            cwd=PLUGIN_ROOT,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError(f"No se pudo consultar Git: {exc}") from exc
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise HarnessError(
            f"Git no pudo vincular el reporte ({' '.join(arguments)}): {detail}"
        )
    return process.stdout


def _validated_git_path(raw_path: bytes) -> str:
    try:
        relative = raw_path.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise HarnessError("Git devolvió una ruta que no es UTF-8 válida.") from exc
    posix_path = PurePosixPath(relative)
    windows_path = PureWindowsPath(relative)
    if (
        not relative
        or "\\" in relative
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise HarnessError(f"Git devolvió una ruta no segura: {relative!r}")
    return relative


def _head_entries() -> dict[str, tuple[str, str, str]]:
    entries: dict[str, tuple[str, str, str]] = {}
    aliases: set[str] = set()
    for record in _git_bytes(["ls-tree", "-r", "-z", "--full-tree", "HEAD"]).split(
        b"\0"
    ):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            raw_mode, raw_type, raw_object_id = metadata.split(b" ", 2)
            mode = raw_mode.decode("ascii", errors="strict")
            object_type = raw_type.decode("ascii", errors="strict")
            object_id = raw_object_id.decode("ascii", errors="strict").lower()
        except (UnicodeDecodeError, ValueError) as exc:
            raise HarnessError("El árbol HEAD contiene una entrada no interpretable.") from exc
        valid_entry = (
            (mode in {"100644", "100755", "120000"} and object_type == "blob")
            or (mode == "160000" and object_type == "commit")
        )
        if not valid_entry or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id):
            raise HarnessError(
                f"El árbol HEAD contiene modo, tipo u objeto no admitido: {record!r}"
            )
        relative = _validated_git_path(raw_path)
        alias = os.path.normcase(str(PLUGIN_ROOT / Path(*PurePosixPath(relative).parts)))
        if relative in entries or alias in aliases:
            raise HarnessError(
                f"El árbol HEAD contiene rutas duplicadas o ambiguas: {relative!r}"
            )
        entries[relative] = (mode, object_type, object_id)
        aliases.add(alias)
    return entries


def _index_entries() -> dict[str, tuple[str, str, str]]:
    entries: dict[str, tuple[str, str, str]] = {}
    for record in _git_bytes(["ls-files", "--stage", "-z"]).split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            raw_mode, raw_object_id, raw_stage = metadata.split(b" ", 2)
            mode = raw_mode.decode("ascii", errors="strict")
            object_id = raw_object_id.decode("ascii", errors="strict").lower()
            stage = raw_stage.decode("ascii", errors="strict")
        except (UnicodeDecodeError, ValueError) as exc:
            raise HarnessError("El índice Git contiene una entrada no interpretable.") from exc
        relative = _validated_git_path(raw_path)
        if (
            stage != "0"
            or relative in entries
            or mode not in {"100644", "100755", "120000", "160000"}
            or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
        ):
            raise HarnessError(
                f"El índice Git contiene una entrada no consolidada o inválida: {relative!r}"
            )
        object_type = "commit" if mode == "160000" else "blob"
        entries[relative] = (mode, object_type, object_id)
    return entries


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _safe_worktree_path(relative: str) -> tuple[Path, os.stat_result] | None:
    current = PLUGIN_ROOT
    parts = PurePosixPath(relative).parts
    for part in parts[:-1]:
        current /= part
        try:
            current_stat = current.lstat()
        except OSError:
            return None
        if _is_link_like(current) or not stat.S_ISDIR(current_stat.st_mode):
            return None
    path = current / parts[-1]
    try:
        return path, path.lstat()
    except OSError:
        return None


def _symlink_blob_id(path: Path, object_id_length: int) -> str:
    try:
        payload = os.fsencode(os.readlink(path))
    except OSError:
        return ""
    header = f"blob {len(payload)}\0".encode("ascii")
    algorithm = hashlib.sha1 if object_id_length == 40 else hashlib.sha256
    return algorithm(header + payload).hexdigest()


def _worktree_entry_matches(
    relative: str, mode: str, object_id: str
) -> bool:
    resolved = _safe_worktree_path(relative)
    if resolved is None:
        return False
    path, path_stat = resolved
    if mode == "120000":
        return path.is_symlink() and _symlink_blob_id(path, len(object_id)) == object_id
    if mode == "160000":
        # Release bundles do not admit submodules; a gitlink can never attest a
        # complete, self-contained plugin working tree.
        return False
    if _is_link_like(path) or not stat.S_ISREG(path_stat.st_mode):
        return False
    if os.name != "nt":
        executable = bool(path_stat.st_mode & 0o111)
        if executable != (mode == "100755"):
            return False
    actual_id = _git_output(
        ["hash-object", f"--path={relative}", "--", relative]
    ).lower()
    return actual_id == object_id


def _repository_tree_matches_head() -> bool:
    """Compare HEAD, index and real files without trusting index stat flags."""
    head = _head_entries()
    if _index_entries() != head:
        return False
    # Deliberately inspect ignored files too. Python startup hooks, .pth files,
    # local configs, scripts and dependency trees can affect the child checks
    # even when .gitignore or .git/info/exclude hides them from git status.
    # A release attestation therefore starts from a checkout with no untracked
    # files; generated outputs created by the checks occur after this snapshot.
    untracked = _git_bytes(["ls-files", "--others", "-z"])
    if any(untracked.split(b"\0")):
        return False
    return all(
        _worktree_entry_matches(relative, mode, object_id)
        for relative, (mode, _object_type, object_id) in head.items()
    )


def repository_binding() -> dict[str, str]:
    """Bind a report to the exact repository HEAD and observed tree state."""
    repository_root = Path(_git_output(["rev-parse", "--show-toplevel"])).resolve()
    if repository_root != PLUGIN_ROOT.resolve():
        raise HarnessError(
            "La raíz Git no coincide con la raíz del plugin; no se puede vincular "
            "el reporte de forma inequívoca."
        )
    commit = _git_output(["rev-parse", "--verify", "HEAD"]).lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise HarnessError(f"HEAD no es un commit SHA-1 completo válido: {commit!r}")
    porcelain = not _repository_tree_matches_head()
    return {
        "commit": commit,
        "tree_state": "dirty" if porcelain else "clean",
    }


def _metric_direction(name: str) -> str:
    try:
        return METRIC_DIRECTIONS[name]
    except KeyError as exc:
        raise HarnessError(
            f"La métrica {name!r} no declara dirección de comparación."
        ) from exc


def compare_metrics(
    current: dict[str, float | int], baseline: dict[str, Any]
) -> dict[str, Any]:
    baseline_metrics = baseline.get("metrics")
    if not isinstance(baseline_metrics, dict):
        raise HarnessError("La baseline no declara metrics.")
    baseline_commit = baseline.get("source_commit")
    if not isinstance(baseline_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", baseline_commit
    ):
        raise HarnessError("La baseline no declara un source_commit SHA-1 completo.")
    comparisons = []
    regressions = []
    for name in sorted(set(current) & set(baseline_metrics)):
        old = baseline_metrics[name]
        new = current[name]
        if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
            continue
        direction = _metric_direction(name)
        regressed = (
            new > old
            if direction == "lower"
            else new < old
            if direction == "higher"
            else False
        )
        comparisons.append(
            {
                "metric": name,
                "direction": direction,
                "baseline": old,
                "current": new,
                "regressed": regressed,
            }
        )
        if regressed:
            regressions.append(f"{name}: {new} frente a {old}")
    return {
        "baseline_version": baseline.get("plugin_version"),
        "baseline_commit": baseline_commit,
        "status": "failed" if regressions else "passed",
        "comparisons": comparisons,
        "regressions": regressions,
        "not_compared": sorted(set(baseline_metrics) - set(current)),
        "current_only": sorted(set(current) - set(baseline_metrics)),
    }


def build_report(
    evaluated_on: str,
    channel: str,
    observations_path: Path | None,
    pilot_summary_path: Path | None,
    baseline_path: Path,
    profile_mode: str | bool,
    rerun_reason: str | None = None,
    release_approval_path: Path | None = None,
) -> dict[str, Any]:
    execution_started = time.monotonic()
    if isinstance(profile_mode, bool):
        profile_mode = "execute" if profile_mode else "not-run"
    # Capture the source boundary before launching any child validator, test or
    # profile gate. This prevents an ignored file from influencing checks and
    # only afterwards being misreported as part of a clean starting tree.
    source = repository_binding()
    if source["tree_state"] != "clean":
        raise HarnessError(
            "Preflight detenido: el checkout inicial no coincide íntegramente con "
            "HEAD (source.tree_state=dirty); no se ha lanzado la suite automatizada."
        )
    catalog = validate_catalog(_load_json(CATALOG_PATH))
    corpus = validate_corpus(_load_json(CORPUS_PATH))
    definition_corpus = validate_definition_corpus(
        _load_json(DEFINITION_CORPUS_PATH), catalog
    )
    manifest = _require_object(_load_json(MANIFEST_PATH), "El manifest del plugin")
    if not _definition_corpus_matches_plugin_line(
        definition_corpus.get("plugin_version"), manifest.get("version")
    ):
        raise HarnessError(
            "El corpus de definición debe pertenecer a la misma línea major.minor "
            "del manifest y no puede ser posterior a la release evaluada."
        )
    if release_approval_path is not None and channel != "stable":
        raise HarnessError(
            "--release-approval solo corresponde a una evaluación stable."
        )
    release_approval = None
    if release_approval_path is not None:
        release_approval = validate_release_approval(
            _load_json(release_approval_path), str(manifest.get("version"))
        )
    observations = None
    if observations_path is not None:
        observations = validate_observations(_load_json(observations_path), corpus)
    pilot_summary = None
    if pilot_summary_path is not None:
        pilot_summary = validate_pilot_summary(_load_json(pilot_summary_path))
    checks, metrics, critical_failures, automated_evidence = run_automated(
        catalog, profile_mode, evaluated_on
    )
    suite_actual = {
        check["id"].removeprefix("unit-tests-"): float(
            check.get("duration_seconds", 0)
        )
        for check in checks
        if check["id"].startswith("unit-tests-")
    }
    candidate_duration = sum(
        float(check.get("duration_seconds", 0))
        for check in checks
        if not (
            profile_mode == "execute" and check["id"] == "reference-profile-complete"
        )
    )
    performance_actual = {**suite_actual, "candidate": round(candidate_duration, 3)}
    if profile_mode == "execute":
        profile_check = next(
            (check for check in checks if check["id"] == "reference-profile-complete"),
            None,
        )
        if profile_check is not None:
            performance_actual["profile_execute"] = float(
                profile_check.get("duration_seconds", 0)
            )
    performance_policy = load_performance_policy()
    fingerprint = runner_fingerprint()
    performance = performance_assessment(
        performance_actual, performance_policy, fingerprint
    )
    critical_failures.extend(performance["regressions"])
    activation, activation_metrics, activation_critical = evaluate_activation(
        corpus, observations, catalog["thresholds"]
    )
    document_review, document_metrics = evaluate_document_reviews(
        observations, catalog["thresholds"]
    )
    metrics.update(activation_metrics)
    metrics.update(document_metrics)
    critical_failures.extend(activation_critical)
    metrics["critical_failures"] = len(critical_failures)
    baseline = _require_object(_load_json(baseline_path), "La baseline")
    comparison = compare_metrics(metrics, baseline)
    automated_status = (
        "failed"
        if any(check["status"] == "failed" for check in checks)
        or automated_evidence["status"] == "failed"
        else "incomplete"
        if automated_evidence["status"] == "incomplete"
        else "passed"
    )
    channels = {
        "automated": {
            "status": automated_status,
            "counts": automated_evidence["counts"],
            "cases": automated_evidence["cases"],
            "critical_incomplete": automated_evidence["critical_incomplete"],
            "pending": automated_evidence["pending"],
        },
        "fixture-integrity": next(
            check for check in checks if check["id"] == "fixture-integrity"
        ),
        "profile-complete": {
            "status": next(
                (
                    check["status"]
                    for check in checks
                    if check["id"] == "reference-profile-complete"
                ),
                "not-run",
            ),
            "evidence_mode": profile_mode,
        },
        "regression": {"status": comparison["status"]},
        "definition-conversation": evaluate_definition_conversation(definition_corpus),
        "activation": activation,
        "document-review": document_review,
        "pilot": evaluate_pilot(pilot_summary),
        "release-approval": evaluate_release_approval(
            release_approval, str(manifest.get("version"))
        ),
    }
    required = catalog["channels"][channel]["required"]
    blockers = list(critical_failures)
    blockers.extend(f"Rendimiento: {item}" for item in performance["regressions"])
    if comparison["regressions"]:
        blockers.extend(f"Regresión: {item}" for item in comparison["regressions"])
    missing_evidence = [
        name
        for name in required
        if channels[name]["status"] in {"not-run", "incomplete"}
    ]
    if "automated" in required:
        missing_evidence.extend(
            f"automated:{case_id}"
            for case_id in automated_evidence["critical_incomplete"]
        )
    failed_channels = [
        name for name in required if channels[name]["status"] == "failed"
    ]
    blockers.extend(f"Canal requerido fallido: {name}" for name in failed_channels)
    if blockers:
        gate_status = "failed"
    elif missing_evidence:
        gate_status = "incomplete"
    else:
        gate_status = "passed"
    return {
        "schema_version": "1.2",
        "suite": catalog["suite"],
        "plugin_version": manifest.get("version"),
        "evaluated_on": evaluated_on,
        "channel": channel,
        "source": source,
        "inputs": {
            "catalog_sha256": _sha256_bytes(_canonical_bytes(catalog)),
            "corpus_sha256": _sha256_bytes(_canonical_bytes(corpus)),
            "definition_corpus_sha256": _sha256_bytes(
                _canonical_bytes(definition_corpus)
            ),
            "fixture_manifest_sha256": _sha256_file(FIXTURE_MANIFEST_PATH),
            "observations_sha256": _sha256_file(observations_path)
            if observations_path
            else None,
            "pilot_summary_sha256": _sha256_file(pilot_summary_path)
            if pilot_summary_path
            else None,
            "release_approval_sha256": _sha256_file(release_approval_path)
            if release_approval_path
            else None,
            "baseline_sha256": _sha256_bytes(_canonical_bytes(baseline)),
            "performance_policy_sha256": _sha256_bytes(
                _canonical_bytes(performance_policy)
            ),
        },
        "checks": checks,
        "execution": {
            "runner_fingerprint": fingerprint,
            "profile_mode": profile_mode,
            "duration_seconds": round(time.monotonic() - execution_started, 3),
            "rerun_reason": rerun_reason,
        },
        "performance": performance,
        "channels": channels,
        "metrics": dict(sorted(metrics.items())),
        "critical_failures": sorted(critical_failures),
        "comparison": comparison,
        "gate": {
            "status": gate_status,
            "eligible": gate_status == "passed",
            "blockers": sorted(set(blockers)),
            "missing_evidence": sorted(missing_evidence),
        },
    }


def _validate_output_destination(path: Path, force: bool) -> Path:
    destination = path.expanduser().resolve()
    if destination.exists() and not force:
        raise HarnessError(
            f"El reporte ya existe; use --force para reemplazarlo: {destination}"
        )
    return destination


def _atomic_write(path: Path, value: dict[str, Any], force: bool) -> None:
    destination = _validate_output_destination(path, force)
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, destination)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="strict")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--channel", choices=("candidate", "stable"), default="candidate"
    )
    parser.add_argument("--date", default=date.today().isoformat(), dest="evaluated_on")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--pilot-summary", type=Path)
    parser.add_argument(
        "--release-approval",
        type=Path,
        help=(
            "Decisión saneada y versionada del responsable del proyecto; "
            "es la autoridad humana requerida por stable."
        ),
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument(
        "--profile-mode",
        choices=("not-run", "reuse", "execute"),
        default="not-run",
        help=(
            "not-run omite el canal, reuse acredita certificaciones exactas vigentes "
            "y execute vuelve a ejecutar el perfil Docker completo."
        ),
    )
    parser.add_argument(
        "--include-complete-profile",
        action="store_true",
        help="Alias heredado de --profile-mode execute.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rerun-reason")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Diagnóstico opcional de la vinculación completa de fuente; la "
            "ejecución integral ya realiza esta misma comprobación antes de los tests."
        ),
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", args.evaluated_on):
        print("ERROR: --date debe usar YYYY-MM-DD.", file=sys.stderr)
        return 2
    if args.include_complete_profile and args.profile_mode not in {"not-run", "execute"}:
        print(
            "ERROR: --include-complete-profile no es compatible con "
            "--profile-mode reuse.",
            file=sys.stderr,
        )
        return 2
    profile_mode = "execute" if args.include_complete_profile else args.profile_mode
    if args.force and not args.rerun_reason:
        print(
            "ERROR: --force requiere --rerun-reason para evitar repeticiones opacas.",
            file=sys.stderr,
        )
        return 2
    try:
        if args.preflight_only:
            source = repository_binding()
            if source["tree_state"] != "clean":
                raise HarnessError(
                    "Preflight detenido: source.tree_state=dirty; no se ejecutarán tests."
                )
            validate_catalog(_load_json(CATALOG_PATH))
            load_performance_policy()
            print(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "status": "passed",
                        "source": source,
                        "profile_mode": profile_mode,
                        "tests_started": False,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.output:
            # Output collisions are parameter errors and must fail before the
            # first costly check, not after the candidate has already run.
            _validate_output_destination(args.output, args.force)
        report = build_report(
            args.evaluated_on,
            args.channel,
            args.observations,
            args.pilot_summary,
            args.baseline.expanduser().resolve(),
            profile_mode,
            args.rerun_reason,
            args.release_approval,
        )
        if args.output:
            _atomic_write(args.output, report, args.force)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report["gate"]["status"] == "passed":
            return 0
        return 3 if report["gate"]["status"] == "incomplete" else 2
    except (HarnessError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
