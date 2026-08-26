#!/usr/bin/env python3
"""Preview, apply, or roll back supported LKS-SDD schema migrations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validate_project import validate_project
from delivery_engine import TASK_HEADERS, parse_tables

LATEST_SCHEMA = "1.5"
PLUGIN_VERSION = "0.12.0"
METHOD_VERSION = "1.5.0"
V14_PLUGIN_VERSION = "0.10.0"
V14_METHOD_VERSION = "1.4.0"
V13_PLUGIN_VERSION = "0.9.1"
V13_METHOD_VERSION = "1.3.0"
V12_PLUGIN_VERSION = "0.8.0"
V12_METHOD_VERSION = "1.2.0"
V11_PLUGIN_VERSION = "0.7.0"
V11_METHOD_VERSION = "1.1.0"
RECORD_NAME = "migration-record.json"
SUPPORTED_MIGRATIONS = {
    ("0.9", "1.0"), ("1.0", "1.1"), ("1.1", "1.2"), ("1.2", "1.3"),
    ("1.3", "1.4"), ("1.4", "1.5")
}

V12_ARTIFACTS = (
    ("ART-ARCH", "docs/lks-sdd/03-solution/architecture.md"),
    ("ART-GOVERNANCE", "docs/lks-sdd/04-delivery/delivery-governance.md"),
    ("ART-PLANS", "docs/lks-sdd/04-delivery/plans.md"),
    ("ART-TASKS", "docs/lks-sdd/04-delivery/tasks.md"),
    ("ART-TEST-STRATEGY", "docs/lks-sdd/05-quality/test-strategy.md"),
    ("ART-DEPLOYMENT", "docs/lks-sdd/06-operation/deployment.md"),
)
V13_ARTIFACTS = (
    ("ART-PLANNING", "docs/lks-sdd/04-delivery/planning-coverage.md"),
)
V14_ARTIFACTS = (
    ("ART-TRACKING", "docs/lks-sdd/04-delivery/task-tracking.md"),
)

LEGACY_STATE_MAP = {
    "proposal": "proposed",
    "decision": "confirmed",
    "fact": "draft",
    "requirement": "draft",
    "assumption": "draft",
    "not-applicable": "draft",
}
REVIEW_STATES = {"fact", "requirement", "assumption", "not-applicable"}
EPISTEMIC_ARTIFACT_TYPES = {
    "repository-inventory",
    "observed-architecture",
    "observed-behavior",
    "gaps-and-unknowns",
    "reconciliation",
}
REFERENCE_TO_LABEL_ARTIFACT_TYPES = {
    "architecture",
    "deployment",
    "observability",
    "operations",
}
INCREMENTS_10_HEADERS = (
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
INCREMENTS_11_HEADERS = (
    "ID",
    "State",
    "In scope",
    "Out of scope",
    "Requirements",
    "Acceptance",
    "Decisions",
    "Tests",
)
DOMAIN_HEADERS = ("Increment", "Domain", "Applicability", "References", "Reason")
TEST_STRATEGY_10_HEADERS = (
    "ID",
    "State",
    "Level or type",
    "Scope",
    "Acceptance",
    "Environment",
    "Evidence",
)
TEST_STRATEGY_11_HEADERS = (
    "Test",
    "Level or type",
    "Scope",
    "Acceptance",
    "Environment",
    "Evidence",
)
RANGE_RE = re.compile(
    r"\b(?P<left>(?P<prefix>[A-Z][A-Z0-9]*)-[0-9]{3})\s+[aA]\s+"
    r"(?P<right>(?P=prefix)-[0-9]{3})\b"
)
ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*-[0-9]{3}\b")


class MigrationError(Exception):
    """Expected, actionable migration failure."""


@dataclass
class PlannedChange:
    path: Path
    before: bytes
    after: bytes
    operations: list[str] = field(default_factory=list)
    created: bool = False
    delete: bool = False


@dataclass
class MigrationPlan:
    status: str
    source_schema: str
    target_schema: str
    changes: list[PlannedChange]
    human_review_required: list[dict[str, str]] = field(default_factory=list)


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise MigrationError(f"La raíz no existe o no es una carpeta: {root}")
    return root


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _relative_path(root: Path, candidate: Path) -> Path:
    """Return a safe relative path, including on Windows 8.3/long-name aliases."""
    try:
        return candidate.relative_to(root)
    except ValueError:
        pass
    for ancestor in (candidate, *candidate.parents):
        try:
            if ancestor.exists() and os.path.samefile(ancestor, root):
                return Path(*candidate.parts[len(ancestor.parts) :])
        except OSError:
            continue
    raise ValueError(f"{candidate} is outside {root}")


def _safe_artifact(root: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise MigrationError(f"Ruta de artefacto no permitida: {relative}")
    current = root
    for part in requested.parts:
        current = current / part
        if _is_link_like(current):
            raise MigrationError(f"El artefacto usa un enlace simbólico: {relative}")
    candidate = (root / requested).resolve()
    try:
        _relative_path(root, candidate)
    except ValueError as exc:
        raise MigrationError(f"Ruta de artefacto fuera de la raíz: {relative}") from exc
    if not candidate.is_file():
        raise MigrationError(f"El artefacto no es un archivo regular: {relative}")
    return candidate


def _safe_new_artifact(root: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise MigrationError(f"Ruta de artefacto no permitida: {relative}")
    current = root
    for part in requested.parts:
        current = current / part
        if current.exists() and _is_link_like(current):
            raise MigrationError(f"El artefacto usa un enlace simbólico: {relative}")
    candidate = (root / requested).resolve(strict=False)
    try:
        _relative_path(root, candidate)
    except ValueError as exc:
        raise MigrationError(f"Ruta de artefacto fuera de la raíz: {relative}") from exc
    if candidate.exists():
        raise MigrationError(
            f"Existe {relative} pero no está indexado; reconcilie la colisión manualmente."
        )
    return candidate


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def _frontmatter_bounds(lines: list[str], relative: str) -> tuple[int, int]:
    if not lines or lines[0].strip() != "---":
        raise MigrationError(f"Front matter ausente: {relative}")
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise MigrationError(f"Front matter sin cierre: {relative}") from exc
    return 1, end


def _frontmatter_value(lines: list[str], start: int, end: int, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*['\"]?(.*?)['\"]?\s*(?:\r?\n)?$")
    values = [
        match.group(1) for line in lines[start:end] if (match := pattern.match(line))
    ]
    if len(values) > 1:
        raise MigrationError(f"Front matter contiene {key} duplicado.")
    return values[0] if values else None


def _set_frontmatter_value(
    lines: list[str], start: int, end: int, key: str, value: str, relative: str
) -> None:
    pattern = re.compile(rf"^({re.escape(key)}:\s*).*(\r?\n)?$")
    matches = [index for index in range(start, end) if pattern.match(lines[index])]
    if len(matches) != 1:
        raise MigrationError(
            f"{relative}: se esperaba exactamente un {key} en front matter."
        )
    index = matches[0]
    match = pattern.match(lines[index])
    assert match is not None
    lines[index] = f'{match.group(1)}"{value}"{_line_ending(lines[index])}'


def _review_entry(
    relative: str, location: str, original: str, migrated: str, reason: str
) -> dict[str, str]:
    return {
        "path": relative,
        "location": location,
        "original": original,
        "migrated": migrated,
        "reason": reason,
    }


def _map_state(
    value: str,
    relative: str,
    location: str,
    reviews: list[dict[str, str]],
) -> str:
    normalized = value.strip().casefold()
    migrated = LEGACY_STATE_MAP.get(normalized, value.strip())
    if normalized in REVIEW_STATES:
        reason = (
            "La aplicabilidad 1.0 no equivale a un estado de ciclo de vida; se conserva como draft hasta revision humana."
            if normalized == "not-applicable"
            else "El estado epistemico 1.0 no demuestra confirmacion; se conserva como draft hasta revision humana."
        )
        reviews.append(
            _review_entry(
                relative,
                location,
                value.strip(),
                migrated,
                reason,
            )
        )
    return migrated


def _table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _is_separator(cells: list[str] | None) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _format_row(cells: list[str], newline: str) -> str:
    return "| " + " | ".join(cells) + " |" + newline


def _normalize_ranges(text: str) -> str:
    return RANGE_RE.sub(
        lambda match: f"{match.group('left')}..{match.group('right')}", text
    )


def _reason_excerpt(value: str) -> str:
    collapsed = " ".join(value.replace("|", "/").split())
    return collapsed if collapsed else "sin contenido"


def _legacy_domain_row(
    relative: str,
    increment_id: str,
    domain: str,
    original: str,
    prefixes: set[str],
    reviews: list[dict[str, str]],
) -> list[str]:
    value = _normalize_ranges(original.strip())
    lowered = value.casefold()
    location = f"increment {increment_id}, domain {domain}"
    if lowered.startswith("not-applicable"):
        _, separator, reason = value.partition(":")
        if separator and reason.strip():
            return [increment_id, domain, "not-applicable", "", reason.strip()]
        reviews.append(
            _review_entry(
                relative,
                location,
                original,
                "not-applicable",
                "La no aplicabilidad 1.0 no incluia motivo; debe justificarse humanamente.",
            )
        )
        return [
            increment_id,
            domain,
            "pending",
            "",
            "La no aplicabilidad 1.0 carecia de motivo; requiere revision humana.",
        ]
    if lowered == "pending" or lowered.startswith("pending:"):
        _, separator, reason = value.partition(":")
        detail = (
            reason.strip()
            if separator and reason.strip()
            else "Pendiente ya declarado en schema 1.0."
        )
        return [increment_id, domain, "pending", "", detail]
    references = [
        item for item in ID_RE.findall(value) if item.split("-", 1)[0] in prefixes
    ]
    unexpected = [
        item for item in ID_RE.findall(value) if item.split("-", 1)[0] not in prefixes
    ]
    if references and not unexpected:
        return [
            increment_id,
            domain,
            "applicable",
            value,
            f"Migrado de la columna {domain} del schema 1.0.",
        ]
    reviews.append(
        _review_entry(
            relative,
            location,
            original,
            "pending",
            "No hay una referencia inequívoca del dominio; no se infiere aplicabilidad.",
        )
    )
    return [
        increment_id,
        domain,
        "pending",
        "",
        f"Valor 1.0 no asignable automaticamente ({_reason_excerpt(value)}); requiere revision humana.",
    ]


def _ambiguous_identity_rows(
    increment_id: str,
    original: str,
) -> list[list[str]]:
    excerpt = _reason_excerpt(_normalize_ranges(original.strip()))
    reason = (
        "La columna Identity de schema 1.0 no distinguia identidad, seguridad y privacidad; "
        "se traslada a pending sin inferir referencias activas; "
        f"valor anterior: {excerpt}."
    )
    return [
        [increment_id, domain, "pending", "", reason]
        for domain in ("identity", "security", "privacy")
    ]


def _migrate_tables_1_1(
    lines: list[str],
    body_start: int,
    relative: str,
    artifact_type: str,
    reviews: list[dict[str, str]],
) -> tuple[list[str], list[str]]:
    operations: list[str] = []
    output = lines[:body_start]
    index = body_start
    while index < len(lines):
        header = _table_cells(lines[index])
        separator = _table_cells(lines[index + 1]) if index + 1 < len(lines) else None
        if (
            header is None
            or not _is_separator(separator)
            or len(header) != len(separator or [])
        ):
            output.append(_normalize_ranges(lines[index]))
            index += 1
            continue
        row_end = index + 2
        while row_end < len(lines) and _table_cells(lines[row_end]) is not None:
            row_end += 1
        rows = [_table_cells(line) or [] for line in lines[index + 2 : row_end]]
        newline = _line_ending(lines[index]) or "\n"
        original_header = tuple(header)
        if original_header == DOMAIN_HEADERS:
            raise MigrationError(
                f"{relative}: schema 1.0 ya contiene la tabla de dominios 1.1; requiere reconciliacion manual."
            )
        if artifact_type == "increments" and original_header == INCREMENTS_10_HEADERS:
            domain_rows: list[list[str]] = []
            migrated_rows: list[list[str]] = []
            for row_number, row in enumerate(rows, 1):
                if len(row) != len(INCREMENTS_10_HEADERS):
                    raise MigrationError(
                        f"{relative}: fila {row_number} de incrementos tiene {len(row)} celdas; se esperaban {len(INCREMENTS_10_HEADERS)}."
                    )
                row[1] = _map_state(
                    row[1], relative, f"table increments row {row_number}", reviews
                )
                increment_id = row[0].strip()
                migrated_rows.append([*row[:7], row[10]])
                domain_rows.append(
                    _legacy_domain_row(
                        relative, increment_id, "data", row[7], {"DATA"}, reviews
                    )
                )
                domain_rows.extend(
                    _ambiguous_identity_rows(increment_id, row[8])
                )
                domain_rows.append(
                    _legacy_domain_row(
                        relative, increment_id, "integrations", row[9], {"INT"}, reviews
                    )
                )
            output.append(_format_row(list(INCREMENTS_11_HEADERS), newline))
            output.append(_format_row(["---"] * len(INCREMENTS_11_HEADERS), newline))
            output.extend(
                _format_row(
                    [_normalize_ranges(cell) for cell in row],
                    _line_ending(lines[index + 2 + offset]) or newline,
                )
                for offset, row in enumerate(migrated_rows)
            )
            output.extend(
                [
                    newline,
                    "## Aplicabilidad por dominio" + newline,
                    newline,
                    _format_row(list(DOMAIN_HEADERS), newline),
                    _format_row(["---"] * len(DOMAIN_HEADERS), newline),
                ]
            )
            output.extend(_format_row(row, newline) for row in domain_rows)
            operations.extend(
                ["increments-main-table-1.1", "domain-applicability-table"]
            )
            index = row_end
            continue
        if (
            artifact_type == "test-strategy"
            and original_header == TEST_STRATEGY_10_HEADERS
        ):
            migrated_rows = []
            for row_number, row in enumerate(rows, 1):
                if len(row) != len(TEST_STRATEGY_10_HEADERS):
                    raise MigrationError(
                        f"{relative}: fila {row_number} de estrategia de pruebas invalida."
                    )
                _map_state(
                    row[1], relative, f"table test-strategy row {row_number}", reviews
                )
                migrated_rows.append([row[0], *row[2:]])
            output.append(_format_row(list(TEST_STRATEGY_11_HEADERS), newline))
            output.append(_format_row(["---"] * len(TEST_STRATEGY_11_HEADERS), newline))
            output.extend(
                _format_row(
                    [_normalize_ranges(cell) for cell in row],
                    _line_ending(lines[index + 2 + offset]) or newline,
                )
                for offset, row in enumerate(migrated_rows)
            )
            operations.append("test-detail-reference-table")
            index = row_end
            continue
        migrated_header = list(header)
        if (
            artifact_type in REFERENCE_TO_LABEL_ARTIFACT_TYPES
            and migrated_header
            and migrated_header[0] == "Reference"
        ):
            migrated_header[0] = "Label"
            operations.append("reference-header-to-label")
        state_index = (
            migrated_header.index("State") if "State" in migrated_header else None
        )
        output.append(_format_row(migrated_header, newline))
        output.append(
            _format_row(
                ["---"] * len(migrated_header),
                _line_ending(lines[index + 1]) or newline,
            )
        )
        for row_number, (source_line, row) in enumerate(
            zip(lines[index + 2 : row_end], rows), 1
        ):
            if len(row) != len(header):
                raise MigrationError(
                    f"{relative}: fila {row_number} de tabla {header!r} tiene un numero de celdas invalido."
                )
            if (
                state_index is not None
                and artifact_type not in EPISTEMIC_ARTIFACT_TYPES
            ):
                row[state_index] = _map_state(
                    row[state_index],
                    relative,
                    f"table {header[0]} row {row_number}",
                    reviews,
                )
            output.append(
                _format_row(
                    [_normalize_ranges(cell) for cell in row],
                    _line_ending(source_line) or newline,
                )
            )
        index = row_end
    if artifact_type == "increments" and "domain-applicability-table" not in operations:
        raise MigrationError(
            f"{relative}: no se encontro la tabla principal de incrementos schema 1.0."
        )
    return output, operations


def _migrate_markdown_09_to_10(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "0.9":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 0.9 en front matter."
        )
    _set_frontmatter_value(lines, start, end, "schema_version", "1.0", relative)
    return "".join(lines).encode("utf-8"), [], ["frontmatter-schema-version"]


def _migrate_markdown_10_to_11(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "1.0":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 1.0 en front matter."
        )
    artifact_type = _frontmatter_value(lines, start, end, "artifact_type")
    if not artifact_type:
        raise MigrationError(f"{relative}: artifact_type ausente en front matter.")
    reviews: list[dict[str, str]] = []
    _set_frontmatter_value(lines, start, end, "schema_version", "1.1", relative)
    _set_frontmatter_value(
        lines, start, end, "method_version", V11_METHOD_VERSION, relative
    )
    _set_frontmatter_value(
        lines, start, end, "created_with_plugin_version", V11_PLUGIN_VERSION, relative
    )
    status = _frontmatter_value(lines, start, end, "status")
    if status and status.casefold() in LEGACY_STATE_MAP:
        mapped = _map_state(status, relative, "frontmatter status", reviews)
        _set_frontmatter_value(lines, start, end, "status", mapped, relative)
    lines, operations = _migrate_tables_1_1(
        lines, end + 1, relative, artifact_type, reviews
    )
    return (
        "".join(lines).encode("utf-8"),
        reviews,
        ["frontmatter-contract-1.1", "legacy-range-normalization", *operations],
    )


def _migrate_markdown_11_to_12(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    """Upgrade metadata and add the explicit deployable-unit boundary.

    Existing prose and legacy component rows remain evidence.  The migration never
    guesses which legacy component is independently deployable or which exact
    profile should be bound to it.
    """

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "1.1":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 1.1 en front matter."
        )
    artifact_type = _frontmatter_value(lines, start, end, "artifact_type")
    if not artifact_type:
        raise MigrationError(f"{relative}: artifact_type ausente en front matter.")
    _set_frontmatter_value(lines, start, end, "schema_version", "1.2", relative)
    _set_frontmatter_value(
        lines, start, end, "method_version", V12_METHOD_VERSION, relative
    )
    _set_frontmatter_value(
        lines, start, end, "created_with_plugin_version", V12_PLUGIN_VERSION, relative
    )
    operations = ["frontmatter-contract-1.2"]
    migrated = "".join(lines)
    architecture_header = (
        "| Unit | State | Component | Responsibility | Runtime boundary | "
        "Interfaces | Data ownership | Requirements | Profile binding |"
    )
    if artifact_type == "architecture" and architecture_header not in migrated:
        newline = "\r\n" if "\r\n" in migrated else "\n"
        migrated = migrated.rstrip("\r\n") + newline * 2 + newline.join(
            (
                "## Unidades desplegables y fronteras de ejecución",
                "",
                architecture_header,
                "|---|---|---|---|---|---|---|---|---|",
                "",
                "La migración conserva los componentes anteriores, pero no infiere "
                "qué constituye una `UNIT-###` ni qué `BIND-###` le corresponde. "
                "Confirme esas fronteras antes de G2.",
                "",
            )
        )
        operations.append("architecture-unit-boundary")
    return migrated.encode("utf-8"), [], operations


def _migrate_markdown_12_to_13(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    """Add planning-continuity structure without inferring completion or evidence."""

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "1.2":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 1.2 en front matter."
        )
    artifact_type = _frontmatter_value(lines, start, end, "artifact_type")
    if not artifact_type:
        raise MigrationError(f"{relative}: artifact_type ausente en front matter.")
    _set_frontmatter_value(lines, start, end, "schema_version", "1.3", relative)
    _set_frontmatter_value(
        lines, start, end, "method_version", V13_METHOD_VERSION, relative
    )
    _set_frontmatter_value(
        lines,
        start,
        end,
        "created_with_plugin_version",
        V13_PLUGIN_VERSION,
        relative,
    )
    operations = ["frontmatter-contract-1.3"]
    migrated = "".join(lines)
    if artifact_type == "development-task":
        newline = "\r\n" if "\r\n" in migrated else "\n"
        additions: list[str] = []
        if "## Plan de ejecución verificable" not in migrated:
            additions.extend(
                [
                    "## Plan de ejecución verificable",
                    "",
                    "| Tests | Decisions and constraints | Risks and blockers | Responsible role | Review entry conditions | Definition of done | Required evidence | Integration points | Parallel constraints |",
                    "|---|---|---|---|---|---|---|---|---|",
                    "| pending | pending | pending | pending-assignment | pending | pending | pending | pending | pending |",
                    "",
                    "## Entregables",
                    "",
                    "| Deliverable | State | Acceptance | Tests | Evidence | Notes |",
                    "|---|---|---|---|---|---|",
                    "| pending | pending | pending | pending | pending | migration did not infer progress |",
                    "",
                ]
            )
            operations.append("task-executable-plan-pending")
        if "## Continuidad" not in migrated:
            additions.extend(
                [
                    "## Continuidad",
                    "",
                    "| Definition status | Current checkpoint | Authorization | Authorization scope | Specification fingerprint | Planning fingerprint | Next safe action |",
                    "|---|---|---|---|---|---|---|",
                    "| incomplete | none | none | none | pending | pending | complete and confirm the migrated task definition |",
                    "",
                ]
            )
            operations.append("task-continuity-pending")
        if additions:
            migrated = migrated.rstrip("\r\n") + newline * 2 + newline.join(additions)
    return migrated.encode("utf-8"), [], operations


def _migrate_markdown_13_to_14(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    """Adopt the 1.4 document contract without inferring external tracking."""

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "1.3":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 1.3 en front matter."
        )
    if not _frontmatter_value(lines, start, end, "artifact_type"):
        raise MigrationError(f"{relative}: artifact_type ausente en front matter.")
    _set_frontmatter_value(lines, start, end, "schema_version", "1.4", relative)
    _set_frontmatter_value(
        lines, start, end, "method_version", V14_METHOD_VERSION, relative
    )
    _set_frontmatter_value(
        lines, start, end, "created_with_plugin_version", V14_PLUGIN_VERSION, relative
    )
    return "".join(lines).encode("utf-8"), [], ["frontmatter-contract-1.4"]


def _migrate_markdown_14_to_15(
    content: bytes, relative: str
) -> tuple[bytes, list[dict[str, str]], list[str]]:
    """Add Jira milestone reporting policy without inferring external writes."""

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines, relative)
    if _frontmatter_value(lines, start, end, "schema_version") != "1.4":
        raise MigrationError(
            f"{relative}: se esperaba schema_version 1.4 en front matter."
        )
    _set_frontmatter_value(lines, start, end, "schema_version", "1.5", relative)
    _set_frontmatter_value(lines, start, end, "method_version", METHOD_VERSION, relative)
    _set_frontmatter_value(
        lines, start, end, "created_with_plugin_version", PLUGIN_VERSION, relative
    )
    migrated = "".join(lines)
    operations = ["frontmatter-contract-1.5"]
    if relative == "docs/lks-sdd/04-delivery/task-tracking.md":
        tables = parse_tables(migrated)
        binding_headers = (
            "Binding", "State", "Mode", "Provider", "Site", "Project",
            "Issue type", "Sync policy", "Write policy", "Decision", "Last reviewed",
        )
        binding_rows = [rows for headers, rows in tables if headers == binding_headers]
        if len(binding_rows) != 1 or len(binding_rows[0]) != 1:
            raise MigrationError("ART-TRACKING 1.4 no contiene un binding único.")
        binding = binding_rows[0][0]
        mode = binding.get("Mode", "pending")
        decision = binding.get("Decision", "pending: reporting scope not selected")
        reviewed = binding.get("Last reviewed", datetime.now(UTC).date().isoformat())
        if mode == "repository-only":
            reporting = (
                f"| RPT-001 | confirmed | not-applicable | not-required | "
                f"not-applicable | {decision} | {reviewed} |"
            )
        elif mode == "jira-hybrid":
            reporting = (
                f"| RPT-001 | confirmed | projection-only | "
                f"{binding.get('Sync policy', 'required-before-execution')} | "
                f"not-applicable | {decision} | {reviewed} |"
            )
        else:
            reporting = (
                f"| RPT-001 | proposed | pending | pending | pending | "
                f"pending: reporting scope not selected | {reviewed} |"
            )
        newline = "\r\n" if "\r\n" in migrated else "\n"
        additions = [
            "## Reporting policy",
            "",
            "| Reporting | State | Scope | Coordination gate | Comment policy | Decision | Last reviewed |",
            "|---|---|---|---|---|---|---|",
            reporting,
            "",
            "## Workflow mapping",
            "",
            "| Local state | State | Jira status ID | Jira status name | Decision | Last reviewed |",
            "|---|---|---|---|---|---|",
            "",
            "## Milestone operations",
            "",
            "| ID | State | Task | Source ref | Event kind | Action | Event hash | Preview hash | Duplicate check | Authorized by role | Authorized on | External ID | External key | Recorded on | Result | Notes |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            "",
        ]
        migrated = migrated.rstrip("\r\n") + newline * 2 + newline.join(additions)
        operations.append("jira-reporting-policy-defaulted-without-write")
    return migrated.encode("utf-8"), [], operations


def _render_v12_template(
    root: Path, relative: str, project_id: str, baseline_id: str, today: str
) -> bytes:
    template_relative = relative.removeprefix("docs/lks-sdd/")
    template = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "lks-sdd-define"
        / "assets"
        / "templates"
        / template_relative
    )
    if not template.is_file():
        raise MigrationError(f"Falta la plantilla 1.2 empaquetada: {template_relative}")
    text = template.read_text(encoding="utf-8")
    text = re.sub(
        r'^schema_version: "[0-9.]+"$',
        'schema_version: "1.2"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^method_version: "[0-9.]+"$',
        f'method_version: "{V12_METHOD_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^created_with_plugin_version: "[0-9A-Za-z.-]+"$',
        f'created_with_plugin_version: "{V12_PLUGIN_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{BASELINE_ID}}": baseline_id,
        "{{DATE}}": today,
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", text)
    if remaining:
        raise MigrationError(
            f"Tokens 1.2 sin resolver en {template_relative}: {remaining}"
        )
    return text.encode("utf-8")


def _render_v13_template(
    root: Path, relative: str, project_id: str, baseline_id: str, today: str
) -> bytes:
    template_relative = relative.removeprefix("docs/lks-sdd/")
    template = (
        Path(__file__).resolve().parents[1]
        / "skills/lks-sdd-define"
        / "assets/templates"
        / template_relative
    )
    if not template.is_file():
        raise MigrationError(f"Falta la plantilla 1.3 empaquetada: {template_relative}")
    text = template.read_text(encoding="utf-8")
    text = re.sub(
        r'^schema_version: "[0-9.]+"$',
        'schema_version: "1.3"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^method_version: "[0-9.]+"$',
        f'method_version: "{V13_METHOD_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^created_with_plugin_version: "[0-9A-Za-z.-]+"$',
        f'created_with_plugin_version: "{V13_PLUGIN_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{BASELINE_ID}}": baseline_id,
        "{{DATE}}": today,
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", text)
    if remaining:
        raise MigrationError(
            f"Tokens 1.3 sin resolver en {template_relative}: {remaining}"
        )
    return text.encode("utf-8")


def _render_v14_template(
    root: Path, relative: str, project_id: str, baseline_id: str, today: str
) -> bytes:
    template_relative = relative.removeprefix("docs/lks-sdd/")
    template = (
        Path(__file__).resolve().parents[1]
        / "skills/lks-sdd-define"
        / "assets/templates"
        / template_relative
    )
    if not template.is_file():
        raise MigrationError(f"Falta la plantilla 1.4 empaquetada: {template_relative}")
    text = template.read_text(encoding="utf-8")
    text = re.sub(
        r'^schema_version: "[0-9.]+"$',
        'schema_version: "1.4"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^method_version: "[0-9.]+"$',
        f'method_version: "{V14_METHOD_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^created_with_plugin_version: "[0-9A-Za-z.-]+"$',
        f'created_with_plugin_version: "{V14_PLUGIN_VERSION}"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"\n## Reporting policy\n.*?(?=\n## Mapping\n)",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\n## Milestone operations\n.*\Z",
        "\n",
        text,
        flags=re.DOTALL,
    )
    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{BASELINE_ID}}": baseline_id,
        "{{DATE}}": today,
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", text)
    if remaining:
        raise MigrationError(
            f"Tokens 1.4 sin resolver en {template_relative}: {remaining}"
        )
    return text.encode("utf-8")


def _read_manifest(root: Path) -> tuple[Path, bytes, dict[str, Any]]:
    manifest_path = _safe_artifact(root, ".lks-sdd/project.json")
    try:
        before = manifest_path.read_bytes()
        manifest = json.loads(before.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise MigrationError("project.json debe ser un objeto.")
    return manifest_path, before, manifest


def _plan(root: Path, target_schema: str = LATEST_SCHEMA) -> MigrationPlan:
    manifest_path, manifest_before, manifest = _read_manifest(root)
    source_schema = manifest.get("schema_version")
    if source_schema == target_schema:
        return MigrationPlan("current", str(source_schema), target_schema, [])
    if (source_schema, target_schema) not in SUPPORTED_MIGRATIONS:
        supported = ", ".join(
            f"{source}->{target}" for source, target in sorted(SUPPORTED_MIGRATIONS)
        )
        raise MigrationError(
            f"Migracion {source_schema!r}->{target_schema!r} no soportada. Rutas disponibles: {supported}. Las migraciones se aplican de una en una."
        )
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise MigrationError("El indice anterior no declara artefactos migrables.")
    changes: list[PlannedChange] = []
    reviews: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in artifacts:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise MigrationError(
                "El indice anterior contiene una entrada de artefacto invalida."
            )
        relative = entry["path"]
        if relative in seen:
            raise MigrationError(f"Ruta duplicada en el indice anterior: {relative}")
        seen.add(relative)
        path = _safe_artifact(root, relative)
        before = path.read_bytes()
        if (source_schema, target_schema) == ("0.9", "1.0"):
            after, artifact_reviews, operations = _migrate_markdown_09_to_10(
                before, relative
            )
        elif (source_schema, target_schema) == ("1.0", "1.1"):
            after, artifact_reviews, operations = _migrate_markdown_10_to_11(
                before, relative
            )
        elif (source_schema, target_schema) == ("1.1", "1.2"):
            after, artifact_reviews, operations = _migrate_markdown_11_to_12(
                before, relative
            )
        elif (source_schema, target_schema) == ("1.2", "1.3"):
            after, artifact_reviews, operations = _migrate_markdown_12_to_13(
                before, relative
            )
        elif (source_schema, target_schema) == ("1.3", "1.4"):
            after, artifact_reviews, operations = _migrate_markdown_13_to_14(
                before, relative
            )
        else:
            after, artifact_reviews, operations = _migrate_markdown_14_to_15(
                before, relative
            )
        reviews.extend(artifact_reviews)
        if before != after:
            changes.append(PlannedChange(path, before, after, operations))
    if (source_schema, target_schema) == ("1.1", "1.2"):
        project_id = manifest.get("project_id")
        baseline_id = manifest.get("baseline_id")
        if not isinstance(project_id, str) or not isinstance(baseline_id, str):
            raise MigrationError(
                "project_id y baseline_id son necesarios para crear los artefactos 1.2."
            )
        today = datetime.now(UTC).date().isoformat()
        artifacts_by_id = {
            item.get("id"): item
            for item in artifacts
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        for artifact_id, relative in V12_ARTIFACTS:
            existing = artifacts_by_id.get(artifact_id)
            if existing is not None:
                if existing.get("path") != relative:
                    raise MigrationError(
                        f"{artifact_id} usa una ruta incompatible: {existing.get('path')!r}."
                    )
                existing["required"] = True
                continue
            destination = _safe_new_artifact(root, relative)
            rendered = _render_v12_template(
                root, relative, project_id, baseline_id, today
            )
            changes.append(
                PlannedChange(
                    destination,
                    b"",
                    rendered,
                    ["create-required-artifact-1.2"],
                    created=True,
                )
            )
            artifacts.append(
                {"id": artifact_id, "path": relative, "required": True}
            )
            artifacts_by_id[artifact_id] = artifacts[-1]
    if (source_schema, target_schema) == ("1.2", "1.3"):
        project_id = manifest.get("project_id")
        baseline_id = manifest.get("baseline_id")
        if not isinstance(project_id, str) or not isinstance(baseline_id, str):
            raise MigrationError(
                "project_id y baseline_id son necesarios para crear los artefactos 1.3."
            )
        today = datetime.now(UTC).date().isoformat()
        artifacts_by_id = {
            item.get("id"): item
            for item in artifacts
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        for artifact_id, relative in V13_ARTIFACTS:
            existing = artifacts_by_id.get(artifact_id)
            if existing is not None:
                if existing.get("path") != relative:
                    raise MigrationError(
                        f"{artifact_id} usa una ruta incompatible: {existing.get('path')!r}."
                    )
                existing["required"] = True
                continue
            destination = _safe_new_artifact(root, relative)
            rendered = _render_v13_template(
                root, relative, project_id, baseline_id, today
            )
            # A migration never guesses that REL-001 is the active planning target.
            rendered_text = rendered.decode("utf-8")
            rendered_text = re.sub(
                r"(?m)^\| REL-001 \| release \| proposed \|.*\|$\r?\n",
                "",
                rendered_text,
                count=1,
            )
            changes.append(
                PlannedChange(
                    destination,
                    b"",
                    rendered_text.encode("utf-8"),
                    ["create-planning-coverage-1.3-without-inference"],
                    created=True,
                )
            )
            artifacts.append(
                {"id": artifact_id, "path": relative, "required": True}
            )
            artifacts_by_id[artifact_id] = artifacts[-1]

        task_folder = root / "docs/lks-sdd/04-delivery/tasks"
        if task_folder.is_dir() and not _is_link_like(task_folder):
            for task_path in sorted(task_folder.glob("TASK-[0-9][0-9][0-9].md")):
                relative = _relative_path(root, task_path).as_posix()
                if relative in seen or _is_link_like(task_path):
                    continue
                before = task_path.read_bytes()
                after, task_reviews, operations = _migrate_markdown_12_to_13(
                    before, relative
                )
                reviews.extend(task_reviews)
                if before != after:
                    changes.append(
                        PlannedChange(task_path, before, after, operations)
                    )
    if (source_schema, target_schema) == ("1.3", "1.4"):
        nonterminal_executions = [
            item.get("execution_id", "EXEC-unknown")
            for item in manifest.get("executions", [])
            if isinstance(item, dict)
            and item.get("status")
            in {"in-progress", "in-review", "paused", "blocked"}
        ]
        if nonterminal_executions:
            raise MigrationError(
                "La migración 1.3 -> 1.4 no altera una ejecución reanudable activa. "
                "Cierre o cancele primero: "
                + ", ".join(sorted(str(item) for item in nonterminal_executions))
                + "."
            )
        project_id = manifest.get("project_id")
        baseline_id = manifest.get("baseline_id")
        if not isinstance(project_id, str) or not isinstance(baseline_id, str):
            raise MigrationError(
                "project_id y baseline_id son necesarios para crear los artefactos 1.4."
            )
        today = datetime.now(UTC).date().isoformat()
        artifacts_by_id = {
            item.get("id"): item
            for item in artifacts
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        for artifact_id, relative in V14_ARTIFACTS:
            existing = artifacts_by_id.get(artifact_id)
            if existing is not None:
                if existing.get("path") != relative:
                    raise MigrationError(
                        f"{artifact_id} usa una ruta incompatible: {existing.get('path')!r}."
                    )
                existing["required"] = True
                continue
            destination = _safe_new_artifact(root, relative)
            rendered = _render_v14_template(
                root, relative, project_id, baseline_id, today
            ).decode("utf-8")
            pending_row = (
                f"| TRK-001 | proposed | pending | pending | pending | pending | "
                f"pending | pending | pending | pending: tracking mode not selected | {today} |"
            )
            repository_row = (
                f"| TRK-001 | proposed | repository-only | none | not-applicable | "
                f"not-applicable | not-applicable | not-required | local-only | "
                f"pending: migration-preserved from schema 1.3 | {today} |"
            )
            if pending_row not in rendered:
                raise MigrationError(
                    "La plantilla ART-TRACKING no contiene el binding pending esperado."
                )
            rendered = rendered.replace(pending_row, repository_row, 1)
            changes.append(
                PlannedChange(
                    destination,
                    b"",
                    rendered.encode("utf-8"),
                    ["create-task-tracking-1.4-repository-only"],
                    created=True,
                )
            )
            artifacts.append(
                {"id": artifact_id, "path": relative, "required": True}
            )
            artifacts_by_id[artifact_id] = artifacts[-1]

        # TASK details participate in the live 1.4 contract. Historical CKPT
        # files remain byte-identical 1.3 evidence; new checkpoints use 1.4.
        dynamic_folders = (
            ("docs/lks-sdd/04-delivery/tasks", "TASK-[0-9][0-9][0-9].md"),
        )
        for folder_relative, pattern in dynamic_folders:
            folder = root / folder_relative
            if not folder.is_dir() or _is_link_like(folder):
                continue
            for dynamic_path in sorted(folder.glob(pattern)):
                relative = _relative_path(root, dynamic_path).as_posix()
                if relative in seen or _is_link_like(dynamic_path):
                    continue
                before = dynamic_path.read_bytes()
                after, dynamic_reviews, operations = _migrate_markdown_13_to_14(
                    before, relative
                )
                reviews.extend(dynamic_reviews)
                if before != after:
                    changes.append(
                        PlannedChange(dynamic_path, before, after, operations)
                    )
    if (source_schema, target_schema) == ("1.4", "1.5"):
        nonterminal_executions = [
            item.get("execution_id", "EXEC-unknown")
            for item in manifest.get("executions", [])
            if isinstance(item, dict)
            and item.get("status")
            in {"in-progress", "in-review", "paused", "blocked"}
        ]
        if nonterminal_executions:
            raise MigrationError(
                "La migración 1.4 -> 1.5 no altera una ejecución reanudable activa. "
                "Cierre o cancele primero: "
                + ", ".join(sorted(str(item) for item in nonterminal_executions))
                + "."
            )
        tracking_entry = next(
            (
                item
                for item in artifacts
                if isinstance(item, dict) and item.get("id") == "ART-TRACKING"
            ),
            None,
        )
        if not isinstance(tracking_entry, dict):
            raise MigrationError("schema 1.4 exige ART-TRACKING antes de migrar.")
        tracking_path = _safe_artifact(root, str(tracking_entry["path"]))
        operation_headers = (
            "ID", "State", "Task", "Action", "Preview hash",
            "Projection fingerprint", "Duplicate check", "Authorized by role",
            "Authorized on", "External ID", "External key", "Recorded on",
            "Result", "Notes",
        )
        unresolved = [
            row.get("ID", "SYNC-unknown")
            for headers, rows in parse_tables(tracking_path.read_text(encoding="utf-8"))
            if headers == operation_headers
            for row in rows
            if row.get("State") in {
                "authorized",
                "conflict",
                "reconciliation-required",
            }
        ]
        if unresolved:
            raise MigrationError(
                "La migración 1.4 -> 1.5 exige cerrar o reconciliar primero: "
                + ", ".join(sorted(str(item) for item in unresolved))
                + "."
            )
        task_folder = root / "docs/lks-sdd/04-delivery/tasks"
        if task_folder.is_dir() and not _is_link_like(task_folder):
            for task_path in sorted(task_folder.glob("TASK-[0-9][0-9][0-9].md")):
                relative = _relative_path(root, task_path).as_posix()
                if relative in seen or _is_link_like(task_path):
                    continue
                before = task_path.read_bytes()
                after, task_reviews, operations = _migrate_markdown_14_to_15(
                    before, relative
                )
                reviews.extend(task_reviews)
                if before != after:
                    changes.append(
                        PlannedChange(task_path, before, after, operations)
                    )
    manifest["schema_version"] = target_schema
    manifest_operations = ["operational-index-version"]
    if target_schema == "1.1":
        manifest["method_version"] = V11_METHOD_VERSION
        manifest["plugin_version"] = V11_PLUGIN_VERSION
        for stale_key in ("open_blockers", "readiness"):
            if stale_key in manifest:
                manifest.pop(stale_key)
                manifest_operations.append(
                    f"remove-derived-{stale_key.replace('_', '-')}"
                )
    if target_schema == "1.2":
        manifest["method_version"] = V12_METHOD_VERSION
        manifest["plugin_version"] = V12_PLUGIN_VERSION
        technology = manifest.setdefault("technology", {})
        if not isinstance(technology, dict):
            raise MigrationError("technology debe ser un objeto antes de migrar a 1.2.")
        technology.setdefault("profile_bindings", [])
        manifest.setdefault("active_plan", "PLAN-001")
        manifest.setdefault("active_task", None)
        manifest["delivery_governance"] = {
            "state": "proposed",
            "model": None,
            "decision": None,
            "source": "docs/lks-sdd/04-delivery/delivery-governance.md",
            "active_change": "CHG-001",
            "review_due": None,
        }
        version_control = manifest.get("version_control")
        if not isinstance(version_control, dict):
            version_control = {"type": "none", "origin": "none"}
        manifest["version_control"] = {
            "type": version_control.get("type", "none"),
            "origin": version_control.get("origin", "none"),
            "branching_model": None,
            "main_branch": None,
            "integration_branch": None,
            "decision": None,
        }
        for stale_key in ("readiness", "implementation", "verification"):
            if stale_key in manifest:
                manifest.pop(stale_key)
                manifest_operations.append(
                    f"remove-derived-{stale_key.replace('_', '-')}"
                )
        manifest_operations.extend(
            [
                "delivery-governance-proposed",
                "task-horizon-initialized",
                "profile-bindings-initialized",
                "version-control-decision-pending",
            ]
        )
    if target_schema == "1.3":
        manifest["method_version"] = V13_METHOD_VERSION
        manifest["plugin_version"] = V13_PLUGIN_VERSION
        task_states: dict[str, str] = {}
        task_entry = next(
            (
                item for item in artifacts
                if isinstance(item, dict) and item.get("id") == "ART-TASKS"
            ),
            None,
        )
        if isinstance(task_entry, dict):
            task_path = _safe_artifact(root, str(task_entry["path"]))
            for headers, rows in parse_tables(
                task_path.read_text(encoding="utf-8")
            ):
                if headers == TASK_HEADERS:
                    task_states.update(
                        {
                            row.get("ID", ""): row.get("Workflow state", "")
                            for row in rows if row.get("ID")
                        }
                    )
        active_tasks = sorted(
            task_id for task_id, state in task_states.items()
            if state in {"in-progress", "in-review", "blocked"}
        )
        manifest["active_tasks"] = active_tasks
        manifest["active_task"] = active_tasks[0] if len(active_tasks) == 1 else None
        manifest["planning"] = {
            "source": "docs/lks-sdd/04-delivery/planning-coverage.md",
            "target_type": None,
            "target_id": None,
            "policy": "complete-before-implementation",
            "policy_decision": None,
            "specification_fingerprint": None,
            "planning_fingerprint": None,
            "confirmed_by_role": None,
            "confirmed_on": None,
            "last_change": None,
        }
        manifest["authorizations"] = []
        manifest["executions"] = []
        manifest_operations.extend(
            [
                "planning-coverage-created-partial",
                "task-definitions-marked-incomplete",
                "authorizations-not-inferred",
                "executions-and-checkpoints-not-inferred",
            ]
        )
    if target_schema == "1.4":
        manifest["method_version"] = V14_METHOD_VERSION
        manifest["plugin_version"] = V14_PLUGIN_VERSION
        manifest["task_tracking"] = {
            "source": "docs/lks-sdd/04-delivery/task-tracking.md",
            "binding_id": "TRK-001",
            "state": "proposed",
            "mode": "repository-only",
            "provider": None,
            "decision": None,
            "site": None,
            "project_key": None,
            "issue_type": None,
            "sync_policy": "not-required",
            "write_policy": "local-only",
            "projection_fingerprint": None,
            "sync_status": "not-required",
            "last_sync_on": None,
        }
        manifest_operations.extend(
            [
                "task-tracking-created-repository-only",
                "external-provider-not-inferred",
                "authorizations-and-executions-preserved",
            ]
        )
    if target_schema == "1.5":
        manifest["method_version"] = METHOD_VERSION
        manifest["plugin_version"] = PLUGIN_VERSION
        tracking = manifest.get("task_tracking")
        if not isinstance(tracking, dict):
            raise MigrationError("project.json 1.4 no contiene task_tracking.")
        mode = tracking.get("mode")
        if mode == "pending":
            tracking.update(
                reporting_scope="pending",
                coordination_gate="pending",
                reporting_status="decision-required",
                last_reported_on=None,
            )
        elif mode == "repository-only":
            tracking.update(
                reporting_scope="not-applicable",
                coordination_gate="not-required",
                reporting_status="not-required",
                last_reported_on=None,
            )
        elif mode == "jira-hybrid":
            tracking.update(
                reporting_scope="projection-only",
                coordination_gate=tracking.get(
                    "sync_policy", "required-before-execution"
                ),
                reporting_status="not-required",
                last_reported_on=None,
            )
        else:
            raise MigrationError(f"Modo de tracking 1.4 inválido: {mode!r}.")
        manifest_operations.extend(
            [
                "jira-reporting-defaulted-without-external-write",
                "workflow-mapping-not-inferred",
                "historical-tracking-receipts-preserved",
            ]
        )
    manifest_after = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    if manifest_before != manifest_after:
        changes.append(
            PlannedChange(
                manifest_path, manifest_before, manifest_after, manifest_operations
            )
        )
    return MigrationPlan(
        "migration-required", str(source_schema), target_schema, changes, reviews
    )


def _preview_hash(root: Path, changes: list[PlannedChange]) -> str:
    digest = hashlib.sha256()
    for change in sorted(changes, key=lambda item: str(item.path)):
        digest.update(_relative_path(root, change.path).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(_hash(change.before)))
        digest.update(bytes.fromhex(_hash(change.after)))
    return digest.hexdigest()


def _preview(root: Path, plan: MigrationPlan) -> dict[str, Any]:
    return {
        "status": plan.status,
        "source_schema": plan.source_schema,
        "target_schema": plan.target_schema,
        "changed": False,
        "preview_hash": _preview_hash(root, plan.changes) if plan.changes else None,
        "human_review_required": plan.human_review_required,
        "changes": [
            {
                "path": _relative_path(root, change.path).as_posix(),
                "before_sha256": _hash(change.before),
                "after_sha256": _hash(change.after),
                "operations": change.operations,
                "body_preserved": change.path.suffix == ".md"
                and change.before.split(b"---", 2)[-1]
                == change.after.split(b"---", 2)[-1],
            }
            for change in plan.changes
        ],
    }


def _backup_target(root: Path, requested: Path) -> Path:
    unresolved = requested.expanduser()
    if not unresolved.is_absolute():
        unresolved = Path.cwd() / unresolved
    current = unresolved
    while current.parent != current:
        if _is_link_like(current):
            raise MigrationError(
                "El backup no puede crearse mediante symlinks o junctions."
            )
        current = current.parent
    backup = unresolved.resolve()
    try:
        _relative_path(root, backup)
    except ValueError:
        pass
    else:
        raise MigrationError("El backup de migracion debe estar fuera del proyecto.")
    if not backup.parent.is_dir() or backup.exists():
        raise MigrationError(
            "La carpeta padre del backup debe existir y el destino no debe existir."
        )
    return backup


def _safe_backup_source(backup: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise MigrationError(f"Ruta fuera del backup: {relative}")
    source_root = backup / "files"
    if not source_root.is_dir() or _is_link_like(source_root):
        raise MigrationError("La carpeta de archivos del backup es invalida.")
    current = source_root
    for part in requested.parts:
        current = current / part
        if _is_link_like(current):
            raise MigrationError(f"El backup usa un enlace simbolico: {relative}")
    source = (source_root / requested).resolve()
    try:
        source.relative_to(source_root.resolve())
    except ValueError as exc:
        raise MigrationError(f"Ruta fuera del backup: {relative}") from exc
    if not source.is_file():
        raise MigrationError(f"Archivo de backup invalido: {relative}")
    return source


def _apply(
    root: Path,
    plan: MigrationPlan,
    backup: Path,
    preview_hash: str,
) -> dict[str, Any]:
    if plan.human_review_required:
        raise MigrationError(
            "La migracion no puede aplicarse mientras human_review_required "
            "no este vacio. Resuelva las ambiguedades en los Markdown 1.0, "
            "valide el origen y repita el dry-run; no se ha creado el backup "
            "ni escrito ningun archivo."
        )
    records: list[dict[str, str]] = []
    try:
        backup.mkdir()
        for change in plan.changes:
            relative = _relative_path(root, change.path)
            backup_file = backup / "files" / relative
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file.write_bytes(change.before)
            records.append(
                {
                    "path": relative.as_posix(),
                    "before_sha256": _hash(change.before),
                    "after_sha256": _hash(change.after),
                    "created": change.created,
                }
            )
    except OSError as exc:
        shutil.rmtree(backup, ignore_errors=True)
        raise MigrationError(f"No se pudo crear el backup externo: {exc}") from exc
    record: dict[str, Any] = {
        "kind": "lks-sdd-schema-migration-backup",
        "source_schema": plan.source_schema,
        "target_schema": plan.target_schema,
        "project_root": str(root),
        "preview_hash": preview_hash,
        "human_review_required": plan.human_review_required,
        "files": records,
        "status": "prepared",
    }
    record_path = backup / RECORD_NAME
    try:
        record_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        shutil.rmtree(backup, ignore_errors=True)
        raise MigrationError(f"No se pudo registrar el backup externo: {exc}") from exc
    written: list[tuple[Path, bytes | None]] = []
    temporary_paths: list[Path] = []
    try:
        for change in plan.changes:
            if change.created:
                if change.path.exists():
                    raise MigrationError(
                        "Apareció un archivo después del preview: "
                        f"{_relative_path(root, change.path)}"
                    )
                change.path.parent.mkdir(parents=True, exist_ok=True)
            elif change.path.read_bytes() != change.before:
                raise MigrationError(
                    f"Cambio el archivo despues del preview: {_relative_path(root, change.path)}"
                )
            temporary = change.path.with_name(
                change.path.name + ".lks-sdd-migration.tmp"
            )
            with temporary.open("xb") as stream:
                temporary_paths.append(temporary)
                stream.write(change.after)
            os.replace(temporary, change.path)
            temporary_paths.remove(temporary)
            written.append((change.path, None if change.created else change.before))
        validation, _, _ = validate_project(root)
        if not validation.valid:
            raise MigrationError(
                "La version migrada no valida: " + "; ".join(validation.errors)
            )
        record["status"] = "applied"
        record_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, MigrationError) as exc:
        for temporary in temporary_paths:
            try:
                temporary.unlink()
            except OSError:
                pass
        for path, before in reversed(written):
            if before is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                path.write_bytes(before)
        record["status"] = "apply-failed-rolled-back"
        try:
            record_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except OSError:
            pass
        raise MigrationError(
            f"La migracion se revirtio automaticamente: {exc}"
        ) from exc
    return {
        "status": "migrated",
        "changed": True,
        "backup": str(backup),
        "validated": True,
    }


def _load_backup(root: Path, backup: Path) -> tuple[Path, dict[str, Any]]:
    record_path = backup / RECORD_NAME
    if _is_link_like(record_path):
        raise MigrationError("El registro de backup no puede ser un enlace simbolico.")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationError(f"Backup de migracion invalido: {exc}") from exc
    if (
        not isinstance(record, dict)
        or record.get("kind") != "lks-sdd-schema-migration-backup"
        or not isinstance(record.get("project_root"), str)
        or Path(record.get("project_root", "")).resolve() != root
    ):
        raise MigrationError("El backup no pertenece a este proyecto.")
    files = record.get("files", [])
    if not isinstance(files, list) or not files:
        raise MigrationError("El registro de backup no contiene archivos.")
    seen: set[str] = set()
    for item in files:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("before_sha256"), str)
            or not isinstance(item.get("after_sha256"), str)
            or not isinstance(item.get("created", False), bool)
            or re.fullmatch(r"[a-f0-9]{64}", item.get("before_sha256", "")) is None
            or re.fullmatch(r"[a-f0-9]{64}", item.get("after_sha256", "")) is None
        ):
            raise MigrationError("El registro de backup contiene una entrada invalida.")
        if item["path"] in seen:
            raise MigrationError(
                f"Ruta duplicada en el registro de backup: {item['path']}"
            )
        seen.add(item["path"])
    return record_path, record


def _plan_rollback(
    root: Path, backup: Path
) -> tuple[MigrationPlan, Path, dict[str, Any]]:
    record_path, record = _load_backup(root, backup)
    changes: list[PlannedChange] = []
    for item in record["files"]:
        if item.get("created") and not (root / Path(item["path"])).exists():
            _safe_new_artifact(root, item["path"])
            continue
        path = _safe_artifact(root, item["path"])
        current = path.read_bytes()
        current_hash = _hash(current)
        if current_hash == item["after_sha256"]:
            if item.get("created"):
                before = b""
                delete = True
            else:
                source = _safe_backup_source(backup, item["path"])
                before = source.read_bytes()
                if _hash(before) != item["before_sha256"]:
                    raise MigrationError(f"Backup corrupto: {item['path']}")
                delete = False
            changes.append(
                PlannedChange(
                    path,
                    current,
                    before,
                    ["remove-created-artifact" if delete else "restore-from-backup"],
                    delete=delete,
                )
            )
        elif current_hash != item["before_sha256"]:
            raise MigrationError(
                f"No se revierte {item['path']}: cambio despues de la migracion."
            )
    status = "rollback-required" if changes else "already-rolled-back"
    plan = MigrationPlan(
        status,
        str(record.get("target_schema")),
        str(record.get("source_schema")),
        changes,
        list(record.get("human_review_required", [])),
    )
    return plan, record_path, record


def _apply_rollback(
    root: Path, plan: MigrationPlan, record_path: Path, record: dict[str, Any]
) -> dict[str, Any]:
    if not plan.changes:
        return {"status": "already-rolled-back", "changed": False}
    restored: list[tuple[Path, bytes]] = []
    temporary_paths: list[Path] = []
    try:
        for change in plan.changes:
            if change.path.read_bytes() != change.before:
                raise MigrationError(
                    f"Cambio el archivo durante el rollback: {_relative_path(root, change.path)}"
                )
            if change.delete:
                change.path.unlink()
                restored.append((change.path, change.before))
                continue
            temporary = change.path.with_name(
                change.path.name + ".lks-sdd-rollback.tmp"
            )
            with temporary.open("xb") as stream:
                temporary_paths.append(temporary)
                stream.write(change.after)
            os.replace(temporary, change.path)
            temporary_paths.remove(temporary)
            restored.append((change.path, change.before))
        record["status"] = "rolled-back"
        record_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, MigrationError) as exc:
        for temporary in temporary_paths:
            try:
                temporary.unlink()
            except OSError:
                pass
        for path, current in reversed(restored):
            path.write_bytes(current)
        record["status"] = "applied"
        try:
            record_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except OSError:
            pass
        raise MigrationError(f"El rollback se revirtio: {exc}") from exc
    return {
        "status": "rolled-back",
        "changed": True,
        "restored_schema": plan.target_schema,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", type=Path)
    parser.add_argument(
        "--target-schema",
        choices=("1.0", "1.1", "1.2", "1.3", "1.4", "1.5"),
        default=LATEST_SCHEMA,
    )
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        root = _safe_root(args.project_root)
        if args.rollback:
            backup = args.rollback.expanduser().resolve()
            plan, record_path, record = _plan_rollback(root, backup)
            result = _preview(root, plan)
            if args.apply:
                if not args.authorize:
                    raise MigrationError("Rollback requiere --authorize.")
                if plan.changes and args.preview_hash != result["preview_hash"]:
                    raise MigrationError(
                        "El preview hash de rollback no coincide; repita --rollback ... --dry-run."
                    )
                result.update(_apply_rollback(root, plan, record_path, record))
        else:
            plan = _plan(root, args.target_schema)
            result = _preview(root, plan)
            if args.apply:
                if not plan.changes:
                    result = {
                        "status": "current",
                        "changed": False,
                        "target_schema": args.target_schema,
                        "human_review_required": [],
                    }
                else:
                    if not args.authorize or not args.backup_dir:
                        raise MigrationError(
                            "Aplicar requiere --authorize y --backup-dir externo."
                        )
                    if args.preview_hash != result["preview_hash"]:
                        raise MigrationError(
                            "El preview hash no coincide; repita el dry-run."
                        )
                    result.update(
                        _apply(
                            root,
                            plan,
                            _backup_target(root, args.backup_dir),
                            result["preview_hash"],
                        )
                    )
        code = 0
    except MigrationError as exc:
        code, result = 2, {"status": "error", "changed": False, "error": str(exc)}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        if result.get("preview_hash"):
            print(f"preview_hash={result['preview_hash']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
