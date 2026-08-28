#!/usr/bin/env python3
"""Validate an LKS-SDD project index and its essential Markdown contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zlib
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from contract_engine import Diagnostic, build_project_model, legacy_messages
from evidence_contract import (
    evidence_gate_applicability_errors,
    evidence_profile_identity_errors,
    visual_gate_applicability,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCHEMAS = {
    "1.0": PLUGIN_ROOT / "schemas" / "project.schema.json",
    "1.1": PLUGIN_ROOT / "schemas" / "project-1.1.schema.json",
    "1.2": PLUGIN_ROOT / "schemas" / "project-1.2.schema.json",
    "1.3": PLUGIN_ROOT / "schemas" / "project-1.3.schema.json",
    "1.4": PLUGIN_ROOT / "schemas" / "project-1.4.schema.json",
    "1.5": PLUGIN_ROOT / "schemas" / "project-1.5.schema.json",
}
FRONTMATTER_SCHEMAS = {
    "1.0": PLUGIN_ROOT / "schemas" / "frontmatter.schema.json",
    "1.1": PLUGIN_ROOT / "schemas" / "frontmatter-1.1.schema.json",
    "1.2": PLUGIN_ROOT / "schemas" / "frontmatter-1.2.schema.json",
    "1.3": PLUGIN_ROOT / "schemas" / "frontmatter-1.3.schema.json",
    "1.4": PLUGIN_ROOT / "schemas" / "frontmatter-1.4.schema.json",
    "1.5": PLUGIN_ROOT / "schemas" / "frontmatter-1.5.schema.json",
}
CATALOGS = json.loads(
    (PLUGIN_ROOT / "schemas" / "catalogs.json").read_text(encoding="utf-8")
)
DOCUMENT_CONTRACTS = json.loads(
    (PLUGIN_ROOT / "schemas" / "document-contracts.json").read_text(encoding="utf-8")
)
ALL_ID_PREFIXES = set(CATALOGS["identifier_prefixes"]) | set(
    DOCUMENT_CONTRACTS["identifier_prefixes"]
)
TRACKING_ID_PREFIXES = {"TRK", "SYNC"}
V15_ONLY_ID_PREFIXES = {"RPT"}


def _id_re_for_schema(schema_version: str) -> re.Pattern[str]:
    prefixes = set(ALL_ID_PREFIXES)
    if schema_version not in {"1.4", "1.5"}:
        prefixes -= TRACKING_ID_PREFIXES
    if schema_version != "1.5":
        prefixes -= V15_ONLY_ID_PREFIXES
    pattern = "|".join(re.escape(prefix) for prefix in sorted(prefixes))
    return re.compile(rf"\b(?:{pattern})-[0-9]{{3}}\b")


ID_RE = _id_re_for_schema("1.5")
VALID_ELEMENT_STATES = set(CATALOGS["element_states"])
V14_ONLY_ELEMENT_STATES = {
    "unlinked",
    "synced",
    "out-of-sync",
    "conflict",
    "failed",
    "reconciliation-required",
    "recorded",
}
CORE_ARTIFACTS = {
    "ART-STATUS": ("docs/lks-sdd/00-control/project-status.md", "project-status"),
    "ART-SCOPE": ("docs/lks-sdd/00-control/scope-register.md", "scope-register"),
    "ART-OPEN": ("docs/lks-sdd/00-control/open-points.md", "open-points"),
    "ART-BRIEF": ("docs/lks-sdd/01-context/product-brief.md", "product-brief"),
    "ART-CONSTRAINTS": ("docs/lks-sdd/01-context/constraints.md", "constraints"),
    "ART-FR": (
        "docs/lks-sdd/02-requirements/functional-requirements.md",
        "functional-requirements",
    ),
    "ART-NFR": (
        "docs/lks-sdd/02-requirements/non-functional-requirements.md",
        "non-functional-requirements",
    ),
    "ART-TR": (
        "docs/lks-sdd/02-requirements/technical-requirements.md",
        "technical-requirements",
    ),
    "ART-AC": (
        "docs/lks-sdd/02-requirements/acceptance-criteria.md",
        "acceptance-criteria",
    ),
    "ART-SOLUTION": (
        "docs/lks-sdd/03-solution/solution-overview.md",
        "solution-overview",
    ),
    "ART-ARCH": ("docs/lks-sdd/03-solution/architecture.md", "architecture"),
    "ART-INCREMENTS": ("docs/lks-sdd/04-delivery/increments.md", "increments"),
    "ART-GOVERNANCE": (
        "docs/lks-sdd/04-delivery/delivery-governance.md",
        "delivery-governance",
    ),
    "ART-PLANS": ("docs/lks-sdd/04-delivery/plans.md", "delivery-plans"),
    "ART-TASKS": (
        "docs/lks-sdd/04-delivery/tasks.md",
        "development-task-board",
    ),
    "ART-PLANNING": (
        "docs/lks-sdd/04-delivery/planning-coverage.md",
        "planning-coverage",
    ),
    "ART-TRACKING": (
        "docs/lks-sdd/04-delivery/task-tracking.md",
        "task-tracking",
    ),
    "ART-RISK": (
        "docs/lks-sdd/04-delivery/risks-dependencies.md",
        "risks-dependencies",
    ),
    "ART-QUALITY": ("docs/lks-sdd/05-quality/quality-strategy.md", "quality-strategy"),
    "ART-TEST-STRATEGY": (
        "docs/lks-sdd/05-quality/test-strategy.md",
        "test-strategy",
    ),
    "ART-TRACE": ("docs/lks-sdd/05-quality/traceability.md", "traceability"),
    "ART-DEPLOYMENT": (
        "docs/lks-sdd/06-operation/deployment.md",
        "deployment",
    ),
}
V12_CORE_ARTIFACTS = {
    "ART-ARCH",
    "ART-GOVERNANCE",
    "ART-PLANS",
    "ART-TASKS",
    "ART-TEST-STRATEGY",
    "ART-DEPLOYMENT",
}
V13_CORE_ARTIFACTS = {"ART-PLANNING"}
V14_CORE_ARTIFACTS = {"ART-TRACKING"}
ADOPTION_ARTIFACTS = {
    "ART-ADOPT-SCOPE": (
        "docs/lks-sdd/07-adoption/inspection-scope.md",
        "inspection-scope",
    ),
    "ART-ADOPT-INVENTORY": (
        "docs/lks-sdd/07-adoption/repository-inventory.md",
        "repository-inventory",
    ),
    "ART-ADOPT-ARCHITECTURE": (
        "docs/lks-sdd/07-adoption/observed-architecture.md",
        "observed-architecture",
    ),
    "ART-ADOPT-BEHAVIOR": (
        "docs/lks-sdd/07-adoption/observed-behavior.md",
        "observed-behavior",
    ),
    "ART-ADOPT-GAPS": (
        "docs/lks-sdd/07-adoption/gaps-and-unknowns.md",
        "gaps-and-unknowns",
    ),
    "ART-ADOPT-RECONCILIATION": (
        "docs/lks-sdd/07-adoption/reconciliation.md",
        "reconciliation",
    ),
    "ART-ADOPT-STRATEGY": (
        "docs/lks-sdd/07-adoption/adoption-strategy.md",
        "adoption-strategy",
    ),
    "ART-ADOPT-BASELINE": (
        "docs/lks-sdd/07-adoption/baseline-record.md",
        "baseline-record",
    ),
}
REQUIRED_TABLE_HEADERS = {
    "ART-STATUS": [
        ("Ruta", "Fase", "Puerta", "Incremento activo", "Readiness", "Próximo paso")
    ],
    "ART-OPEN": [("ID", "State", "Question", "Impact", "Scope", "Blocking")],
    "ART-CONSTRAINTS": [("ID", "State", "Type", "Statement", "Source", "Impact")],
    "ART-FR": [
        ("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")
    ],
    "ART-NFR": [
        ("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")
    ],
    "ART-TR": [
        ("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")
    ],
    "ART-AC": [("ID", "State", "Condition", "Requirement", "Evidence")],
    "ART-SOLUTION": [
        ("ID", "State", "Option", "Support", "Fit", "Risks", "Alternative"),
        ("ID", "State", "Decision", "Requirements", "Impact"),
    ],
    "ART-INCREMENTS": [
        (
            "ID",
            "State",
            "In scope",
            "Out of scope",
            "Requirements",
            "Acceptance",
            "Decisions",
            "Data",
            "Identity",
            "Integrations",
            "Tests",
        )
    ],
    "ART-RISK": [
        ("ID", "State", "Description", "Scope", "Impact", "Treatment", "Owner")
    ],
    "ART-QUALITY": [("ID", "State", "Purpose", "Increment", "Acceptance")],
    "ART-TRACE": [
        ("Requirement", "Acceptance", "Decision", "Increment", "Test", "Evidence")
    ],
}

DEFINITION_COVERAGE_HEADERS = (
    "Dimensión",
    "Estado",
    "Alcance",
    "Información disponible",
    "Falta profundizar",
    "Impacto",
)
INTERFACE_CONTRACT_HEADERS = (
    "Increment",
    "Interface applicability",
    "UX contract",
    "Visual mode",
    "Visual prototype",
    "Reason",
)
UX_SCREEN_HEADERS = (
    "ID",
    "State",
    "Screen",
    "Purpose",
    "Users",
    "Content",
    "Main actions",
    "Requirements",
    "Acceptance",
    "Increment",
)
UX_SCREEN_DETAIL_HEADERS = (
    "Screen",
    "Entry and exit",
    "Information hierarchy",
    "Secondary actions",
    "Permissions and role variants",
    "Responsive and priority devices",
    "Accessibility",
    "Pending content",
)
UX_SCREEN_STATE_HEADERS = (
    "Screen",
    "Loading",
    "Empty",
    "Error",
    "No permission",
    "Confirmation",
    "Recovery",
)
UX_FLOW_HEADERS = (
    "ID",
    "State",
    "Flow or interaction",
    "User",
    "Screens",
    "Entry or trigger",
    "Expected steps or response",
    "Alternate, error or recovery path",
    "Dialog or confirmation",
    "Accessibility",
    "Acceptance",
    "Increment",
)
UX_DIRECTION_HEADERS = (
    "ID",
    "State",
    "Aspect",
    "Proposal",
    "Rationale",
    "Constraints",
    "Human validation",
    "Decision",
    "Increment",
)
VISUAL_PROTOTYPE_HEADERS = (
    "ID",
    "State",
    "Asset",
    "Format",
    "Viewport",
    "Screens or flow",
    "Requirements",
    "Source",
    "Generated on",
    "Prompt or brief",
    "SHA-256",
    "Human validation",
    "Confirmation scope",
    "Limitations",
    "Decision",
    "Increment",
)
UX_REQUIRED_HEADERS = {
    UX_SCREEN_HEADERS,
    UX_SCREEN_DETAIL_HEADERS,
    UX_SCREEN_STATE_HEADERS,
    UX_FLOW_HEADERS,
    UX_DIRECTION_HEADERS,
    VISUAL_PROTOTYPE_HEADERS,
}
VISUAL_MODES = {"pending", "new", "material-change", "reuse", "none"}
VISUAL_ASSET_ROOT = Path("docs/lks-sdd/03-solution/ui-prototypes")
MARKDOWN_IMAGE_RE = re.compile(r"^!\[([^\]]+)\]\(([^)]+)\)$")
MAX_IMAGE_FILE_BYTES = 50 * 1024 * 1024
MAX_DECODED_IMAGE_BYTES = 200 * 1024 * 1024
IMPLEMENTATION_SCOPE_ROOTS = ("apps", "packages", "services", "src", "lib", "tests")
IMPLEMENTATION_IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}
MAX_IMPLEMENTATION_SCOPE_FILES = 50_000


@dataclass
class ValidationReport:
    project_root: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_files: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "project_root": self.project_root,
            "errors": self.errors,
            "warnings": self.warnings,
            "checked_files": self.checked_files,
            "diagnostics": self.diagnostics,
        }


def _legacy_error_backing_diagnostic(
    diagnostic: Diagnostic, legacy_errors: list[str]
) -> int | None:
    """Return the legacy error index that independently confirms a diagnostic."""

    if diagnostic.code == "LKS-REF-UNDEFINED" and isinstance(
        diagnostic.observed, str
    ):
        marker = f"referencia sin definición: {diagnostic.observed}"
        for index, error in enumerate(legacy_errors):
            if marker in error and (
                diagnostic.location.path is None
                or error.startswith(f"{diagnostic.location.path}:")
            ):
                return index
    return None


def _matches_type(value: Any, expected: str) -> bool:
    mapping = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: type(item) is bool,
        "null": lambda item: item is None,
        "number": lambda item: (
            isinstance(item, (int, float)) and type(item) is not bool
        ),
        "integer": lambda item: isinstance(item, int) and type(item) is not bool,
    }
    return expected in mapping and mapping[expected](value)


def validate_json_schema(
    value: Any, schema: dict[str, Any], location: str = "$"
) -> list[str]:
    """Validate the JSON Schema subset used by this plugin without dependencies."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, option) for option in options):
            return [f"{location}: tipo inválido; se esperaba {options}."]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: debe ser {schema['const']!r}.")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: valor {value!r} fuera del catálogo permitido.")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: texto demasiado corto.")
        pattern = schema.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            errors.append(f"{location}: no cumple el patrón {pattern!r}.")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: contiene menos elementos de los requeridos.")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{location}: contiene más elementos de los permitidos.")
        if schema.get("uniqueItems") is True:
            encoded_items = [
                json.dumps(item, sort_keys=True, ensure_ascii=True) for item in value
            ]
            if len(encoded_items) != len(set(encoded_items)):
                errors.append(f"{location}: contiene elementos duplicados.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(
                    validate_json_schema(item, item_schema, f"{location}[{index}]")
                )

    if isinstance(value, dict):
        required = schema.get("required", [])
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
                    validate_json_schema(value[key], child_schema, f"{location}.{key}")
                )
    return errors


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("falta el delimitador inicial de front matter")
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("falta el delimitador final de front matter") from exc

    data: dict[str, Any] = {}
    list_key: str | None = None
    for line_number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if list_key is None or not isinstance(data.get(list_key), list):
                raise ValueError(f"lista sin clave en la línea {line_number}")
            data[list_key].append(_parse_scalar(line[4:]))
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"sintaxis no soportada en la línea {line_number}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"clave vacía en la línea {line_number}")
        if raw.strip():
            data[key] = _parse_scalar(raw)
            list_key = None
        else:
            data[key] = []
            list_key = key
    return data, "\n".join(lines[end + 1 :]).strip()


def parse_markdown_table_blocks(
    body: str,
) -> list[tuple[tuple[str, ...], list[dict[str, str]]]]:
    lines = body.splitlines()
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and separator_line.startswith("|")):
            index += 1
            continue
        headers = [cell.strip() for cell in header_line.strip("|").split("|")]
        separators = [cell.strip() for cell in separator_line.strip("|").split("|")]
        if len(headers) != len(separators) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            index += 1
            continue
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [
                cell.strip() for cell in lines[index].strip().strip("|").split("|")
            ]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            index += 1
        tables.append((tuple(headers), rows))
    return tables


def parse_markdown_tables(body: str) -> list[list[dict[str, str]]]:
    return [rows for _, rows in parse_markdown_table_blocks(body)]


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _safe_relative_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, f"ruta no permitida: {relative}"
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"ruta fuera de la raíz: {relative}"
    current = root
    for part in candidate.parts:
        current = current / part
        if _is_link_like(current):
            return None, f"la ruta usa un enlace simbólico o junction: {relative}"
    return resolved, None


def plugin_version_at_least(value: Any, minimum: tuple[int, int, int]) -> bool:
    """Compare the numeric core of a plugin semantic version."""
    if not isinstance(value, str):
        return False
    match = re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?",
        value,
    )
    if not match:
        return False
    return tuple(int(match.group(index)) for index in range(1, 4)) >= minimum


def v06_contract_applies(
    manifest: dict[str, Any], metadata: dict[str, Any] | None = None
) -> bool:
    """A 0.6 project cannot opt out through one downgraded Markdown header."""
    return plugin_version_at_least(manifest.get("plugin_version"), (0, 6, 0)) or (
        metadata is not None
        and plugin_version_at_least(
            metadata.get("created_with_plugin_version"), (0, 6, 0)
        )
    )


def table_rows_for_headers(
    table_blocks: list[tuple[tuple[str, ...], list[dict[str, str]]]],
    headers: tuple[str, ...],
) -> list[dict[str, str]] | None:
    matching = [rows for actual, rows in table_blocks if actual == headers]
    if len(matching) != 1:
        return None
    return matching[0]


def document_table_contract(
    artifact_id: str, headers: tuple[str, ...], schema_version: str
) -> dict[str, Any] | None:
    """Resolve one declared table contract for schema-aware parsing."""
    artifact = DOCUMENT_CONTRACTS.get("artifacts", {}).get(artifact_id, {})
    contracts = artifact.get("tables", [])
    effective_schema = schema_version
    inheritance = DOCUMENT_CONTRACTS.get("schema_inheritance", {})
    visited: set[str] = set()
    while not any(
        effective_schema in contract.get("schemas", []) for contract in contracts
    ):
        if effective_schema in visited or effective_schema not in inheritance:
            break
        visited.add(effective_schema)
        effective_schema = inheritance[effective_schema]
    for contract in contracts:
        if (
            effective_schema in contract.get("schemas", [])
            and tuple(contract.get("headers", [])) == headers
        ):
            return contract
    return None


def interface_applicability(value: str) -> tuple[str | None, str | None]:
    """Normalize the compatible interface applicability spellings."""
    raw = (value or "").strip()
    lowered = raw.casefold()
    if lowered in {"applicable", "pending"}:
        return lowered, None
    if lowered == "not-applicable":
        return "not-applicable", None
    if lowered.startswith("not-applicable:"):
        reason = raw.split(":", 1)[1].strip()
        return "not-applicable", reason or None
    return None, None


def _markdown_image_target(value: str) -> tuple[str | None, str | None]:
    match = MARKDOWN_IMAGE_RE.fullmatch((value or "").strip())
    if not match:
        return None, "Asset debe ser un enlace de imagen Markdown ![texto](ruta)."
    alt_text, target = match.groups()
    if not alt_text.strip():
        return None, "El enlace de imagen necesita texto alternativo."
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None, "El asset visual debe usar una ruta local relativa."
    if any(character in target for character in ("?", "#", "%")):
        return None, "La ruta del asset no puede contener query, fragmento ni escapes URL."
    return target.replace("\\", "/"), None


def _png_expected_decoded_size(
    width: int, height: int, bit_depth: int, color_type: int, interlace: int
) -> int | None:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    valid_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if color_type not in channels or bit_depth not in valid_depths[color_type]:
        return None
    bits_per_pixel = channels[color_type] * bit_depth

    def pass_size(pass_width: int, pass_height: int) -> int:
        if pass_width <= 0 or pass_height <= 0:
            return 0
        row_bytes = (pass_width * bits_per_pixel + 7) // 8
        return pass_height * (1 + row_bytes)

    if interlace == 0:
        return pass_size(width, height)
    if interlace != 1:
        return None
    total = 0
    for x_start, y_start, x_step, y_step in (
        (0, 0, 8, 8),
        (4, 0, 8, 8),
        (0, 4, 4, 8),
        (2, 0, 4, 4),
        (0, 2, 2, 4),
        (1, 0, 2, 2),
        (0, 1, 1, 2),
    ):
        pass_width = max(0, (width - x_start + x_step - 1) // x_step)
        pass_height = max(0, (height - y_start + y_step - 1) // y_step)
        total += pass_size(pass_width, pass_height)
    return total


def _png_filter_bytes_valid(
    decoded: bytes,
    width: int,
    height: int,
    bit_depth: int,
    color_type: int,
    interlace: int,
) -> bool:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    bits_per_pixel = channels[color_type] * bit_depth
    passes = (
        [(width, height)]
        if interlace == 0
        else [
            (
                max(0, (width - x_start + x_step - 1) // x_step),
                max(0, (height - y_start + y_step - 1) // y_step),
            )
            for x_start, y_start, x_step, y_step in (
                (0, 0, 8, 8),
                (4, 0, 8, 8),
                (0, 4, 4, 8),
                (2, 0, 4, 4),
                (0, 2, 2, 4),
                (1, 0, 2, 2),
                (0, 1, 1, 2),
            )
        ]
    )
    offset = 0
    for pass_width, pass_height in passes:
        if pass_width <= 0 or pass_height <= 0:
            continue
        row_bytes = (pass_width * bits_per_pixel + 7) // 8
        for _ in range(pass_height):
            if offset >= len(decoded) or decoded[offset] > 4:
                return False
            offset += 1 + row_bytes
    return offset == len(decoded)


def _jpeg_structure(data: bytes) -> tuple[int, int] | None:
    """Validate the marker, table, frame and scan structure of a common JPEG."""
    if (
        len(data) < 8
        or not data.startswith(b"\xff\xd8\xff")
        or not data.endswith(b"\xff\xd9")
    ):
        return None

    quantization_tables: set[int] = set()
    huffman_tables: set[tuple[int, int]] = set()
    frame_components: dict[int, int] = {}
    frame_marker: int | None = None
    width = height = 0
    seen_scan = seen_entropy = seen_eoi = False
    index = 2

    while index < len(data):
        if data[index] != 0xFF:
            return None
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            return None
        marker = data[index]
        index += 1
        if marker == 0xD9:
            seen_eoi = index == len(data)
            break
        if marker in {0x00, 0xD8} or 0xD0 <= marker <= 0xD7:
            return None
        if marker == 0x01:
            continue
        if index + 2 > len(data):
            return None
        length = int.from_bytes(data[index : index + 2], "big")
        segment_end = index + length
        if length < 2 or segment_end > len(data):
            return None
        payload = data[index + 2 : segment_end]

        if marker == 0xDB:  # Define quantization tables.
            offset = 0
            while offset < len(payload):
                table_spec = payload[offset]
                offset += 1
                precision, table_id = table_spec >> 4, table_spec & 0x0F
                if precision not in {0, 1} or table_id > 3:
                    return None
                table_bytes = 64 * (precision + 1)
                if offset + table_bytes > len(payload):
                    return None
                values = payload[offset : offset + table_bytes]
                step = precision + 1
                if any(
                    int.from_bytes(values[position : position + step], "big") == 0
                    for position in range(0, len(values), step)
                ):
                    return None
                quantization_tables.add(table_id)
                offset += table_bytes
            if offset == 0:
                return None

        elif marker == 0xC4:  # Define Huffman tables.
            offset = 0
            while offset < len(payload):
                if offset + 17 > len(payload):
                    return None
                table_spec = payload[offset]
                table_class, table_id = table_spec >> 4, table_spec & 0x0F
                if table_class not in {0, 1} or table_id > 3:
                    return None
                counts = payload[offset + 1 : offset + 17]
                symbol_count = sum(counts)
                if symbol_count == 0 or symbol_count > 256:
                    return None
                available_codes = 1
                for count in counts:
                    available_codes = available_codes * 2 - count
                    if available_codes < 0:
                        return None
                symbols_start = offset + 17
                symbols_end = symbols_start + symbol_count
                if symbols_end > len(payload):
                    return None
                symbols = payload[symbols_start:symbols_end]
                if len(set(symbols)) != len(symbols):
                    return None
                huffman_tables.add((table_class, table_id))
                offset = symbols_end
            if offset == 0:
                return None

        elif marker in {0xC0, 0xC1, 0xC2}:  # Baseline/extended/progressive DCT.
            if frame_marker is not None or len(payload) < 9:
                return None
            precision = payload[0]
            height = int.from_bytes(payload[1:3], "big")
            width = int.from_bytes(payload[3:5], "big")
            component_count = payload[5]
            if (
                precision not in {8, 12}
                or not width
                or not height
                or component_count not in {1, 3, 4}
                or len(payload) != 6 + 3 * component_count
            ):
                return None
            for offset in range(6, len(payload), 3):
                component_id = payload[offset]
                sampling = payload[offset + 1]
                table_id = payload[offset + 2]
                horizontal, vertical = sampling >> 4, sampling & 0x0F
                if (
                    component_id in frame_components
                    or horizontal not in {1, 2, 3, 4}
                    or vertical not in {1, 2, 3, 4}
                    or table_id > 3
                ):
                    return None
                frame_components[component_id] = table_id
            frame_marker = marker

        elif marker == 0xDA:  # Start of scan.
            if frame_marker is None or len(payload) < 6:
                return None
            scan_components = payload[0]
            if (
                scan_components == 0
                or scan_components > len(frame_components)
                or len(payload) != 4 + 2 * scan_components
            ):
                return None
            selected_components: set[int] = set()
            selected_tables: list[tuple[int, int]] = []
            for offset in range(1, 1 + 2 * scan_components, 2):
                component_id = payload[offset]
                selectors = payload[offset + 1]
                dc_table, ac_table = selectors >> 4, selectors & 0x0F
                if (
                    component_id not in frame_components
                    or component_id in selected_components
                    or dc_table > 3
                    or ac_table > 3
                ):
                    return None
                selected_components.add(component_id)
                selected_tables.append((dc_table, ac_table))
            spectral_start, spectral_end, approximation = payload[-3:]
            high, low = approximation >> 4, approximation & 0x0F
            if frame_marker in {0xC0, 0xC1}:
                if (spectral_start, spectral_end, high, low) != (0, 63, 0, 0):
                    return None
            elif (
                spectral_start > spectral_end
                or spectral_end > 63
                or (spectral_start == 0 and spectral_end != 0)
                or (spectral_start > 0 and scan_components != 1)
                or high > 13
                or low > 13
                or (high != 0 and high != low + 1)
            ):
                return None
            for dc_table, ac_table in selected_tables:
                if spectral_start == 0 and (0, dc_table) not in huffman_tables:
                    return None
                if spectral_start > 0 and (1, ac_table) not in huffman_tables:
                    return None

            seen_scan = True
            scan_start = segment_end
            index = scan_start
            entropy_bytes = 0
            while index < len(data):
                if data[index] != 0xFF:
                    entropy_bytes += 1
                    index += 1
                    continue
                marker_start = index
                while index < len(data) and data[index] == 0xFF:
                    index += 1
                if index >= len(data):
                    return None
                scan_marker = data[index]
                if scan_marker == 0x00:
                    entropy_bytes += 1
                    index += 1
                    continue
                if 0xD0 <= scan_marker <= 0xD7:
                    index += 1
                    continue
                if entropy_bytes == 0 or marker_start == scan_start:
                    return None
                seen_entropy = True
                index = marker_start
                break
            continue

        elif 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC}:
            # Reject unsupported arithmetic/lossless frame families instead of
            # pretending that their entropy stream was decoded.
            return None

        index = segment_end

    if (
        frame_marker is None
        or not quantization_tables
        or not huffman_tables
        or not seen_scan
        or not seen_entropy
        or not seen_eoi
        or not set(frame_components.values()).issubset(quantization_tables)
    ):
        return None
    return width, height


def _image_signature(path: Path) -> tuple[str | None, tuple[int, int] | None]:
    """Validate a bounded PNG/JPEG structure and return its real dimensions."""
    try:
        data = path.read_bytes()
    except OSError:
        return None, None
    if not data or len(data) > MAX_IMAGE_FILE_BYTES:
        return None, None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        offset = 8
        width = height = bit_depth = color_type = interlace = 0
        chunks = 0
        idat_parts: list[bytes] = []
        seen_ihdr = seen_idat = seen_iend = seen_plte = False
        idat_ended = False
        while offset + 12 <= len(data):
            length = int.from_bytes(data[offset : offset + 4], "big")
            chunk_type = data[offset + 4 : offset + 8]
            payload_start = offset + 8
            payload_end = payload_start + length
            crc_end = payload_end + 4
            if payload_end < payload_start or crc_end > len(data):
                return None, None
            payload = data[payload_start:payload_end]
            expected_crc = int.from_bytes(data[payload_end:crc_end], "big")
            actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
            if expected_crc != actual_crc:
                return None, None
            chunks += 1
            if chunks == 1:
                if chunk_type != b"IHDR" or length != 13:
                    return None, None
                width = int.from_bytes(payload[0:4], "big")
                height = int.from_bytes(payload[4:8], "big")
                bit_depth = payload[8]
                color_type = payload[9]
                if (
                    not width
                    or not height
                    or payload[10] != 0
                    or payload[11] != 0
                    or payload[12] not in {0, 1}
                ):
                    return None, None
                interlace = payload[12]
                seen_ihdr = True
            elif chunk_type == b"IHDR":
                return None, None
            elif chunk_type == b"PLTE":
                if seen_idat or length == 0 or length % 3 or length > 768:
                    return None, None
                seen_plte = True
            elif chunk_type == b"IDAT":
                if not seen_ihdr or idat_ended or length == 0:
                    return None, None
                seen_idat = True
                idat_parts.append(payload)
            elif chunk_type == b"IEND":
                if length != 0 or not seen_idat or crc_end != len(data):
                    return None, None
                seen_iend = True
                offset = crc_end
                break
            elif seen_idat:
                idat_ended = True
            offset = crc_end
        if not (seen_ihdr and seen_idat and seen_iend) or offset != len(data):
            return None, None
        if color_type == 3 and not seen_plte:
            return None, None
        expected_size = _png_expected_decoded_size(
            width, height, bit_depth, color_type, interlace
        )
        if expected_size is None or expected_size > MAX_DECODED_IMAGE_BYTES:
            return None, None
        try:
            decompressor = zlib.decompressobj()
            decoded = decompressor.decompress(
                b"".join(idat_parts), expected_size + 1
            )
        except zlib.error:
            return None, None
        if (
            len(decoded) != expected_size
            or not decompressor.eof
            or decompressor.unused_data
            or decompressor.unconsumed_tail
            or not _png_filter_bytes_valid(
                decoded, width, height, bit_depth, color_type, interlace
            )
        ):
            return None, None
        return "PNG", (width, height)
    jpeg_dimensions = _jpeg_structure(data)
    if jpeg_dimensions is None:
        return None, None
    return "JPEG", jpeg_dimensions


def _human_validation_marker(value: str) -> bool:
    lowered = (value or "").strip().casefold()
    if not lowered or lowered in {
        "none",
        "pending",
        "not-run",
        "not-validated",
        "unknown",
        "open",
        "n/a",
    }:
        return False
    if any(marker in lowered for marker in ("not confirmed", "not approved", "no confirmado", "no aprobado")):
        return False
    return any(
        marker in lowered
        for marker in (
            "human-confirmed",
            "user-confirmed",
            "human-approved",
            "user-approved",
            "validated-by-human",
            "confirmado por",
            "validado por",
            "aprobado por",
        )
    )


def _explicit_human_validation(value: str) -> bool:
    """Require result, non-identifying role/alias, calendar date and ADR reference."""
    raw = (value or "").strip()
    if not _human_validation_marker(raw):
        return False
    role_match = re.search(
        r"(?:^|;)\s*(?:role|rol|alias)\s*=\s*([^;]+)", raw, re.IGNORECASE
    )
    date_match = re.search(
        r"(?:^|;)\s*(?:date|fecha)\s*=\s*([0-9]{4}-[0-9]{2}-[0-9]{2})(?:;|$)",
        raw,
        re.IGNORECASE,
    )
    reference_match = re.search(
        r"(?:^|;)\s*(?:ref|reference|referencia)\s*=\s*(ADR-[0-9]{3})(?:;|$)",
        raw,
        re.IGNORECASE,
    )
    if not role_match or not date_match or not reference_match:
        return False
    if not _meaningful_cell(role_match.group(1)):
        return False
    try:
        date.fromisoformat(date_match.group(1))
    except ValueError:
        return False
    return True


def _meaningful_cell(value: str) -> bool:
    lowered = (value or "").strip().casefold()
    if lowered.startswith(("no confirmado", "not confirmed", "sin confirmar")):
        return False
    return lowered not in {
        "",
        "none",
        "unknown",
        "open",
        "pending",
        "n/a",
        "not-run",
    }


def _meaningful_or_reasoned_na(value: str) -> bool:
    raw = (value or "").strip()
    lowered = raw.casefold()
    if lowered.startswith("not-applicable"):
        _, separator, reason = raw.partition(":")
        return bool(separator and _meaningful_cell(reason))
    return _meaningful_cell(raw)


def _implementation_scope_files(root: Path) -> tuple[list[Path], list[str]]:
    """Inventory implementation trees while excluding dependencies and build output."""
    files: list[Path] = []
    errors: list[str] = []
    for scope_name in IMPLEMENTATION_SCOPE_ROOTS:
        scope = root / scope_name
        if not scope.exists():
            continue
        if not scope.is_dir() or _is_link_like(scope):
            errors.append(f"el scope de implementación no es un directorio seguro: {scope_name}")
            continue
        for directory, dirnames, filenames in os.walk(scope, followlinks=False):
            directory_path = Path(directory)
            safe_directories: list[str] = []
            for dirname in sorted(dirnames):
                candidate = directory_path / dirname
                if dirname in IMPLEMENTATION_IGNORED_PARTS:
                    continue
                if _is_link_like(candidate):
                    errors.append(
                        "el scope de implementación contiene un enlace no permitido: "
                        + candidate.relative_to(root).as_posix()
                    )
                    continue
                safe_directories.append(dirname)
            dirnames[:] = safe_directories
            for filename in sorted(filenames):
                candidate = directory_path / filename
                relative = candidate.relative_to(root)
                if (
                    IMPLEMENTATION_IGNORED_PARTS.intersection(relative.parts)
                    or candidate.suffix.casefold() in {".pyc", ".tsbuildinfo"}
                ):
                    continue
                if _is_link_like(candidate) or not candidate.is_file():
                    errors.append(
                        "el scope de implementación contiene un archivo no permitido: "
                        + relative.as_posix()
                    )
                    continue
                files.append(candidate)
                if len(files) > MAX_IMPLEMENTATION_SCOPE_FILES:
                    return [], [
                        "el scope de implementación supera el máximo de "
                        f"{MAX_IMPLEMENTATION_SCOPE_FILES} archivos"
                    ]
    return files, errors


def implementation_fingerprint(
    root: Path, manifest: dict[str, Any], increment: str
) -> tuple[str | None, list[str], list[str]]:
    """Hash the implementation record and its complete relevant source trees."""
    root = root.resolve()
    errors: list[str] = []
    checked: list[str] = []
    implementation = manifest.get("implementation")
    if not isinstance(implementation, dict):
        return None, checked, ["falta el registro de implementación"]
    if implementation.get("status") != "completed":
        errors.append("implementation.status debe ser completed")
    if implementation.get("increment") != increment:
        errors.append("implementation.increment no coincide")
    changed_paths = implementation.get("changed_paths")
    if not isinstance(changed_paths, list) or not changed_paths:
        errors.append("implementation.changed_paths debe contener archivos")
        changed_paths = []
    declared_paths: set[str] = set()
    scope_paths: dict[str, Path] = {}
    seen_paths: set[str] = set()
    for value in changed_paths:
        if not isinstance(value, str) or not value.strip():
            errors.append("implementation.changed_paths contiene una ruta inválida")
            continue
        path, path_error = _safe_relative_file(root, value)
        if path_error or path is None:
            errors.append(f"implementation.changed_paths no permitido: {path_error}")
            continue
        if not path.is_file():
            errors.append(f"implementation.changed_paths no es un archivo: {value}")
            continue
        relative = path.relative_to(root).as_posix()
        if relative in seen_paths:
            errors.append(f"implementation.changed_paths duplica {relative}")
            continue
        seen_paths.add(relative)
        declared_paths.add(relative)
        scope_paths[relative] = path
    implementation_files, scope_errors = _implementation_scope_files(root)
    errors.extend(scope_errors)
    for path in implementation_files:
        scope_paths[path.relative_to(root).as_posix()] = path
    if errors:
        return None, checked, errors
    normalized: list[tuple[str, str]] = []
    for relative, path in sorted(scope_paths.items()):
        checked.append(relative)
        normalized.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    digest = hashlib.sha256()
    record = {
        "increment": implementation.get("increment"),
        "profile_id": implementation.get("profile_id"),
        "profile_version": implementation.get("profile_version"),
        "declared_changed_paths": sorted(declared_paths),
        "files": sorted(normalized),
    }
    digest.update(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return digest.hexdigest(), checked, []


def _artifact_hash(
    root: Path, manifest: dict[str, Any], artifact_id: str
) -> tuple[str | None, str | None, str | None]:
    entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if isinstance(item, dict) and item.get("id") == artifact_id
        ),
        None,
    )
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        return None, None, f"falta {artifact_id}"
    path, path_error = _safe_relative_file(root, entry["path"])
    if path_error or path is None or not path.is_file():
        return None, None, f"no se puede leer {artifact_id}: {path_error or entry['path']}"
    relative = path.relative_to(root).as_posix()
    return hashlib.sha256(path.read_bytes()).hexdigest(), relative, None


def _visual_evidence_path(
    root: Path, requested: str | Path
) -> tuple[Path | None, str | None]:
    root_alias = root.absolute()
    root = root.resolve()
    candidate = Path(requested)
    if candidate.is_absolute():
        candidate_absolute = candidate.absolute()
        try:
            relative = candidate_absolute.relative_to(root_alias)
        except ValueError:
            if any(
                _is_link_like(parent)
                for parent in (candidate_absolute, *candidate_absolute.parents)
            ):
                return None, "la evidencia visual usa un enlace simbólico o junction"
            try:
                relative = candidate.resolve().relative_to(root)
            except ValueError:
                return None, "la evidencia visual está fuera del proyecto"
    else:
        relative = candidate
    path, path_error = _safe_relative_file(root, relative.as_posix())
    if path_error or path is None:
        return None, path_error
    try:
        path.relative_to((root / "docs/lks-sdd/evidence/visual").resolve())
    except ValueError:
        return None, "la evidencia visual debe estar bajo docs/lks-sdd/evidence/visual/"
    return path, None


def validate_visual_review_evidence(
    root: Path,
    manifest: dict[str, Any],
    definitions: dict[str, dict[str, str]],
    increment: str,
    requested: str | Path,
    *,
    require_fresh: bool,
) -> tuple[list[str], dict[str, Any] | None, list[str], list[str]]:
    """Validate browser evidence against the current implementation and UX baseline."""
    root = root.resolve()
    errors: list[str] = []
    limitations: list[str] = []
    checked_files: list[str] = []
    path, path_error = _visual_evidence_path(root, requested)
    if path_error or path is None:
        return [path_error or "ruta de evidencia inválida"], None, limitations, checked_files
    if not path.is_file():
        return [f"falta la evidencia visual {path.name}"], None, limitations, checked_files
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"evidencia visual JSON inválida: {exc}"], None, limitations, checked_files
    required = {
        "schema_version",
        "increment",
        "status",
        "review_type",
        "reviewed_at",
        "reviewer",
        "human_validation",
        "baseline",
        "coverage",
        "screenshots",
        "checks",
        "limitations",
    }
    if not isinstance(value, dict) or set(value) != required:
        return ["la evidencia visual no respeta el contrato cerrado 1.1"], None, limitations, checked_files
    if value.get("schema_version") != "1.1":
        errors.append("schema_version debe ser 1.1")
    if value.get("increment") != increment:
        errors.append("increment no coincide")
    if value.get("status") != "passed":
        errors.append("status debe ser passed")
    if value.get("review_type") != "manual-browser":
        errors.append("review_type debe ser manual-browser")
    reviewed_at: datetime | None = None
    try:
        reviewed_at = datetime.fromisoformat(
            str(value.get("reviewed_at", "")).replace("Z", "+00:00")
        )
        if reviewed_at.tzinfo is None:
            raise ValueError("timezone missing")
        if reviewed_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
            errors.append("reviewed_at no puede estar en el futuro")
        if require_fresh and (
            datetime.now(timezone.utc) - reviewed_at.astimezone(timezone.utc)
        ).days > 7:
            errors.append("reviewed_at tiene más de siete días; repita la revisión")
    except ValueError:
        errors.append("reviewed_at debe ser un timestamp ISO-8601 con zona horaria")
    reviewer = value.get("reviewer")
    if not isinstance(reviewer, dict) or set(reviewer) != {"role", "alias"}:
        errors.append("reviewer debe declarar role y alias no identificativo")
    elif not _meaningful_cell(str(reviewer.get("role", ""))) or not _meaningful_cell(
        str(reviewer.get("alias", ""))
    ):
        errors.append("reviewer.role y reviewer.alias deben ser significativos")
    if not _human_validation_marker(str(value.get("human_validation", ""))):
        errors.append("human_validation no contiene confirmación humana explícita")

    increments_hash, increments_path, artifact_error = _artifact_hash(
        root, manifest, "ART-INCREMENTS"
    )
    if artifact_error:
        errors.append(artifact_error)
    ux_hash, ux_path, artifact_error = _artifact_hash(root, manifest, "ART-UX")
    if artifact_error:
        errors.append(artifact_error)
    implementation_hash, implementation_files, implementation_errors = (
        implementation_fingerprint(root, manifest, increment)
    )
    errors.extend(implementation_errors)
    checked_files.extend(implementation_files)

    interface_entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if isinstance(item, dict) and item.get("id") == "ART-INCREMENTS"
        ),
        None,
    )
    interface_row: dict[str, str] | None = None
    if isinstance(interface_entry, dict) and isinstance(interface_entry.get("path"), str):
        try:
            _, interface_body = parse_frontmatter(
                (root / interface_entry["path"]).read_text(encoding="utf-8")
            )
            interface_rows = table_rows_for_headers(
                parse_markdown_table_blocks(interface_body), INTERFACE_CONTRACT_HEADERS
            )
            matching = [
                row
                for row in interface_rows or []
                if row.get("Increment", "").strip() == increment
            ]
            if len(matching) == 1:
                interface_row = matching[0]
        except (OSError, UnicodeError, ValueError):
            interface_row = None
    if interface_row is None:
        errors.append("no se puede resolver la fila de interfaz del incremento")
        expected_ux: set[str] = set()
        expected_visuals: set[str] = set()
    else:
        visual_mode = interface_row.get("Visual mode", "").strip().casefold()
        expected_ux = {
            item
            for item in ID_RE.findall(interface_row.get("UX contract", ""))
            if item.startswith("UX-")
        }
        expected_visuals = {
            item
            for item in ID_RE.findall(interface_row.get("Visual prototype", ""))
            if item.startswith("VIS-")
        }
    if interface_row is None:
        visual_mode = "invalid"
    if not expected_ux:
        errors.append("la fila de interfaz no enlaza UX-###")
    if visual_mode in {"new", "material-change", "reuse"} and not expected_visuals:
        errors.append("la fila de interfaz no enlaza VIS-###")

    baseline = value.get("baseline")
    baseline_required = {
        "baseline_id",
        "implementation_sha256",
        "increments_sha256",
        "ux_contract_sha256",
        "visual_assets",
    }
    if not isinstance(baseline, dict) or set(baseline) != baseline_required:
        errors.append("baseline no respeta el contrato cerrado")
        baseline = {}
    if baseline.get("baseline_id") != manifest.get("baseline_id"):
        errors.append("baseline_id no coincide")
    for label, actual, expected in (
        ("implementation_sha256", baseline.get("implementation_sha256"), implementation_hash),
        ("increments_sha256", baseline.get("increments_sha256"), increments_hash),
        ("ux_contract_sha256", baseline.get("ux_contract_sha256"), ux_hash),
    ):
        if not isinstance(actual, str) or not re.fullmatch(r"[a-f0-9]{64}", actual):
            errors.append(f"baseline.{label} debe ser SHA-256")
        elif expected is not None and actual != expected:
            errors.append(f"baseline.{label} no coincide con la instantánea actual")
    visual_assets = baseline.get("visual_assets")
    declared_visuals: dict[str, str] = {}
    if not isinstance(visual_assets, list):
        errors.append("baseline.visual_assets debe ser una lista")
    else:
        for item in visual_assets:
            if not isinstance(item, dict) or set(item) != {"vis_id", "sha256"}:
                errors.append("baseline.visual_assets contiene una fila inválida")
                continue
            visual_id = str(item.get("vis_id", ""))
            sha = str(item.get("sha256", "")).casefold()
            if visual_id in declared_visuals:
                errors.append(f"baseline.visual_assets duplica {visual_id}")
            declared_visuals[visual_id] = sha
    if set(declared_visuals) != expected_visuals:
        errors.append("baseline.visual_assets no coincide con los VIS del incremento")
    for visual_id in sorted(expected_visuals):
        visual = definitions.get(visual_id, {})
        if visual.get("State") not in {"confirmed", "decision"}:
            errors.append(f"{visual_id} no está confirmado")
        actual_hash = visual.get("_asset_sha256")
        if declared_visuals.get(visual_id) != actual_hash:
            errors.append(f"baseline visual no coincide con {visual_id}")

    screenshots = value.get("screenshots")
    screenshot_ids: set[str] = set()
    screenshot_records: list[dict[str, Any]] = []
    if not isinstance(screenshots, list) or not screenshots:
        errors.append("screenshots debe contener al menos una captura")
        screenshots = []
    for screenshot in screenshots:
        screenshot_required = {"id", "path", "sha256", "route", "viewport", "capture"}
        if not isinstance(screenshot, dict) or set(screenshot) != screenshot_required:
            errors.append("screenshots contiene una fila inválida")
            continue
        screenshot_id = str(screenshot.get("id", ""))
        if not re.fullmatch(r"SHOT-[0-9]{3}", screenshot_id) or screenshot_id in screenshot_ids:
            errors.append(f"ID de screenshot inválido o duplicado: {screenshot_id}")
            continue
        screenshot_ids.add(screenshot_id)
        screenshot_path, screenshot_error = _visual_evidence_path(
            root, str(screenshot.get("path", ""))
        )
        if screenshot_error or screenshot_path is None or not screenshot_path.is_file():
            errors.append(f"{screenshot_id}: screenshot no disponible: {screenshot_error}")
            continue
        actual_format, dimensions = _image_signature(screenshot_path)
        if actual_format is None or dimensions is None:
            errors.append(f"{screenshot_id}: firma PNG/JPEG inválida")
            continue
        expected_sha = str(screenshot.get("sha256", "")).casefold()
        actual_sha = hashlib.sha256(screenshot_path.read_bytes()).hexdigest()
        if not re.fullmatch(r"[a-f0-9]{64}", expected_sha) or expected_sha != actual_sha:
            errors.append(f"{screenshot_id}: SHA-256 no coincide")
        viewport = screenshot.get("viewport")
        if not isinstance(viewport, dict) or set(viewport) != {"width", "height", "dpr"}:
            errors.append(f"{screenshot_id}: viewport inválido")
        else:
            width = viewport.get("width")
            height = viewport.get("height")
            dpr = viewport.get("dpr")
            if (
                not isinstance(width, int)
                or isinstance(width, bool)
                or width <= 0
                or not isinstance(height, int)
                or isinstance(height, bool)
                or height <= 0
                or not isinstance(dpr, (int, float))
                or isinstance(dpr, bool)
                or dpr <= 0
            ):
                errors.append(f"{screenshot_id}: viewport contiene dimensiones inválidas")
            else:
                expected_width = round(width * dpr)
                expected_height = round(height * dpr)
                capture = screenshot.get("capture")
                if capture == "viewport" and dimensions != (expected_width, expected_height):
                    errors.append(f"{screenshot_id}: dimensiones no coinciden con viewport y DPR")
                elif capture == "full-page" and (
                    dimensions[0] != expected_width or dimensions[1] < expected_height
                ):
                    errors.append(f"{screenshot_id}: captura full-page no coincide con el viewport")
                elif capture not in {"viewport", "full-page"}:
                    errors.append(f"{screenshot_id}: capture inválido")
        if not isinstance(screenshot.get("route"), str) or not screenshot.get("route", "").startswith("/"):
            errors.append(f"{screenshot_id}: route debe ser una ruta de aplicación")
        relative = screenshot_path.relative_to(root).as_posix()
        checked_files.append(relative)
        screenshot_records.append(
            {"id": screenshot_id, "path": relative, "sha256": actual_sha}
        )

    coverage = value.get("coverage")
    covered_ux: set[str] = set()
    covered_visuals: set[str] = set()
    used_screenshots: set[str] = set()
    if not isinstance(coverage, list) or not coverage:
        errors.append("coverage debe contener la cobertura UX/VIS")
        coverage = []
    for item in coverage:
        if not isinstance(item, dict) or set(item) != {"ux_ids", "vis_ids", "states", "status", "screenshots"}:
            errors.append("coverage contiene una fila inválida")
            continue
        ux_ids = item.get("ux_ids")
        vis_ids = item.get("vis_ids")
        states = item.get("states")
        shot_ids = item.get("screenshots")
        if item.get("status") != "passed":
            errors.append("toda cobertura visual debe estar passed")
        if not isinstance(ux_ids, list) or not ux_ids or not all(isinstance(v, str) for v in ux_ids):
            errors.append("coverage.ux_ids debe contener IDs")
            ux_ids = []
        if not isinstance(vis_ids, list) or not all(isinstance(v, str) for v in vis_ids):
            errors.append("coverage.vis_ids debe ser una lista de IDs")
            vis_ids = []
        elif expected_visuals and not vis_ids:
            errors.append("coverage.vis_ids debe contener los VIS aplicables")
        if not isinstance(states, list) or not states or not all(_meaningful_cell(str(v)) for v in states):
            errors.append("coverage.states debe describir estados revisados")
        if not isinstance(shot_ids, list) or not shot_ids or not all(isinstance(v, str) for v in shot_ids):
            errors.append("coverage.screenshots debe enlazar capturas")
            shot_ids = []
        covered_ux.update(ux_ids)
        covered_visuals.update(vis_ids)
        used_screenshots.update(shot_ids)
        if not set(ux_ids).issubset(expected_ux):
            errors.append("coverage contiene UX ajenos al incremento")
        if not set(vis_ids).issubset(expected_visuals):
            errors.append("coverage contiene VIS ajenos al incremento")
        if not set(shot_ids).issubset(screenshot_ids):
            errors.append("coverage enlaza screenshots inexistentes")
    if covered_ux != expected_ux:
        errors.append("coverage no cubre todos los UX del incremento")
    if covered_visuals != expected_visuals:
        errors.append("coverage no cubre todos los VIS del incremento")

    checks = value.get("checks")
    check_ids: set[str] = set()
    if not isinstance(checks, list) or not checks:
        errors.append("checks debe contener comprobaciones estructuradas")
        checks = []
    for item in checks:
        if not isinstance(item, dict) or set(item) != {"id", "status", "ux_ids", "screenshots", "note"}:
            errors.append("checks contiene una fila inválida")
            continue
        check_id = str(item.get("id", ""))
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", check_id) or check_id in check_ids:
            errors.append(f"check ID inválido o duplicado: {check_id}")
        check_ids.add(check_id)
        if item.get("status") != "passed":
            errors.append(f"{check_id}: status debe ser passed")
        ux_ids = item.get("ux_ids")
        shot_ids = item.get("screenshots")
        if (
            not isinstance(ux_ids, list)
            or not ux_ids
            or not all(isinstance(value, str) for value in ux_ids)
            or not set(ux_ids).issubset(expected_ux)
        ):
            errors.append(f"{check_id}: ux_ids inválidos")
        if (
            not isinstance(shot_ids, list)
            or not shot_ids
            or not all(isinstance(value, str) for value in shot_ids)
            or not set(shot_ids).issubset(screenshot_ids)
        ):
            errors.append(f"{check_id}: screenshots inválidos")
        else:
            used_screenshots.update(shot_ids)
        if not _meaningful_cell(str(item.get("note", ""))):
            errors.append(f"{check_id}: note es obligatorio")
    if screenshot_ids - used_screenshots:
        errors.append("hay screenshots que no respaldan cobertura ni checks")

    declared_limitations = value.get("limitations")
    if not isinstance(declared_limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in declared_limitations
    ):
        errors.append("limitations debe ser una lista de textos")
    else:
        limitations.extend(f"Revisión visual: {item}" for item in declared_limitations)

    relative = path.relative_to(root).as_posix()
    checked_files.extend(
        item
        for item in (relative, increments_path, ux_path)
        if isinstance(item, str)
    )
    if errors:
        return errors, None, limitations, list(dict.fromkeys(checked_files))
    evidence_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    outcome = {
        "name": "visual-browser-review",
        "status": "passed",
        "schema_version": "1.1",
        "evidence": relative,
        "evidence_sha256": evidence_sha,
        "baseline": {
            "baseline_id": manifest.get("baseline_id"),
            "implementation_sha256": implementation_hash,
            "increments_sha256": increments_hash,
            "ux_contract_sha256": ux_hash,
            "visual_assets": [
                {"vis_id": visual_id, "sha256": declared_visuals[visual_id]}
                for visual_id in sorted(declared_visuals)
            ],
        },
        "screenshots": screenshot_records,
    }
    return [], outcome, limitations, list(dict.fromkeys(checked_files))


def evidence_document_errors(value: Any, expected_id: str) -> list[str]:
    if not isinstance(value, dict):
        return ["debe ser un objeto JSON"]
    errors: list[str] = []
    if value.get("schema_version") == "1.2":
        evidence_schema = json.loads(
            (PLUGIN_ROOT / "schemas/verification-evidence-1.2.schema.json").read_text(
                encoding="utf-8"
            )
        )
        errors.extend(validate_json_schema(value, evidence_schema, "evidence"))
    if value.get("evidence_id") != expected_id:
        errors.append("evidence_id no coincide con la referencia")
    if not isinstance(value.get("increment"), str) or not re.fullmatch(
        r"INC-[0-9]{3}", value.get("increment", "")
    ):
        errors.append("increment no usa INC-###")
    if (
        not isinstance(value.get("profile_id"), str)
        or not value.get("profile_id", "").strip()
    ):
        errors.append("profile_id es obligatorio")
    if (
        not isinstance(value.get("profile_version"), str)
        or not value.get("profile_version", "").strip()
    ):
        errors.append("profile_version es obligatorio")
    if value.get("revision") is not None and not isinstance(value.get("revision"), str):
        errors.append("revision debe ser texto o null")
    classification = value.get("classification")
    if classification not in {
        "verified",
        "verified-with-reservations",
        "not-verified",
    }:
        errors.append("classification no pertenece al catálogo")
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks debe contener resultados ejecutados")
        checks = []
    elif not all(
        isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and item.get("status") in {"passed", "failed", "blocked", "not-run"}
        for item in checks
    ):
        errors.append("checks contiene resultados inválidos")
    limitations = value.get("limitations")
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        errors.append("limitations debe ser una lista de textos")
        limitations = []
    statuses = [item.get("status") for item in checks if isinstance(item, dict)]
    if classification == "verified" and (
        any(status != "passed" for status in statuses) or limitations
    ):
        errors.append("verified requiere checks superados y ninguna limitación")
    if classification == "verified-with-reservations" and (
        any(status != "passed" for status in statuses) or not limitations
    ):
        errors.append(
            "verified-with-reservations requiere checks superados y limitaciones"
        )
    if (
        classification == "not-verified"
        and statuses
        and all(status == "passed" for status in statuses)
    ):
        errors.append("not-verified requiere al menos un check no superado")
    return errors


def load_project_manifest(
    project_root: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    path, path_error = _safe_relative_file(project_root, ".lks-sdd/project.json")
    if path_error or path is None:
        return None, [f"Índice operativo no permitido: {path_error}"]
    if not path.is_file():
        return None, ["Falta .lks-sdd/project.json."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"No se puede leer el índice o su esquema: {exc}"]
    if not isinstance(data, dict):
        return None, ["El índice operativo debe contener un objeto JSON."]
    schema_version = data.get("schema_version")
    schema_path = PROJECT_SCHEMAS.get(schema_version)
    if schema_path is None:
        return data, [
            f"project.schema_version={schema_version!r} no está soportado; use 1.0 a 1.5."
        ]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return data, [f"No se puede leer el esquema {schema_version}: {exc}"]
    return data, validate_json_schema(data, schema, "project")


def validate_project(
    project_root: Path,
) -> tuple[ValidationReport, dict[str, Any] | None, dict[str, dict[str, str]]]:
    root = project_root.expanduser().resolve()
    report = ValidationReport(project_root=str(root))
    if not root.is_dir():
        report.errors.append(f"La raíz no existe o no es una carpeta: {root}")
        return report, None, {}

    manifest, manifest_errors = load_project_manifest(root)
    report.errors.extend(manifest_errors)
    if manifest is None:
        return report, None, {}
    report.checked_files.append(".lks-sdd/project.json")
    if manifest_errors:
        return report, manifest, {}

    artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
    artifact_ids: set[str] = set()
    artifact_paths: set[str] = set()
    artifact_entries: dict[str, dict[str, Any]] = {}
    artifact_tables: dict[
        str, list[tuple[tuple[str, ...], list[dict[str, str]]]]
    ] = {}
    artifact_metadata: dict[str, dict[str, Any]] = {}
    artifact_bodies: dict[str, str] = {}
    definitions: dict[str, dict[str, str]] = {}
    references: list[tuple[str, str]] = []
    schema_version = str(manifest.get("schema_version", ""))
    id_re = _id_re_for_schema(schema_version)
    valid_element_states = set(VALID_ELEMENT_STATES)
    if schema_version not in {"1.4", "1.5"}:
        valid_element_states -= V14_ONLY_ELEMENT_STATES
    frontmatter_schema = json.loads(
        FRONTMATTER_SCHEMAS[schema_version].read_text(encoding="utf-8")
    )
    if schema_version == "1.0":
        report.warnings.append(
            "Proyecto schema 1.0 validado en modo compatibilidad; prepare 1.1 "
            "con `python \"<plugin-root>/scripts/lks_sdd.py\" migrate "
            "\"<project-root>\" --target-schema 1.1 --dry-run`. Si "
            "human_review_required no está vacío, resuelva las ambigüedades "
            "en los Markdown 1.0 antes de aplicar; no se infieren confirmaciones."
        )
    elif schema_version == "1.1":
        report.warnings.append(
            "Proyecto schema 1.1 validado en modo compatible; la gobernanza de "
            "entrega, perfiles por desplegable y PLAN/TASK requieren una migración "
            "explícita 1.1 -> 1.2."
        )

    for entry in artifacts if isinstance(artifacts, list) else []:
        if not isinstance(entry, dict):
            continue
        artifact_id = entry.get("id")
        relative = entry.get("path")
        if artifact_id in artifact_ids:
            report.errors.append(f"Identificador de artefacto duplicado: {artifact_id}")
        artifact_ids.add(artifact_id)
        if isinstance(artifact_id, str):
            artifact_entries.setdefault(artifact_id, entry)
        if relative in artifact_paths:
            report.errors.append(f"Ruta de artefacto duplicada: {relative}")
        artifact_paths.add(relative)
        if not isinstance(relative, str):
            continue
        path, path_error = _safe_relative_file(root, relative)
        if path_error:
            report.errors.append(path_error)
            continue
        if path is None or not path.is_file():
            if entry.get("required"):
                report.errors.append(f"Falta el artefacto obligatorio: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
        except (OSError, UnicodeError, ValueError) as exc:
            report.errors.append(f"{relative}: Markdown inválido: {exc}")
            continue
        report.checked_files.append(relative)
        report.errors.extend(
            f"{relative}: {error}"
            for error in validate_json_schema(
                metadata, frontmatter_schema, "frontmatter"
            )
        )
        if metadata.get("artifact_id") != artifact_id:
            report.errors.append(f"{relative}: artifact_id no coincide con el índice.")
        if metadata.get("project_id") != manifest.get("project_id"):
            report.errors.append(f"{relative}: project_id no coincide con el índice.")
        if metadata.get("baseline_id") != manifest.get("baseline_id"):
            report.errors.append(f"{relative}: baseline_id no coincide con el índice.")
        core_contract = CORE_ARTIFACTS.get(artifact_id) or ADOPTION_ARTIFACTS.get(
            artifact_id
        )
        if core_contract and metadata.get("artifact_type") != core_contract[1]:
            report.errors.append(
                f"{relative}: artifact_type debe ser {core_contract[1]!r} para {artifact_id}."
            )
        if not body or not re.search(r"^#\s+\S", body, re.MULTILINE):
            report.errors.append(
                f"{relative}: el cuerpo no contiene un título y contenido legible."
            )
        if re.search(r"\{\{[A-Z0-9_]+\}\}", text):
            report.errors.append(
                f"{relative}: contiene tokens de plantilla sin resolver."
            )

        table_blocks = parse_markdown_table_blocks(body)
        if isinstance(artifact_id, str):
            artifact_tables[artifact_id] = table_blocks
            artifact_metadata[artifact_id] = metadata
            artifact_bodies[artifact_id] = body
        actual_headers = {headers for headers, _ in table_blocks}
        if schema_version != "1.0":
            artifact_contract = DOCUMENT_CONTRACTS.get("artifacts", {}).get(
                artifact_id, {}
            )
            contracts = artifact_contract.get("tables", [])
            effective_schema = schema_version
            inheritance = DOCUMENT_CONTRACTS.get("schema_inheritance", {})
            visited: set[str] = set()
            while not any(
                effective_schema in item.get("schemas", []) for item in contracts
            ):
                if effective_schema in visited or effective_schema not in inheritance:
                    break
                visited.add(effective_schema)
                effective_schema = inheritance[effective_schema]
            required_header_sets = [
                tuple(item.get("headers", []))
                for item in contracts
                if effective_schema in item.get("schemas", [])
                and item.get("min_occurs", 0) > 0
            ]
        else:
            required_header_sets = REQUIRED_TABLE_HEADERS.get(artifact_id, [])
        for required_headers in required_header_sets:
            if required_headers not in actual_headers:
                report.errors.append(
                    f"{relative}: falta la tabla contractual con cabeceras {list(required_headers)!r}."
                )

        for headers, table in table_blocks:
            table_contract = document_table_contract(
                str(artifact_id), headers, schema_version
            )
            key_column = "ID"
            if schema_version != "1.0" and table_contract is not None:
                key_column = table_contract.get("key", {}).get("column", "")
            for row in table:
                element_id = row.get(key_column) if key_column else None
                if element_id:
                    if not id_re.fullmatch(element_id):
                        report.errors.append(
                            f"{relative}: identificador inválido {element_id!r}."
                        )
                    elif (
                        schema_version != "1.0"
                        and table_contract is not None
                        and element_id.split("-", 1)[0]
                        not in set(table_contract.get("key", {}).get("prefixes", []))
                    ):
                        report.errors.append(
                            f"{relative}: {element_id} no pertenece al prefijo propietario de {table_contract.get('id')}."
                        )
                    elif element_id in definitions:
                        report.errors.append(
                            f"Identificador de elemento duplicado: {element_id}"
                        )
                    else:
                        definitions[element_id] = {
                            "path": relative,
                            "artifact_type": metadata.get("artifact_type", "unknown"),
                            **row,
                        }
                state = row.get("State")
                if schema_version != "1.0" and state and table_contract is not None:
                    policy_name = table_contract.get("state", {}).get("policy")
                    allowed_states = set(
                        DOCUMENT_CONTRACTS.get("state_policies", {})
                        .get(policy_name, {})
                        .get("allowed", [])
                    )
                    if state not in allowed_states:
                        report.errors.append(
                            f"{relative}: estado {state!r} no admitido por la política {policy_name!r}."
                        )
                elif state and state not in valid_element_states:
                    report.errors.append(
                        f"{relative}: estado de elemento no admitido {state!r}."
                    )
                if schema_version != "1.0" and table_contract is not None:
                    relation_columns = set(table_contract.get("relations", {}))
                else:
                    relation_columns = set(row) - {"ID"}
                for column in relation_columns:
                    cell = row.get(column, "")
                    references.extend((relative, item) for item in id_re.findall(cell))

    manifest_v06_contract = plugin_version_at_least(
        manifest.get("plugin_version"), (0, 6, 0)
    )
    for gated_artifact in ("ART-STATUS", "ART-INCREMENTS", "ART-UX"):
        metadata = artifact_metadata.get(gated_artifact)
        if (
            manifest_v06_contract
            and metadata is not None
            and not plugin_version_at_least(
                metadata.get("created_with_plugin_version"), (0, 6, 0)
            )
        ):
            report.errors.append(
                f"{gated_artifact}: created_with_plugin_version no puede rebajarse por debajo de project.json.plugin_version 0.6."
            )
    status_v06_contract = v06_contract_applies(
        manifest, artifact_metadata.get("ART-STATUS")
    )
    increments_v06_contract = v06_contract_applies(
        manifest, artifact_metadata.get("ART-INCREMENTS")
    )

    if status_v06_contract:
        status_body = artifact_bodies.get("ART-STATUS", "")
        global_percentage = re.search(
            r"(?im)^(?=[^\n]*(?:madurez|cobertura|definici[oó]n|avance global|progreso global))[^\n]*\b[0-9]{1,3}\s*%",
            status_body,
        )
        if global_percentage:
            report.errors.append(
                "ART-STATUS: no se admite un porcentaje global de madurez o cobertura."
            )
        status_tables = artifact_tables.get("ART-STATUS", [])
        coverage_rows = table_rows_for_headers(
            status_tables, DEFINITION_COVERAGE_HEADERS
        )
        if coverage_rows is None:
            report.errors.append(
                "docs/lks-sdd/00-control/project-status.md: falta una única tabla de cobertura cualitativa contractual."
            )
        elif not coverage_rows:
            report.errors.append(
                "docs/lks-sdd/00-control/project-status.md: la cobertura cualitativa no puede quedar vacía."
            )
        else:
            seen_dimensions: set[str] = set()
            for row in coverage_rows:
                dimension = row.get("Dimensión", "").strip()
                state = row.get("Estado", "").strip()
                scope = row.get("Alcance", "").strip()
                available = row.get("Información disponible", "").strip()
                missing = row.get("Falta profundizar", "").strip()
                impact = row.get("Impacto", "").strip()
                if not dimension:
                    report.errors.append("ART-STATUS: dimensión de cobertura vacía.")
                elif dimension in seen_dimensions:
                    report.errors.append(
                        f"ART-STATUS: dimensión de cobertura duplicada: {dimension}"
                    )
                else:
                    seen_dimensions.add(dimension)
                if not scope:
                    report.errors.append(
                        f"ART-STATUS: {dimension or 'dimensión'} no declara alcance."
                    )
                if state not in {"unknown", "partial", "sufficient"}:
                    if not state.startswith("not-applicable:") or not state.partition(":")[2].strip():
                        report.errors.append(
                            f"ART-STATUS: estado de cobertura inválido para {dimension or 'dimensión'}: {state!r}."
                        )
                if state == "sufficient" and not _meaningful_cell(available):
                    report.errors.append(
                        f"ART-STATUS: {dimension} no puede estar sufficient sin información disponible."
                    )
                if state in {"unknown", "partial"} and not _meaningful_cell(missing):
                    report.errors.append(
                        f"ART-STATUS: {dimension} debe explicar qué falta profundizar."
                    )
                if not _meaningful_cell(impact):
                    report.errors.append(
                        f"ART-STATUS: {dimension or 'dimensión'} debe declarar impacto."
                    )

    increment_tables = artifact_tables.get("ART-INCREMENTS", [])
    interface_rows = table_rows_for_headers(
        increment_tables, INTERFACE_CONTRACT_HEADERS
    )
    interface_by_increment: dict[str, dict[str, str]] = {}
    if increments_v06_contract and interface_rows is None:
        report.errors.append(
            "docs/lks-sdd/04-delivery/increments.md: falta una única tabla contractual de aplicabilidad de interfaz."
        )
    if interface_rows is not None:
        for row in interface_rows:
            increment_id = row.get("Increment", "").strip()
            applicability, inline_reason = interface_applicability(
                row.get("Interface applicability", "")
            )
            visual_mode = row.get("Visual mode", "").strip().casefold()
            visual = row.get("Visual prototype", "").strip()
            reason = row.get("Reason", "").strip() or inline_reason or ""
            if not re.fullmatch(r"INC-[0-9]{3}", increment_id):
                report.errors.append(
                    f"ART-INCREMENTS: identificador inválido en aplicabilidad de interfaz: {increment_id!r}."
                )
                continue
            if increment_id in interface_by_increment:
                report.errors.append(
                    f"ART-INCREMENTS: aplicabilidad de interfaz duplicada para {increment_id}."
                )
                continue
            interface_by_increment[increment_id] = row
            if applicability is None:
                report.errors.append(
                    f"ART-INCREMENTS: aplicabilidad de interfaz inválida para {increment_id}."
                )
                continue
            if visual_mode not in VISUAL_MODES:
                report.errors.append(
                    f"ART-INCREMENTS: Visual mode inválido para {increment_id}: {visual_mode!r}."
                )
                continue
            if applicability in {"pending", "not-applicable"} and not _meaningful_cell(reason):
                report.errors.append(
                    f"ART-INCREMENTS: {increment_id} requiere motivo para interface {applicability}."
                )
            if applicability == "pending" and visual_mode != "pending":
                report.errors.append(
                    f"ART-INCREMENTS: {increment_id} con interfaz pending debe usar Visual mode=pending."
                )
            if applicability == "not-applicable":
                if visual_mode != "none":
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} sin interfaz debe usar Visual mode=none."
                    )
                if not visual.casefold().startswith("not-applicable:"):
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} sin interfaz debe justificar Visual prototype como not-applicable: motivo."
                    )
            if applicability == "applicable":
                ux_contract = row.get("UX contract", "").strip()
                if not ux_contract:
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} applicable debe enlazar su contrato UX o dejarlo pending."
                    )
                if not visual:
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} applicable debe declarar prototipo, pending o not-applicable: motivo."
                    )
                visual_ids = [
                    item
                    for item in id_re.findall(visual)
                    if item.startswith("VIS-")
                ]
                if visual_mode == "pending" and visual.casefold() != "pending":
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} con Visual mode=pending debe declarar Visual prototype=pending."
                    )
                if visual_mode in {"new", "material-change"} and not (
                    visual.casefold() == "pending" or visual_ids
                ):
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} con Visual mode={visual_mode} requiere VIS-### o pending."
                    )
                if visual_mode == "reuse":
                    if not visual_ids:
                        report.errors.append(
                            f"ART-INCREMENTS: {increment_id} con Visual mode=reuse debe enlazar una baseline VIS-### confirmada."
                        )
                    if not _meaningful_cell(reason):
                        report.errors.append(
                            f"ART-INCREMENTS: {increment_id} con Visual mode=reuse debe delimitar el motivo de reutilización."
                        )
                if visual_mode == "none":
                    if not visual.casefold().startswith("not-applicable:"):
                        report.errors.append(
                            f"ART-INCREMENTS: {increment_id} con Visual mode=none debe justificar Visual prototype como not-applicable: motivo."
                        )
                    none_disclosure = f"{visual} {reason}".casefold()
                    if (
                        visual_ids
                        or any(item.startswith("VIS-") for item in id_re.findall(reason))
                        or "reutil" in none_disclosure
                        or "reuse" in none_disclosure
                    ):
                        report.errors.append(
                            f"ART-INCREMENTS: {increment_id} no puede ocultar reutilización bajo Visual mode=none."
                        )
                    if not _meaningful_cell(reason):
                        report.errors.append(
                            f"ART-INCREMENTS: {increment_id} con Visual mode=none requiere motivo."
                        )

    if increments_v06_contract:
        increment_ids = {
            item_id
            for item_id, item in definitions.items()
            if item_id.startswith("INC-")
            and item.get("path", "").endswith("increments.md")
            and item.get("State") in {"confirmed", "decision"}
        }
        for increment_id in sorted(increment_ids - set(interface_by_increment)):
            report.errors.append(
                f"ART-INCREMENTS: falta aplicabilidad de interfaz para {increment_id}."
            )

    ux_entry = artifact_entries.get("ART-UX")
    applicable_increments = {
        increment_id
        for increment_id, row in interface_by_increment.items()
        if interface_applicability(row.get("Interface applicability", ""))[0]
        == "applicable"
    }
    if applicable_increments and ux_entry is None:
        report.errors.append(
            "Un incremento con interfaz applicable requiere ART-UX en el índice operativo."
        )
    if ux_entry is not None:
        expected_ux_path = "docs/lks-sdd/03-solution/ux-accessibility.md"
        if ux_entry.get("path") != expected_ux_path:
            report.errors.append(
                f"ART-UX: la ruta canónica debe ser {expected_ux_path!r}."
            )
        if ux_entry.get("required") is not True:
            report.errors.append(
                "ART-UX: una vez materializado, el contrato UX debe ser obligatorio."
            )
        ux_tables = artifact_tables.get("ART-UX", [])
        ux_actual_headers = {headers for headers, _ in ux_tables}
        ux_v06_contract = v06_contract_applies(
            manifest, artifact_metadata.get("ART-UX")
        )
        if ux_v06_contract:
            for required_headers in sorted(UX_REQUIRED_HEADERS):
                if required_headers not in ux_actual_headers:
                    report.errors.append(
                        f"{expected_ux_path}: falta la tabla UX contractual con cabeceras {list(required_headers)!r}."
                    )

            screen_rows = table_rows_for_headers(ux_tables, UX_SCREEN_HEADERS)
            detail_rows = table_rows_for_headers(
                ux_tables, UX_SCREEN_DETAIL_HEADERS
            )
            state_rows = table_rows_for_headers(
                ux_tables, UX_SCREEN_STATE_HEADERS
            )
            flow_rows = table_rows_for_headers(ux_tables, UX_FLOW_HEADERS)
            direction_rows = table_rows_for_headers(
                ux_tables, UX_DIRECTION_HEADERS
            )
            for label, rows in (
                ("inventario de pantallas", screen_rows),
                ("detalle por pantalla", detail_rows),
                ("estados por pantalla", state_rows),
                ("flujos", flow_rows),
                ("dirección visual", direction_rows),
            ):
                if rows is None:
                    report.errors.append(
                        f"{expected_ux_path}: debe existir exactamente una tabla de {label}."
                    )

            confirmed_screens: set[str] = set()
            if screen_rows is not None:
                for row in screen_rows:
                    screen_id = row.get("ID", "").strip()
                    if row.get("State") not in {"confirmed", "decision"}:
                        continue
                    confirmed_screens.add(screen_id)
                    for column in (
                        "Screen",
                        "Purpose",
                        "Users",
                        "Content",
                        "Main actions",
                        "Requirements",
                        "Acceptance",
                        "Increment",
                    ):
                        if not _meaningful_cell(row.get(column, "")):
                            report.errors.append(
                                f"{expected_ux_path}: {screen_id} confirmed requiere {column}."
                            )

            def screen_rows_by_reference(
                rows: list[dict[str, str]] | None, label: str
            ) -> dict[str, list[dict[str, str]]]:
                grouped: dict[str, list[dict[str, str]]] = {}
                for row in rows or []:
                    references_in_cell = [
                        item
                        for item in id_re.findall(row.get("Screen", ""))
                        if item.startswith("UX-")
                    ]
                    if len(references_in_cell) != 1:
                        report.errors.append(
                            f"{expected_ux_path}: cada fila de {label} debe enlazar exactamente una pantalla UX-###."
                        )
                        continue
                    screen_id = references_in_cell[0]
                    screen = definitions.get(screen_id)
                    if screen is None or "Screen" not in screen:
                        report.errors.append(
                            f"{expected_ux_path}: {label} enlaza una pantalla inexistente: {screen_id}."
                        )
                    grouped.setdefault(screen_id, []).append(row)
                return grouped

            detail_by_screen = screen_rows_by_reference(
                detail_rows, "detalle contractual"
            )
            states_by_screen = screen_rows_by_reference(
                state_rows, "estados"
            )
            strict_detail_columns = {
                "Entry and exit",
                "Information hierarchy",
                "Accessibility",
            }
            for screen_id in sorted(confirmed_screens):
                details = detail_by_screen.get(screen_id, [])
                states = states_by_screen.get(screen_id, [])
                if len(details) != 1:
                    report.errors.append(
                        f"{expected_ux_path}: {screen_id} confirmed requiere exactamente una fila de detalle contractual."
                    )
                else:
                    for column in UX_SCREEN_DETAIL_HEADERS[1:]:
                        value = details[0].get(column, "")
                        valid = (
                            _meaningful_cell(value)
                            and not value.strip().casefold().startswith("not-applicable")
                            if column in strict_detail_columns
                            else _meaningful_or_reasoned_na(value)
                        )
                        if not valid:
                            report.errors.append(
                                f"{expected_ux_path}: {screen_id} requiere detalle significativo en {column}."
                            )
                if len(states) != 1:
                    report.errors.append(
                        f"{expected_ux_path}: {screen_id} confirmed requiere exactamente una fila de estados."
                    )
                else:
                    for column in UX_SCREEN_STATE_HEADERS[1:]:
                        if not _meaningful_or_reasoned_na(states[0].get(column, "")):
                            report.errors.append(
                                f"{expected_ux_path}: {screen_id} requiere comportamiento o not-applicable: motivo para {column}."
                            )

            confirmed_flow_coverage: set[str] = set()
            if flow_rows is not None:
                for row in flow_rows:
                    if row.get("State") not in {"confirmed", "decision"}:
                        continue
                    flow_id = row.get("ID", "").strip()
                    for column in UX_FLOW_HEADERS[2:]:
                        if not _meaningful_or_reasoned_na(row.get(column, "")):
                            report.errors.append(
                                f"{expected_ux_path}: {flow_id} confirmed requiere {column}."
                            )
                    linked_screens = [
                        item
                        for item in id_re.findall(row.get("Screens", ""))
                        if item.startswith("UX-")
                    ]
                    if not linked_screens:
                        report.errors.append(
                            f"{expected_ux_path}: {flow_id} confirmed debe enlazar pantallas UX-###."
                        )
                    for screen_id in linked_screens:
                        if screen_id not in confirmed_screens:
                            report.errors.append(
                                f"{expected_ux_path}: {flow_id} enlaza una pantalla no confirmada: {screen_id}."
                            )
                        confirmed_flow_coverage.add(screen_id)
            for screen_id in sorted(confirmed_screens - confirmed_flow_coverage):
                report.errors.append(
                    f"{expected_ux_path}: {screen_id} confirmed no está cubierta por ningún flujo confirmado."
                )

            for increment_id in sorted(applicable_increments):
                contract_row = interface_by_increment[increment_id]
                contract_ids = {
                    item
                    for item in id_re.findall(contract_row.get("UX contract", ""))
                    if item.startswith("UX-")
                }
                if not contract_ids:
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id} applicable debe enumerar sus elementos UX-###."
                    )
                    continue
                contract_screens = {
                    item
                    for item in contract_ids
                    if "Screen" in definitions.get(item, {})
                    and definitions[item].get("State") in {"confirmed", "decision"}
                }
                contract_flows = {
                    item
                    for item in contract_ids
                    if "Flow or interaction" in definitions.get(item, {})
                    and definitions[item].get("State") in {"confirmed", "decision"}
                }
                covered_contract_screens: set[str] = set()
                for flow_id in contract_flows:
                    covered_contract_screens.update(
                        item
                        for item in id_re.findall(
                            definitions[flow_id].get("Screens", "")
                        )
                        if item in contract_screens
                    )
                for screen_id in sorted(
                    contract_screens - covered_contract_screens
                ):
                    report.errors.append(
                        f"ART-INCREMENTS: {increment_id}: {screen_id} no está cubierta por un flujo incluido en su contrato UX."
                    )

            if direction_rows is not None:
                for row in direction_rows:
                    if row.get("State") not in {"confirmed", "decision"}:
                        continue
                    direction_id = row.get("ID", "").strip()
                    for column in (
                        "Aspect",
                        "Proposal",
                        "Rationale",
                        "Constraints",
                        "Increment",
                    ):
                        if not _meaningful_or_reasoned_na(row.get(column, "")):
                            report.errors.append(
                                f"{expected_ux_path}: {direction_id} confirmed requiere {column}."
                            )
                    if not _explicit_human_validation(
                        row.get("Human validation", "")
                    ):
                        report.errors.append(
                            f"{expected_ux_path}: {direction_id} confirmed requiere validación humana con resultado, rol/alias, fecha y referencia ADR."
                        )
                    direction_decisions = [
                        item
                        for item in id_re.findall(row.get("Decision", ""))
                        if item.startswith("ADR-")
                    ]
                    if not direction_decisions:
                        report.errors.append(
                            f"{expected_ux_path}: {direction_id} confirmed requiere una decisión ADR-###."
                        )
                    validation_refs = re.findall(
                        r"(?:ref|reference|referencia)\s*=\s*(ADR-[0-9]{3})",
                        row.get("Human validation", ""),
                        re.IGNORECASE,
                    )
                    if validation_refs and not set(validation_refs).intersection(
                        direction_decisions
                    ):
                        report.errors.append(
                            f"{expected_ux_path}: {direction_id} no enlaza la misma ADR en Human validation y Decision."
                        )

        prototype_rows = table_rows_for_headers(
            ux_tables, VISUAL_PROTOTYPE_HEADERS
        )
        if prototype_rows is not None:
            seen_asset_paths: set[str] = set()
            ux_document = ux_entry.get("path", expected_ux_path)
            for row in prototype_rows:
                visual_id = row.get("ID", "").strip()
                if not re.fullmatch(r"VIS-[0-9]{3}", visual_id):
                    report.errors.append(
                        f"{expected_ux_path}: prototipo visual con ID inválido {visual_id!r}."
                    )
                    continue
                if schema_version != "1.0" and row.get("State") in {
                    "rejected",
                    "superseded",
                    "retired",
                }:
                    # Historical visual rows remain auditable through the common
                    # contract model, but their assets are not active inputs.
                    continue
                target, target_error = _markdown_image_target(row.get("Asset", ""))
                if target_error or target is None:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: {target_error}"
                    )
                    continue
                target_path = Path(target)
                if target_path.parts[:2] == ("docs", "lks-sdd"):
                    asset_relative = target_path.as_posix()
                else:
                    asset_relative = (
                        Path(ux_document).parent / target_path
                    ).as_posix()
                asset_path, path_error = _safe_relative_file(root, asset_relative)
                if path_error or asset_path is None:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: asset no permitido: {path_error}"
                    )
                    continue
                try:
                    asset_path.relative_to((root / VISUAL_ASSET_ROOT).resolve())
                except ValueError:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: el asset debe estar bajo {VISUAL_ASSET_ROOT.as_posix()}/."
                    )
                    continue
                normalized_relative = asset_path.relative_to(root).as_posix()
                if normalized_relative in seen_asset_paths:
                    report.errors.append(
                        f"{expected_ux_path}: asset visual duplicado: {normalized_relative}"
                    )
                seen_asset_paths.add(normalized_relative)
                if not asset_path.is_file():
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: falta el asset {normalized_relative}."
                    )
                    continue
                if normalized_relative not in report.checked_files:
                    report.checked_files.append(normalized_relative)
                extension = asset_path.suffix.casefold()
                if extension not in {".png", ".jpg", ".jpeg"}:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: extensión visual no admitida {extension!r}."
                    )
                actual_format, dimensions = _image_signature(asset_path)
                declared_format = row.get("Format", "").strip().upper()
                normalized_declared = "JPEG" if declared_format in {"JPG", "JPEG"} else declared_format
                if actual_format is None:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: firma PNG/JPEG inválida o imagen truncada."
                    )
                elif normalized_declared != actual_format:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Format={declared_format!r} no coincide con {actual_format}."
                    )
                if not _meaningful_cell(row.get("Viewport", "")):
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Viewport es obligatorio."
                    )
                linked_ux = id_re.findall(row.get("Screens or flow", ""))
                linked_ux = [item for item in linked_ux if item.startswith("UX-")]
                if not linked_ux:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Screens or flow debe enlazar UX-###."
                    )
                linked_requirements = [
                    item
                    for item in id_re.findall(row.get("Requirements", ""))
                    if item.startswith(("FR-", "NFR-", "TR-"))
                ]
                if not linked_requirements:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Requirements debe enlazar FR/NFR/TR-###."
                    )
                if not _meaningful_cell(row.get("Source", "")):
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Source es obligatorio."
                    )
                elif "imagegen" not in row.get("Source", "").casefold():
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Source debe declarar ImageGen."
                    )
                generated_on = row.get("Generated on", "").strip()
                try:
                    date.fromisoformat(generated_on)
                except ValueError:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Generated on debe usar una fecha real YYYY-MM-DD."
                    )
                if not _meaningful_cell(row.get("Prompt or brief", "")):
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: Prompt or brief es obligatorio."
                    )
                expected_hash = row.get("SHA-256", "").strip().casefold()
                actual_hash = hashlib.sha256(asset_path.read_bytes()).hexdigest()
                if not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: SHA-256 debe contener 64 hexadecimales."
                    )
                elif expected_hash != actual_hash:
                    report.errors.append(
                        f"{expected_ux_path}: {visual_id}: SHA-256 no coincide con el asset."
                    )
                visual_definition = definitions.get(visual_id)
                if visual_definition is not None:
                    visual_definition["_asset_path"] = normalized_relative
                    visual_definition["_asset_format"] = actual_format or "invalid"
                    visual_definition["_asset_sha256"] = actual_hash
                    if dimensions is not None:
                        visual_definition["_asset_dimensions"] = (
                            f"{dimensions[0]}x{dimensions[1]}"
                        )
                if row.get("State") == "confirmed":
                    if not _explicit_human_validation(
                        row.get("Human validation", "")
                    ):
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} confirmed requiere validación humana con resultado, rol/alias, fecha y referencia ADR."
                        )
                    if not _meaningful_cell(row.get("Confirmation scope", "")):
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} confirmed requiere delimitar Confirmation scope."
                        )
                    if not _meaningful_or_reasoned_na(row.get("Limitations", "")):
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} confirmed requiere declarar Limitations."
                        )
                    decision_ids = [
                        item
                        for item in id_re.findall(row.get("Decision", ""))
                        if item.startswith("ADR-")
                    ]
                    if not decision_ids:
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} confirmed requiere una decisión ADR-###."
                        )
                    validation_refs = re.findall(
                        r"(?:ref|reference|referencia)\s*=\s*(ADR-[0-9]{3})",
                        row.get("Human validation", ""),
                        re.IGNORECASE,
                    )
                    if validation_refs and not set(validation_refs).intersection(
                        decision_ids
                    ):
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} no enlaza la misma ADR en Human validation y Decision."
                        )
                    for decision_id in decision_ids:
                        decision = definitions.get(decision_id)
                        if decision is None or decision.get("State") not in {
                            "decision",
                            "confirmed",
                        }:
                            report.errors.append(
                                f"{expected_ux_path}: {visual_id} enlaza una decisión no confirmada: {decision_id}."
                            )
                    increment_ids = [
                        item
                        for item in id_re.findall(row.get("Increment", ""))
                        if item.startswith("INC-")
                    ]
                    if not increment_ids:
                        report.errors.append(
                            f"{expected_ux_path}: {visual_id} confirmed debe enlazar INC-###."
                        )

    delivery_contract: dict[str, Any] | None = None
    if schema_version in {"1.2", "1.3", "1.4", "1.5"}:
        from delivery_engine import validate_delivery_contract

        delivery_contract = validate_delivery_contract(root, manifest)

    evidence_cache: dict[str, Any] = {}
    index_defined_ids = {
        str(item.get("binding_id"))
        for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict) and item.get("binding_id")
    }
    for relative, reference in references:
        if reference in definitions or reference in index_defined_ids:
            continue
        if reference.startswith("EVID-"):
            evidence_relative = f"docs/lks-sdd/evidence/{reference}.json"
            evidence_path, path_error = _safe_relative_file(root, evidence_relative)
            if path_error or evidence_path is None:
                report.errors.append(
                    f"{relative}: evidencia {reference} en ruta no permitida: {path_error}"
                )
                continue
            if reference not in evidence_cache:
                try:
                    evidence_cache[reference] = json.loads(
                        evidence_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    evidence_cache[reference] = None
            evidence = evidence_cache[reference]
            evidence_errors = evidence_document_errors(evidence, reference)
            if isinstance(evidence, dict):
                evidence_increment_id = str(evidence.get("increment", ""))
                evidence_increment = definitions.get(evidence_increment_id)
                if evidence_increment is None or not evidence_increment.get(
                    "path", ""
                ).endswith("increments.md"):
                    evidence_errors.append(
                        "increment no referencia un incremento definido"
                    )
                evidence_errors.extend(
                    evidence_profile_identity_errors(evidence, manifest)
                )
                checks = evidence.get("checks", [])
                visual_checks = [
                    check
                    for check in checks
                    if isinstance(check, dict)
                    and check.get("name") == "visual-browser-review"
                ] if isinstance(checks, list) else []
                interface_row = interface_by_increment.get(evidence_increment_id)
                applicability = (
                    interface_applicability(
                        interface_row.get("Interface applicability", "")
                    )[0]
                    if interface_row is not None
                    else None
                )
                task_ids = evidence.get("task_ids")
                if task_ids is None and evidence.get("schema_version") in {None, "1.2"}:
                    if (
                        increments_v06_contract
                        and applicability == "applicable"
                        and evidence.get("classification")
                        in {"verified", "verified-with-reservations"}
                    ):
                        if len(visual_checks) != 1 or visual_checks[0].get("status") != "passed":
                            evidence_errors.append(
                                "un incremento con interfaz applicable requiere exactamente un check visual-browser-review ejecutado y passed"
                            )
                elif not isinstance(task_ids, list) or not task_ids or not all(
                    isinstance(item, str) for item in task_ids
                ):
                    evidence_errors.append("task_ids debe identificar el TASK slice")
                elif delivery_contract is not None:
                    unknown_tasks = sorted(
                        set(task_ids) - set(delivery_contract.get("tasks", {}))
                    )
                    wrong_increment = sorted(
                        task_id
                        for task_id in task_ids
                        if delivery_contract.get("tasks", {}).get(task_id, {}).get("Increment")
                        != evidence_increment_id
                    )
                    if unknown_tasks:
                        evidence_errors.append(
                            "task_ids referencia tareas inexistentes: "
                            + ", ".join(unknown_tasks)
                        )
                    if wrong_increment:
                        evidence_errors.append(
                            "task_ids contiene tareas de otro incremento: "
                            + ", ".join(wrong_increment)
                        )
                    if not unknown_tasks and not wrong_increment:
                        expected_applicability = visual_gate_applicability(
                            task_ids,
                            delivery_contract,
                            release_interface_applicable=(
                                increments_v06_contract
                                and applicability == "applicable"
                            ),
                        )
                        evidence_errors.extend(
                            evidence_gate_applicability_errors(
                                evidence, expected_applicability
                            )
                        )
                for check in visual_checks:
                    if (
                        check.get("status") != "passed"
                    ):
                        continue
                    visual_path = check.get("evidence")
                    if not isinstance(visual_path, str):
                        evidence_errors.append(
                            "visual-browser-review no conserva la ruta de evidencia"
                        )
                        continue
                    visual_errors, visual_outcome, _, visual_checked = (
                        validate_visual_review_evidence(
                            root,
                            manifest,
                            definitions,
                            str(evidence.get("increment", "")),
                            visual_path,
                            require_fresh=False,
                        )
                    )
                    evidence_errors.extend(
                        f"visual-browser-review: {error}"
                        for error in visual_errors
                    )
                    if visual_outcome is not None:
                        for field in (
                            "evidence_sha256",
                            "baseline",
                            "screenshots",
                        ):
                            if check.get(field) != visual_outcome.get(field):
                                evidence_errors.append(
                                    f"visual-browser-review: {field} ya no coincide"
                                )
                    for checked in visual_checked:
                        if checked not in report.checked_files:
                            report.checked_files.append(checked)
            if evidence_errors:
                report.errors.extend(
                    f"{evidence_relative}: {error}" for error in evidence_errors
                )
                continue
            if evidence_relative not in report.checked_files:
                report.checked_files.append(evidence_relative)
            continue
        report.errors.append(f"{relative}: referencia sin definición: {reference}")

    for artifact_id, (expected_path, _) in CORE_ARTIFACTS.items():
        if artifact_id in V12_CORE_ARTIFACTS and schema_version not in {"1.2", "1.3", "1.4", "1.5"}:
            continue
        if artifact_id in V13_CORE_ARTIFACTS and schema_version not in {"1.3", "1.4", "1.5"}:
            continue
        if artifact_id in V14_CORE_ARTIFACTS and schema_version not in {"1.4", "1.5"}:
            continue
        entry = artifact_entries.get(artifact_id)
        if entry is None:
            report.errors.append(
                f"Falta el artefacto del núcleo en el índice: {artifact_id}"
            )
            continue
        if entry.get("path") != expected_path:
            report.errors.append(
                f"{artifact_id}: la ruta canónica debe ser {expected_path!r}, no {entry.get('path')!r}."
            )
        if entry.get("required") is not True:
            report.errors.append(
                f"{artifact_id}: el artefacto del núcleo debe ser obligatorio."
            )

    if schema_version == "1.0":
        indexed_blockers = set(manifest.get("open_blockers", []))
        for blocker_id in indexed_blockers:
            blocker = definitions.get(blocker_id)
            if blocker is None or not blocker.get("path", "").endswith("open-points.md"):
                report.errors.append(
                    f"El índice referencia un bloqueo sin definición en ART-OPEN: {blocker_id}"
                )
            elif blocker.get("State") not in {"open", "blocked"}:
                report.errors.append(
                    f"El bloqueo indexado {blocker_id} no está open ni blocked."
                )
            elif blocker.get("Blocking", "").strip().lower() != "true":
                report.errors.append(
                    f"El bloqueo indexado {blocker_id} no declara Blocking=true en ART-OPEN."
                )
        for item_id, item in definitions.items():
            if not item.get("path", "").endswith("open-points.md"):
                continue
            is_blocking = item.get("Blocking", "").strip().lower() == "true"
            is_open = item.get("State") in {"open", "blocked"}
            if is_blocking and is_open and item_id not in indexed_blockers:
                report.errors.append(
                    f"El bloqueo {item_id} está activo en ART-OPEN pero no aparece en el índice."
                )

    technology = manifest.get("technology", {})
    selected_profile = (
        technology.get("selected_profile") if isinstance(technology, dict) else None
    )
    selection_decision = (
        technology.get("selection_decision") if isinstance(technology, dict) else None
    )
    if selected_profile is not None and selection_decision is None:
        report.errors.append(
            "Un perfil seleccionado requiere selection_decision en el índice."
        )
    if (
        selected_profile is not None
        and technology.get("preferred_stack_assessed") is not True
    ):
        report.errors.append(
            "Un perfil seleccionado requiere preferred_stack_assessed=true."
        )
    if selection_decision is not None:
        decision = definitions.get(selection_decision)
        if selected_profile is None:
            report.errors.append(
                "selection_decision no puede existir sin selected_profile."
            )
        if decision is None or decision.get("artifact_type") not in {
            "solution-overview",
            "architecture-decision",
        }:
            report.errors.append(
                f"La decisión de perfil {selection_decision} no está definida en un artefacto de solución o ADR."
            )
        elif decision.get("State") not in {"decision", "confirmed"}:
            report.errors.append(
                f"La decisión de perfil {selection_decision} no está confirmada; estado: {decision.get('State')}."
            )
        elif selected_profile is not None and selected_profile not in " ".join(
            str(value) for value in decision.values()
        ):
            report.errors.append(
                f"La decisión {selection_decision} no identifica el perfil seleccionado {selected_profile}."
            )
    if schema_version in {"1.2", "1.3", "1.4", "1.5"} and isinstance(technology, dict):
        bindings = technology.get("profile_bindings", [])
        if bindings and technology.get("preferred_stack_assessed") is not True:
            report.errors.append(
                "Los profile_bindings requieren preferred_stack_assessed=true."
            )
        for binding in bindings if isinstance(bindings, list) else []:
            if not isinstance(binding, dict) or binding.get("state") != "confirmed":
                continue
            binding_id = binding.get("binding_id")
            decision_id = binding.get("selection_decision")
            profile_id = binding.get("profile_id")
            decision = definitions.get(decision_id)
            if decision is None or decision.get("artifact_type") not in {
                "solution-overview",
                "architecture-decision",
            }:
                report.errors.append(
                    f"{binding_id}: la ADR {decision_id} no está definida en solución."
                )
            elif decision.get("State") not in {"decision", "confirmed"}:
                report.errors.append(
                    f"{binding_id}: la ADR {decision_id} no está confirmada."
                )
            elif profile_id not in " ".join(str(value) for value in decision.values()):
                report.errors.append(
                    f"{binding_id}: la ADR {decision_id} no identifica {profile_id}."
                )

    for field_name, increment_id in (
        ("active_increment", manifest.get("active_increment")),
        (
            "readiness.assessed_increment",
            manifest.get("readiness", {}).get("assessed_increment"),
        ),
    ):
        if increment_id is None:
            continue
        increment = definitions.get(increment_id)
        if increment is None or not increment.get("path", "").endswith("increments.md"):
            report.errors.append(
                f"{field_name} referencia un incremento no definido: {increment_id}"
            )

    if manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption")
        if not isinstance(adoption, dict):
            report.errors.append("La ruta adopt-existing requiere el bloque adoption.")
        for artifact_id, (expected_path, _) in ADOPTION_ARTIFACTS.items():
            entry = artifact_entries.get(artifact_id)
            if entry is None:
                report.errors.append(
                    f"Falta el artefacto de adopción en el índice: {artifact_id}"
                )
                continue
            if entry.get("path") != expected_path or entry.get("required") is not True:
                report.errors.append(
                    f"{artifact_id}: ruta o obligatoriedad de adopción inválida."
                )
    elif "adoption" in manifest:
        report.warnings.append("La ruta new no necesita un bloque adoption.")

    if delivery_contract is not None:
        delivery = delivery_contract
        report.errors.extend(
            f"Contrato de entrega: {item}" for item in delivery["errors"]
        )
        report.warnings.extend(
            f"Contrato de entrega: {item}" for item in delivery["warnings"]
        )
        report.checked_files.extend(delivery["checked_files"])

    if schema_version in {"1.4", "1.5"}:
        from task_tracking_engine import validate_tracking_contract

        tracking = validate_tracking_contract(root, manifest)
        report.errors.extend(
            f"Contrato de tracking: {item}" for item in tracking["errors"]
        )
        report.warnings.extend(
            f"Contrato de tracking: {item}" for item in tracking["warnings"]
        )
        report.checked_files.extend(tracking["checked_files"])

    contract_model = build_project_model(root)
    legacy_errors = list(report.errors)
    backed_legacy_errors: set[int] = set()
    contract_diagnostics: list[Diagnostic] = []
    for item in contract_model.diagnostics:
        if schema_version != "1.0" or item.severity != "error":
            contract_diagnostics.append(item)
            continue
        legacy_error_index = _legacy_error_backing_diagnostic(item, legacy_errors)
        if legacy_error_index is None:
            contract_diagnostics.append(replace(item, severity="warning"))
        else:
            backed_legacy_errors.add(legacy_error_index)
            contract_diagnostics.append(item)
    report.diagnostics = [item.as_dict() for item in contract_diagnostics]
    if schema_version == "1.0":
        report.diagnostics.extend(
            {
                "code": "LKS-LEGACY-VALIDATION",
                "severity": "error",
                "stage": "structure",
                "message": error,
                "location": {},
                "cause": "legacy-validator",
            }
            for index, error in enumerate(legacy_errors)
            if index not in backed_legacy_errors
        )
        diagnostic_counts: dict[str, int] = {}
        for item in contract_diagnostics:
            if item.severity != "warning":
                continue
            diagnostic_counts[item.code] = diagnostic_counts.get(item.code, 0) + 1
        compatibility_warnings = [
            f"[{code}] Compatibilidad 1.0: {count} incidencia(s); "
            "consulte diagnostics para ubicaciones y migre a 1.1 para aplicar "
            "el contrato estricto."
            for code, count in sorted(diagnostic_counts.items())
        ]
        report.warnings = list(
            dict.fromkeys([*report.warnings, *compatibility_warnings])
        )
    else:
        messages = legacy_messages(contract_diagnostics)
        report.errors = list(dict.fromkeys([*report.errors, *messages["errors"]]))
        report.warnings = list(
            dict.fromkeys([*report.warnings, *messages["warnings"]])
        )
    report.checked_files = list(
        dict.fromkeys([*report.checked_files, *contract_model.checked_files])
    )

    return report, manifest, definitions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, _, _ = validate_project(args.project_root)
    if args.as_json:
        print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    else:
        print("VALID" if report.valid else "INVALID")
        print(f"Checked files: {len(report.checked_files)}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        for error in report.errors:
            print(f"ERROR: {error}")
    return 0 if report.valid else 2


if __name__ == "__main__":
    sys.exit(main())
