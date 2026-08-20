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
from pathlib import Path
from typing import Any

from validate_project import validate_project

LATEST_SCHEMA = "1.1"
PLUGIN_VERSION = "0.7.0"
METHOD_VERSION = "1.1.0"
RECORD_NAME = "migration-record.json"
SUPPORTED_MIGRATIONS = {("0.9", "1.0"), ("1.0", "1.1")}

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
        lines, start, end, "method_version", METHOD_VERSION, relative
    )
    _set_frontmatter_value(
        lines, start, end, "created_with_plugin_version", PLUGIN_VERSION, relative
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
        else:
            after, artifact_reviews, operations = _migrate_markdown_10_to_11(
                before, relative
            )
        reviews.extend(artifact_reviews)
        if before != after:
            changes.append(PlannedChange(path, before, after, operations))
    manifest["schema_version"] = target_schema
    manifest_operations = ["operational-index-version"]
    if target_schema == "1.1":
        manifest["method_version"] = METHOD_VERSION
        manifest["plugin_version"] = PLUGIN_VERSION
        for stale_key in ("open_blockers", "readiness"):
            if stale_key in manifest:
                manifest.pop(stale_key)
                manifest_operations.append(
                    f"remove-derived-{stale_key.replace('_', '-')}"
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
    written: list[tuple[Path, bytes]] = []
    temporary_paths: list[Path] = []
    try:
        for change in plan.changes:
            if change.path.read_bytes() != change.before:
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
            written.append((change.path, change.before))
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
        path = _safe_artifact(root, item["path"])
        current = path.read_bytes()
        current_hash = _hash(current)
        if current_hash == item["after_sha256"]:
            source = _safe_backup_source(backup, item["path"])
            before = source.read_bytes()
            if _hash(before) != item["before_sha256"]:
                raise MigrationError(f"Backup corrupto: {item['path']}")
            changes.append(
                PlannedChange(path, current, before, ["restore-from-backup"])
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
        "--target-schema", choices=("1.0", "1.1"), default=LATEST_SCHEMA
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
