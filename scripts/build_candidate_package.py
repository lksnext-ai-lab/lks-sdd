#!/usr/bin/env python3
"""Build deterministic LKS-SDD candidate bundles from an exact clean Git HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
QUALITY_REPORT_NAME = "quality-report.json"
EXPECTED_BASELINE_COMMIT = "7318ccc337570e296bffda68a8e49724bed94c99"
EXPECTED_CANDIDATE_CHECKS = {
    "fixture-integrity",
    "plugin-contract",
    "reference-profile-structure",
    "unit-tests",
    "deterministic-evals",
    "reference-profile-complete",
}
EXPECTED_CANDIDATE_REQUIRED_CHANNELS = {
    "automated",
    "fixture-integrity",
    "profile-complete",
    "regression",
}
EXPECTED_CANDIDATE_OPTIONAL_CHANNELS = {
    "definition-conversation",
    "activation",
    "document-review",
    "pilot",
}
EXPECTED_AUTOMATED_CASE_IDS = (
    "FX-02",
    "FX-03",
    "FX-04",
    "FX-05",
    "FX-08",
    "FX-09",
    "FX-10",
    "FX-11",
    "FX-12",
    "FX-13",
    "FX-14",
    "FX-15",
    "FX-18",
    "FX-22",
    "FX-23",
    "FX-24",
    "FX-25",
    "FX-26",
    "FX-27",
    "FX-28",
    "FX-29",
    "FX-30",
    "FX-31",
    "FX-32",
    "FX-33",
    "FX-34",
    "FX-35",
)
EXPECTED_DETERMINISTIC_EVAL_IDS = {
    "FX-M1-ALTERNATIVE-STACK",
    "FX-M1-HELP",
    "FX-M1-INSUFFICIENT",
    "FX-M1-NEW-PROJECT",
    "FX-M1-SCOPED-BLOCKER",
}
EXPECTED_RELEASE_METRICS = {
    "automated_catalog_cases",
    "automated_catalog_cases_failed",
    "automated_catalog_cases_incomplete",
    "automated_catalog_cases_passed",
    "automated_eval_cases",
    "automated_eval_pass_rate",
    "critical_failures",
    "profile_complete_gate",
    "profile_structure_gate",
    "unit_tests_executed",
    "unit_tests_failed",
    "unit_tests_passed",
    "unit_tests_skipped",
    "unit_tests_total",
}
METRIC_DIRECTIONS = {
    "automated_catalog_cases": "neutral",
    "automated_catalog_cases_failed": "lower",
    "automated_catalog_cases_incomplete": "lower",
    "automated_catalog_cases_passed": "higher",
    "automated_eval_cases": "neutral",
    "automated_eval_pass_rate": "higher",
    "critical_failures": "lower",
    "profile_complete_gate": "higher",
    "profile_structure_gate": "higher",
    "unit_tests_executed": "neutral",
    "unit_tests_failed": "lower",
    "unit_tests_passed": "higher",
    "unit_tests_skipped": "lower",
    "unit_tests_total": "neutral",
}
QUALITY_SCHEMA_KEYWORDS = {
    "$id",
    "$schema",
    "additionalProperties",
    "const",
    "description",
    "enum",
    "format",
    "items",
    "minLength",
    "minProperties",
    "pattern",
    "properties",
    "required",
    "title",
    "type",
    "uniqueItems",
}
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
)
EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules",
    "dist",
    "pilot-data",
}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
)


class PackageError(Exception):
    """Expected, actionable packaging failure."""


def _load_json_bytes(content: bytes, relative: str) -> Any:
    try:
        return json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"JSON ilegible {relative}: {exc}") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _matches_json_type(value: Any, expected: str) -> bool:
    checks = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: type(item) is bool,
        "integer": lambda item: isinstance(item, int) and type(item) is not bool,
        "null": lambda item: item is None,
        "number": lambda item: (
            (isinstance(item, int) and type(item) is not bool)
            or (isinstance(item, float) and math.isfinite(item))
        ),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
    }
    return expected in checks and checks[expected](value)


def _assert_supported_quality_schema(
    schema: dict[str, Any], location: str = "$schema"
) -> None:
    unsupported = sorted(set(schema) - QUALITY_SCHEMA_KEYWORDS)
    if unsupported:
        raise PackageError(
            f"{location}: keywords JSON Schema no soportadas: {unsupported}"
        )
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise PackageError(f"{location}.properties debe ser un objeto.")
    for name, child in properties.items():
        if not isinstance(child, dict):
            raise PackageError(f"{location}.properties.{name} debe ser un schema.")
        _assert_supported_quality_schema(child, f"{location}.properties.{name}")
    items = schema.get("items")
    if items is not None:
        if not isinstance(items, dict):
            raise PackageError(f"{location}.items debe ser un schema.")
        _assert_supported_quality_schema(items, f"{location}.items")
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        _assert_supported_quality_schema(additional, f"{location}.additionalProperties")
    elif additional not in {None, True, False}:
        raise PackageError(f"{location}.additionalProperties no es válido.")


def _quality_schema_errors(
    value: Any, schema: dict[str, Any], location: str = "$"
) -> list[str]:
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
        errors.append(f"{location}: valor fuera del catálogo permitido.")
    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{location}: longitud inferior a {minimum}.")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{location}: no cumple el patrón declarado.")
        if schema.get("format") == "date":
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                errors.append(f"{location}: no es una fecha ISO válida.")
            else:
                if parsed.isoformat() != value:
                    errors.append(f"{location}: no usa el formato YYYY-MM-DD.")
    if isinstance(value, list):
        if schema.get("uniqueItems") is True:
            canonical = [
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{location}: contiene elementos duplicados.")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _quality_schema_errors(item, item_schema, f"{location}[{index}]")
                )
    if isinstance(value, dict):
        minimum = schema.get("minProperties")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{location}: contiene menos de {minimum} propiedades.")
        required = schema.get("required", [])
        if not isinstance(required, list):
            errors.append(f"{location}: required inválido en el schema.")
            required = []
        for key in required:
            if key not in value:
                errors.append(f"{location}: falta la propiedad {key!r}.")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                errors.extend(
                    _quality_schema_errors(
                        item, properties[key], f"{location}.{key}"
                    )
                )
            elif additional is False:
                errors.append(f"{location}: propiedad no admitida {key!r}.")
            elif isinstance(additional, dict):
                errors.extend(
                    _quality_schema_errors(item, additional, f"{location}.{key}")
                )
    return errors


def _committed_json(
    committed_files: dict[str, bytes], relative: str
) -> dict[str, Any]:
    content = committed_files.get(relative)
    if content is None:
        raise PackageError(f"Falta el input de calidad comprometido: {relative}")
    value = _load_json_bytes(content, relative)
    if not isinstance(value, dict):
        raise PackageError(f"El input de calidad debe ser un objeto JSON: {relative}")
    return value


def _validate_fixture_attestation(
    manifest: dict[str, Any], committed_files: dict[str, bytes]
) -> int:
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("root") != "tests/fixtures"
        or manifest.get("classification") != "synthetic-only"
    ):
        raise PackageError("El manifiesto de fixtures comprometido no es válido.")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise PackageError("El manifiesto de fixtures no declara un inventario.")
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    deterministic_eval_ids: set[str] = set()
    for item in fixtures:
        if not isinstance(item, dict) or set(item) != {"path", "id", "sha256"}:
            raise PackageError("El inventario de fixtures contiene una entrada inválida.")
        relative = item.get("path")
        fixture_id = item.get("id")
        expected_hash = item.get("sha256")
        if (
            not isinstance(relative, str)
            or PurePosixPath(relative).is_absolute()
            or ".." in PurePosixPath(relative).parts
            or relative in {"", "."}
            or "\\" in relative
            or not isinstance(fixture_id, str)
            or not fixture_id
            or not isinstance(expected_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
            or relative in seen_paths
            or fixture_id in seen_ids
        ):
            raise PackageError("El inventario de fixtures no es único o seguro.")
        seen_paths.add(relative)
        seen_ids.add(fixture_id)
        content = committed_files.get(f"tests/fixtures/{relative}")
        if content is None or _sha256(content) != expected_hash:
            raise PackageError(
                f"El fixture comprometido no coincide con su hash: {relative}"
            )
        if fixture_id.startswith("FX-M1-"):
            deterministic_eval_ids.add(fixture_id)
    if deterministic_eval_ids != EXPECTED_DETERMINISTIC_EVAL_IDS:
        raise PackageError("El inventario comprometido de evals deterministas cambió.")
    return len(deterministic_eval_ids)


def _expected_comparison(
    metrics: dict[str, int | float], baseline: dict[str, Any]
) -> dict[str, Any]:
    baseline_metrics = baseline.get("metrics")
    if not isinstance(baseline_metrics, dict):
        raise PackageError("La baseline comprometida no declara métricas.")
    comparisons: list[dict[str, Any]] = []
    regressions: list[str] = []
    for name in sorted(set(metrics) & set(baseline_metrics)):
        old = baseline_metrics[name]
        new = metrics[name]
        if not _matches_json_type(old, "number"):
            raise PackageError(f"La baseline contiene una métrica inválida: {name}")
        direction = METRIC_DIRECTIONS.get(name)
        if direction is None:
            raise PackageError(f"La métrica no declara dirección: {name}")
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
        "baseline_commit": baseline.get("source_commit"),
        "status": "failed" if regressions else "passed",
        "comparisons": comparisons,
        "regressions": regressions,
        "not_compared": sorted(set(baseline_metrics) - set(metrics)),
        "current_only": sorted(set(metrics) - set(baseline_metrics)),
    }


def _safe_output(path: Path, source_root: Path = PLUGIN_ROOT) -> Path:
    output = path.expanduser().resolve()
    try:
        output.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise PackageError("El paquete debe generarse fuera del repositorio fuente.")
    if output.exists():
        raise PackageError(f"La salida ya existe y no se sobrescribirá: {output}")
    current = output.parent
    while current.parent != current:
        if current.is_symlink() or (
            hasattr(current, "is_junction") and current.is_junction()
        ):
            raise PackageError("La salida no puede atravesar symlinks o junctions.")
        current = current.parent
    return output


def _git(root: Path, *args: str, input_data: bytes | None = None) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            input=input_data,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise PackageError(f"Git no está disponible: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PackageError(
            f"Git no pudo ejecutar {' '.join(args)}"
            + (f": {detail}" if detail else ".")
        )
    return completed.stdout


def _validate_source_checkout(root: Path, source_commit: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
        raise PackageError(
            "--source-commit debe ser un commit Git completo de 40 caracteres."
        )
    source_root = root.expanduser().resolve()
    top_level = Path(
        _git(source_root, "rev-parse", "--show-toplevel")
        .decode("utf-8", errors="strict")
        .strip()
    ).resolve()
    if os.path.normcase(str(top_level)) != os.path.normcase(str(source_root)):
        raise PackageError("La fuente debe ser la raíz exacta del repositorio Git.")
    resolved_commit = (
        _git(source_root, "rev-parse", "--verify", f"{source_commit}^{{commit}}")
        .decode("ascii", errors="strict")
        .strip()
    )
    if resolved_commit != source_commit:
        raise PackageError(
            "--source-commit no identifica exactamente el commit solicitado."
        )
    head_commit = (
        _git(source_root, "rev-parse", "HEAD").decode("ascii", errors="strict").strip()
    )
    if head_commit != source_commit:
        raise PackageError("--source-commit debe coincidir con HEAD.")
    status = _git(
        source_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status:
        raise PackageError("El árbol de trabajo debe estar limpio antes de empaquetar.")
    return source_root


def validate_marketplace(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"name", "interface", "plugins"}:
        raise PackageError("La plantilla de marketplace no respeta el contrato raíz.")
    if value.get("name") != "lks-sdd-development":
        raise PackageError(
            "El marketplace de desarrollo debe llamarse lks-sdd-development."
        )
    interface = value.get("interface")
    if (
        not isinstance(interface, dict)
        or interface.get("displayName") != "LKS-SDD Development"
    ):
        raise PackageError("Falta el displayName del marketplace.")
    plugins = value.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise PackageError("El marketplace debe contener exactamente LKS-SDD.")
    plugin = plugins[0]
    expected = {
        "name": "lks-sdd",
        "source": {"source": "local", "path": "./plugins/lks-sdd"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Developer Tools",
    }
    if plugin != expected:
        raise PackageError(
            "La entrada del marketplace no coincide con el contrato de Codex."
        )
    return value


def _read_git_blobs(root: Path, objects: list[tuple[str, str]]) -> dict[str, bytes]:
    if not objects:
        return {}
    requested = b"".join(f"{object_id}\n".encode("ascii") for _, object_id in objects)
    response = _git(root, "cat-file", "--batch", input_data=requested)
    position = 0
    contents: dict[str, bytes] = {}
    for relative, expected_id in objects:
        header_end = response.find(b"\n", position)
        if header_end < 0:
            raise PackageError("Git devolvió una respuesta de blobs incompleta.")
        header = response[position:header_end].decode("ascii", errors="strict").split()
        if len(header) != 3 or header[0] != expected_id or header[1] != "blob":
            raise PackageError(f"Git no devolvió el blob esperado para {relative}.")
        try:
            size = int(header[2])
        except ValueError as exc:
            raise PackageError(
                f"Git devolvió un tamaño inválido para {relative}."
            ) from exc
        start = header_end + 1
        end = start + size
        if end >= len(response) or response[end : end + 1] != b"\n":
            raise PackageError(f"Git devolvió contenido incompleto para {relative}.")
        contents[relative] = response[start:end]
        position = end + 1
    if position != len(response):
        raise PackageError("Git devolvió datos de blobs no solicitados.")
    return contents


def collect_source_files(root: Path, source_commit: str) -> list[tuple[str, bytes]]:
    tree = _git(root, "ls-tree", "-r", "-z", "--full-tree", source_commit)
    objects: list[tuple[str, str]] = []
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            relative_text = raw_path.decode("utf-8")
        except (UnicodeError, ValueError) as exc:
            raise PackageError(
                "El árbol Git contiene una entrada no interpretable."
            ) from exc
        relative = PurePosixPath(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise PackageError(f"Ruta Git insegura: {relative_text}")
        if EXCLUDED_PARTS.intersection(relative.parts) or relative.parts[:2] in {
            ("tests", "reports"),
            ("pilot", "runs"),
        }:
            continue
        if relative.suffix in {".pyc", ".pyo"}:
            continue
        if mode == "120000":
            raise PackageError(f"No se empaquetan enlaces: {relative_text}")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise PackageError(
                f"Tipo de entrada Git no soportado para el paquete: {relative_text} ({mode} {object_type})."
            )
        objects.append((relative.as_posix(), object_id))
    blob_contents = _read_git_blobs(root, objects)
    files: list[tuple[str, bytes]] = []
    for relative, _ in objects:
        content = blob_contents[relative]
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                raise PackageError(
                    f"Posible secreto o clave privada en {relative}; paquete bloqueado."
                )
        files.append((relative, content))
    files.sort(key=lambda item: item[0])
    required = {
        ".codex-plugin/plugin.json",
        "README.md",
        "SECURITY.md",
        "SUPPORT.md",
        "distribution/marketplace.template.json",
    }
    present = {relative for relative, _ in files}
    missing = sorted(required - present)
    if missing:
        raise PackageError(f"Faltan archivos obligatorios del paquete: {missing}")
    return files


def _validated_quality_report(
    path: Path,
    *,
    plugin_version: str,
    source_commit: str,
    build_date: str,
    committed_files: dict[str, bytes],
) -> tuple[dict[str, Any], bytes]:
    report_path = path.expanduser().resolve()
    if report_path.is_symlink() or (
        hasattr(report_path, "is_junction") and report_path.is_junction()
    ):
        raise PackageError("El reporte de calidad no puede ser un enlace.")
    try:
        content = report_path.read_bytes()
    except OSError as exc:
        raise PackageError(f"No se puede leer --quality-report: {exc}") from exc
    if len(content) > 10 * 1024 * 1024:
        raise PackageError("El reporte de calidad supera el límite de 10 MiB.")
    report = _load_json_bytes(content, str(report_path))
    schema = _committed_json(committed_files, "schemas/quality-report.schema.json")
    _assert_supported_quality_schema(schema)
    schema_errors = _quality_schema_errors(report, schema)
    if schema_errors:
        raise PackageError(
            "El reporte no cumple schemas/quality-report.schema.json: "
            + " | ".join(schema_errors[:10])
        )
    if not isinstance(report, dict):
        raise PackageError("El reporte de calidad debe ser un objeto JSON.")
    if report.get("plugin_version") != plugin_version:
        raise PackageError(
            "El reporte de calidad no corresponde a la versión empaquetada."
        )
    if report.get("evaluated_on") != build_date:
        raise PackageError("El reporte de calidad no corresponde a la fecha del build.")
    if report.get("channel") != "candidate":
        raise PackageError(
            "El empaquetado candidate requiere un reporte del canal candidate."
        )
    source = report.get("source")
    if not isinstance(source, dict) or source.get("commit") != source_commit:
        raise PackageError("El reporte de calidad no corresponde al commit fuente.")
    if source.get("tree_state") != "clean":
        raise PackageError(
            "El reporte de calidad debe acreditar un árbol fuente clean."
        )
    gate = report["gate"]
    catalog = _committed_json(committed_files, "quality/catalog.json")
    corpus = _committed_json(committed_files, "quality/corpora/activation.json")
    definition_corpus = _committed_json(
        committed_files, "quality/corpora/definition-v0.9.0.json"
    )
    fixture_manifest = _committed_json(
        committed_files, "quality/fixture-manifest.json"
    )
    baseline = _committed_json(
        committed_files, "quality/baselines/v0.6.1.json"
    )
    if (
        baseline.get("plugin_version") != "0.6.1"
        or baseline.get("source_commit") != EXPECTED_BASELINE_COMMIT
    ):
        raise PackageError("La baseline comprometida no es la release v0.6.1 esperada.")
    deterministic_eval_count = _validate_fixture_attestation(
        fixture_manifest, committed_files
    )
    inputs = report["inputs"]
    expected_input_hashes = {
        "catalog_sha256": _sha256(_canonical_json_bytes(catalog)),
        "corpus_sha256": _sha256(_canonical_json_bytes(corpus)),
        "definition_corpus_sha256": _sha256(
            _canonical_json_bytes(definition_corpus)
        ),
        "fixture_manifest_sha256": _sha256(
            committed_files["quality/fixture-manifest.json"]
        ),
        "baseline_sha256": _sha256(_canonical_json_bytes(baseline)),
    }
    if any(
        inputs.get(name) != digest
        for name, digest in expected_input_hashes.items()
    ):
        raise PackageError(
            "El reporte no está ligado por hash a todos los inputs comprometidos."
        )
    if inputs.get("observations_sha256") is not None or inputs.get(
        "pilot_summary_sha256"
    ) is not None:
        raise PackageError(
            "El candidate reproducible no admite observaciones o piloto externos."
        )
    if report.get("suite") != catalog.get("suite"):
        raise PackageError("El reporte no corresponde a la suite comprometida.")
    channel_catalog = catalog.get("channels")
    if not isinstance(channel_catalog, dict):
        raise PackageError("El catálogo comprometido no declara canales válidos.")
    candidate_channels = channel_catalog.get("candidate")
    if not isinstance(candidate_channels, dict):
        raise PackageError("El catálogo comprometido no declara candidate.")
    required_names = candidate_channels.get("required")
    optional_names = candidate_channels.get("optional")
    if (
        not isinstance(required_names, list)
        or set(required_names) != EXPECTED_CANDIDATE_REQUIRED_CHANNELS
        or len(required_names) != len(set(required_names))
        or not isinstance(optional_names, list)
        or set(optional_names) != EXPECTED_CANDIDATE_OPTIONAL_CHANNELS
        or len(optional_names) != len(set(optional_names))
    ):
        raise PackageError("El catálogo candidate comprometido reduce canales esperados.")
    checks = report["checks"]
    check_ids = [check["id"] for check in checks]
    if (
        len(check_ids) != len(set(check_ids))
        or set(check_ids) != EXPECTED_CANDIDATE_CHECKS
    ):
        raise PackageError(
            "El reporte no contiene el inventario exacto de checks candidate."
        )
    check_by_id = {check["id"]: check for check in checks}
    for check_id, check in check_by_id.items():
        expected_summary = (
            f"fixtures={len(fixture_manifest['fixtures'])}"
            if check_id == "fixture-integrity"
            else "exit=0"
        )
        if (
            check.get("status") != "passed"
            or check.get("critical") is not True
            or check.get("summary") != expected_summary
        ):
            raise PackageError(f"El check candidate no acredita éxito: {check_id}")
    channels = report["channels"]
    expected_channel_names = set(required_names) | set(optional_names)
    if set(channels) != expected_channel_names:
        raise PackageError("El reporte no contiene el inventario exacto de canales.")
    catalog_cases = catalog.get("cases")
    extension_cases = catalog.get("extension_cases")
    if not isinstance(catalog_cases, list) or not isinstance(extension_cases, list):
        raise PackageError("El catálogo comprometido no declara casos válidos.")
    catalog_ids = [
        case.get("id") for case in catalog_cases if isinstance(case, dict)
    ]
    extension_ids = [
        case.get("id") for case in extension_cases if isinstance(case, dict)
    ]
    if (
        len(catalog_ids) != len(catalog_cases)
        or not all(isinstance(case_id, str) for case_id in catalog_ids)
        or set(catalog_ids) != {f"FX-{index:02d}" for index in range(1, 20)}
        or len(catalog_ids) != len(set(catalog_ids))
        or len(extension_ids) != len(extension_cases)
        or not all(isinstance(case_id, str) for case_id in extension_ids)
        or set(extension_ids) != {f"FX-{index:02d}" for index in range(20, 36)}
        or len(extension_ids) != len(set(extension_ids))
    ):
        raise PackageError("El inventario comprometido de casos FX cambió.")
    automated_cases = [
        case
        for case in [*catalog_cases, *extension_cases]
        if isinstance(case, dict) and case.get("mode") == "automated"
    ]
    if tuple(case.get("id") for case in automated_cases) != EXPECTED_AUTOMATED_CASE_IDS:
        raise PackageError("El inventario comprometido de casos automatizados cambió.")
    automated = channels.get("automated")
    if not isinstance(automated, dict) or set(automated) != {
        "status",
        "counts",
        "cases",
        "critical_incomplete",
        "pending",
    }:
        raise PackageError("El canal automated no respeta el contrato del harness.")
    if (
        automated.get("status") != "passed"
        or automated.get("critical_incomplete") != []
        or automated.get("pending") != []
    ):
        raise PackageError("El canal automated no está completamente acreditado.")
    case_results = automated.get("cases")
    if not isinstance(case_results, list) or len(case_results) != len(automated_cases):
        raise PackageError("El canal automated no cubre todos los casos automatizados.")
    for expected_case, case_result in zip(automated_cases, case_results, strict=True):
        references = expected_case.get("evidence")
        if (
            not isinstance(expected_case.get("id"), str)
            or type(expected_case.get("critical")) is not bool
            or not isinstance(references, list)
            or not references
            or not all(
                isinstance(reference, str)
                and re.fullmatch(
                    r"(?:eval|test|profile):[A-Za-z0-9._-]+", reference
                )
                for reference in references
            )
        ):
            raise PackageError("El catálogo contiene evidencia automatizada inválida.")
        if not isinstance(case_result, dict) or set(case_result) != {
            "id",
            "critical",
            "status",
            "evidence",
        }:
            raise PackageError("Un caso automatizado no respeta el contrato del harness.")
        outcomes = case_result.get("evidence")
        if (
            case_result.get("id") != expected_case.get("id")
            or case_result.get("critical") is not expected_case.get("critical")
            or case_result.get("status") != "passed"
            or not isinstance(outcomes, list)
            or len(outcomes) != len(references)
        ):
            raise PackageError(
                f"Evidencia automatizada incompleta para {expected_case.get('id')}."
            )
        for reference, outcome in zip(references, outcomes, strict=True):
            if not isinstance(outcome, dict) or not {
                "reference",
                "status",
                "resolved_id",
            }.issubset(outcome):
                raise PackageError(f"Evidencia no resuelta: {reference}")
            if set(outcome) - {"reference", "status", "resolved_id", "reason"}:
                raise PackageError(f"Evidencia con campos no admitidos: {reference}")
            if (
                outcome.get("reference") != reference
                or outcome.get("status") != "passed"
                or outcome.get("reason") not in {None}
            ):
                raise PackageError(f"Evidencia no superada: {reference}")
            kind, evidence_id = reference.split(":", 1)
            resolved_id = outcome.get("resolved_id")
            resolved = isinstance(resolved_id, str) and (
                (kind == "test" and resolved_id.rsplit(".", 1)[-1] == evidence_id)
                or (kind == "eval" and resolved_id == evidence_id)
                or (kind == "profile" and resolved_id == "complete-gate")
            )
            if not resolved:
                raise PackageError(
                    f"Evidencia resuelta contra otro resultado: {reference}"
                )
    expected_automated_total = len(automated_cases)
    if automated.get("counts") != {
        "total": expected_automated_total,
        "passed": expected_automated_total,
        "failed": 0,
        "incomplete": 0,
    }:
        raise PackageError("Los totales del canal automated no son consistentes.")
    if channels.get("fixture-integrity") != check_by_id["fixture-integrity"]:
        raise PackageError("El canal fixture-integrity no coincide con su check.")
    if channels.get("profile-complete") != {"status": "passed"}:
        raise PackageError("El canal profile-complete no quedó superado.")
    if channels.get("regression") != {"status": "passed"}:
        raise PackageError("El canal regression no quedó superado.")
    expected_optional_channels = {
        "definition-conversation": {
            "status": "not-run",
            "observed": 0,
            "total": len(definition_corpus.get("cases", [])),
            "corpus_id": definition_corpus.get("corpus_id"),
            "required_review": definition_corpus.get("evaluation", {}).get(
                "required_review"
            ),
        },
        "activation": {
            "status": "not-run",
            "observed": 0,
            "total": len(corpus.get("cases", [])),
        },
        "document-review": {"status": "not-run", "reviewed": 0},
        "pilot": {"status": "not-run", "decision": "not-evaluated"},
    }
    if any(
        channels.get(name) != expected
        for name, expected in expected_optional_channels.items()
    ):
        raise PackageError("Los canales opcionales no reflejan su estado not-run real.")
    metrics = report["metrics"]
    if set(metrics) != EXPECTED_RELEASE_METRICS:
        raise PackageError("El reporte no contiene el inventario exacto de métricas.")
    integer_metrics = EXPECTED_RELEASE_METRICS - {"automated_eval_pass_rate"}
    if any(
        not _matches_json_type(metrics[name], "integer") for name in integer_metrics
    ):
        raise PackageError("Las métricas de conteo deben ser enteros finitos.")
    if not _matches_json_type(metrics["automated_eval_pass_rate"], "number"):
        raise PackageError("La tasa de evals debe ser un número finito.")
    if (
        metrics["unit_tests_total"] < 1
        or metrics["unit_tests_passed"] < 1
        or metrics["unit_tests_failed"] != 0
        or metrics["unit_tests_executed"]
        != metrics["unit_tests_passed"] + metrics["unit_tests_failed"]
        or metrics["unit_tests_total"]
        != metrics["unit_tests_passed"]
        + metrics["unit_tests_skipped"]
        + metrics["unit_tests_failed"]
        or metrics["automated_eval_cases"] != deterministic_eval_count
        or metrics["automated_eval_pass_rate"] != 1
        or metrics["profile_structure_gate"] != 1
        or metrics["profile_complete_gate"] != 1
        or metrics["automated_catalog_cases"] != expected_automated_total
        or metrics["automated_catalog_cases_passed"] != expected_automated_total
        or metrics["automated_catalog_cases_failed"] != 0
        or metrics["automated_catalog_cases_incomplete"] != 0
        or metrics["critical_failures"] != 0
    ):
        raise PackageError("Las métricas del reporte no son internamente consistentes.")
    if report.get("critical_failures") != []:
        raise PackageError("El reporte de calidad contiene fallos críticos.")
    comparison = report["comparison"]
    expected_comparison = _expected_comparison(metrics, baseline)
    if comparison != expected_comparison or comparison.get("status") != "passed":
        raise PackageError(
            "El reporte no acredita una comparación reproducible con v0.6.1."
        )
    if gate != {
        "status": "passed",
        "eligible": True,
        "blockers": [],
        "missing_evidence": [],
    }:
        raise PackageError("El gate candidate no es consistente con su evidencia.")
    return report, content


def _zip_bytes(
    entries: list[tuple[str, bytes]], timestamp: tuple[int, int, int, int, int, int]
) -> bytes:
    handle, temporary_name = tempfile.mkstemp(prefix="lks-sdd-package-", suffix=".zip")
    os.close(handle)
    try:
        with zipfile.ZipFile(
            temporary_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, content in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=timestamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
                )
        return Path(temporary_name).read_bytes()
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def build(
    output: Path,
    build_date: str,
    source_commit: str,
    source_root: Path = PLUGIN_ROOT,
    quality_report: Path | None = None,
) -> dict[str, Any]:
    try:
        parsed_date = date.fromisoformat(build_date)
    except ValueError as exc:
        raise PackageError("--date debe usar YYYY-MM-DD.") from exc
    source_root = _validate_source_checkout(source_root, source_commit)
    files = collect_source_files(source_root, source_commit)
    committed_files = dict(files)
    manifest = _load_json_bytes(
        committed_files[".codex-plugin/plugin.json"], ".codex-plugin/plugin.json"
    )
    plugin_version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(plugin_version, str) or not SEMVER_RE.fullmatch(plugin_version):
        raise PackageError(
            "El manifest debe declarar una versión SemVer válida antes de empaquetar."
        )
    if quality_report is None:
        raise PackageError("El empaquetado requiere --quality-report.")
    quality, quality_bytes = _validated_quality_report(
        quality_report,
        plugin_version=plugin_version,
        source_commit=source_commit,
        build_date=build_date,
        committed_files=committed_files,
    )
    marketplace = validate_marketplace(
        _load_json_bytes(
            committed_files["distribution/marketplace.template.json"],
            "distribution/marketplace.template.json",
        )
    )
    output = _safe_output(output, source_root)
    timestamp = (parsed_date.year, parsed_date.month, parsed_date.day, 0, 0, 0)
    plugin_entries = [(f"lks-sdd/{relative}", content) for relative, content in files]
    marketplace_bytes = (
        json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    marketplace_entries = [
        (".agents/plugins/marketplace.json", marketplace_bytes),
        *[(f"plugins/lks-sdd/{relative}", content) for relative, content in files],
    ]
    plugin_zip = _zip_bytes(plugin_entries, timestamp)
    marketplace_zip = _zip_bytes(marketplace_entries, timestamp)
    plugin_name = f"lks-sdd-plugin-v{plugin_version}.zip"
    marketplace_name = f"lks-sdd-marketplace-v{plugin_version}.zip"
    release_manifest = {
        "schema_version": "1.0",
        "plugin_version": plugin_version,
        "source_commit": source_commit,
        "built_on": build_date,
        "source_file_count": len(files),
        "source_files": [
            {"path": relative, "sha256": _sha256(content), "size": len(content)}
            for relative, content in files
        ],
        "artifacts": [
            {
                "path": plugin_name,
                "sha256": _sha256(plugin_zip),
                "size": len(plugin_zip),
            },
            {
                "path": marketplace_name,
                "sha256": _sha256(marketplace_zip),
                "size": len(marketplace_zip),
            },
            {
                "path": QUALITY_REPORT_NAME,
                "sha256": _sha256(quality_bytes),
                "size": len(quality_bytes),
            },
        ],
        "quality": {
            "gate": quality["gate"]["status"],
            "baseline_commit": quality["comparison"]["baseline_commit"],
            "report_sha256": _sha256(quality_bytes),
        },
        "marketplace": marketplace,
    }
    output.mkdir(parents=True)
    (output / plugin_name).write_bytes(plugin_zip)
    (output / marketplace_name).write_bytes(marketplace_zip)
    (output / QUALITY_REPORT_NAME).write_bytes(quality_bytes)
    manifest_bytes = (
        json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    (output / "release-manifest.json").write_bytes(manifest_bytes)
    checksums = (
        "\n".join(
            [
                *(
                    f"{artifact['sha256']}  {artifact['path']}"
                    for artifact in release_manifest["artifacts"]
                ),
                f"{_sha256(manifest_bytes)}  release-manifest.json",
            ]
        )
        + "\n"
    )
    (output / "SHA256SUMS").write_text(checksums, encoding="utf-8", newline="\n")
    return {
        "status": "built",
        "plugin_version": plugin_version,
        "output": str(output),
        "source_file_count": len(files),
        "artifacts": release_manifest["artifacts"],
        "manifest_sha256": _sha256(manifest_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat(), dest="build_date")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--quality-report", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(
            args.output,
            args.build_date,
            args.source_commit,
            quality_report=args.quality_report,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (PackageError, OSError, zipfile.BadZipFile) as exc:
        print(
            json.dumps(
                {"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
