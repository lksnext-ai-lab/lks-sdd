#!/usr/bin/env python3
"""Preview, apply, or roll back the supported LKS-SDD schema 0.9 to 1.0 migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from validate_project import validate_project

TARGET_SCHEMA = "1.0"
SOURCE_SCHEMA = "0.9"
PLUGIN_VERSION = "0.4.0"
RECORD_NAME = "migration-record.json"


class MigrationError(Exception):
    """Expected, actionable migration failure."""


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise MigrationError(f"La raíz no existe o no es una carpeta: {root}")
    return root


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _safe_artifact(root: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise MigrationError(f"Ruta de artefacto no permitida: {relative}")
    unresolved = root / requested
    current = root
    for part in requested.parts:
        current = current / part
        if _is_link_like(current):
            raise MigrationError(f"El artefacto usa un enlace simbólico: {relative}")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise MigrationError(f"Ruta de artefacto fuera de la raíz: {relative}") from exc
    if not candidate.is_file():
        raise MigrationError(f"El artefacto no es un archivo regular: {relative}")
    return candidate


def _migrate_markdown(content: bytes, relative: str) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError(f"Markdown no UTF-8: {relative}") from exc
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise MigrationError(f"Front matter ausente: {relative}")
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise MigrationError(f"Front matter sin cierre: {relative}") from exc
    pattern = re.compile(r"^(schema_version:\s*)['\"]?0\.9['\"]?(\s*(?:\r?\n)?)$")
    changed = 0
    for index in range(1, end):
        match = pattern.match(lines[index])
        if match:
            newline = (
                "\r\n"
                if lines[index].endswith("\r\n")
                else "\n"
                if lines[index].endswith("\n")
                else ""
            )
            lines[index] = f'{match.group(1)}"{TARGET_SCHEMA}"{newline}'
            changed += 1
    if changed != 1:
        raise MigrationError(
            f"{relative}: se esperaba exactamente un schema_version 0.9 en front matter."
        )
    return "".join(lines).encode("utf-8")


def _plan(root: Path) -> tuple[str, list[tuple[Path, bytes, bytes]], dict[str, Any]]:
    manifest_path = _safe_artifact(root, ".lks-sdd/project.json")
    try:
        manifest_before = manifest_path.read_bytes()
        manifest = json.loads(manifest_before.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise MigrationError("project.json debe ser un objeto.")
    version = manifest.get("schema_version")
    if version == TARGET_SCHEMA:
        return "current", [], manifest
    if version != SOURCE_SCHEMA:
        raise MigrationError(
            f"Schema {version!r} no soportado. Esta versión solo migra {SOURCE_SCHEMA} -> {TARGET_SCHEMA}; "
            "use diagnóstico de solo lectura o una migración específica."
        )
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise MigrationError("El índice anterior no declara artefactos migrables.")
    changes: list[tuple[Path, bytes, bytes]] = []
    seen: set[str] = set()
    for entry in artifacts:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise MigrationError(
                "El índice anterior contiene una entrada de artefacto inválida."
            )
        relative = entry["path"]
        if relative in seen:
            raise MigrationError(f"Ruta duplicada en el índice anterior: {relative}")
        seen.add(relative)
        path = _safe_artifact(root, relative)
        before = path.read_bytes()
        after = _migrate_markdown(before, relative)
        changes.append((path, before, after))
    manifest["schema_version"] = TARGET_SCHEMA
    manifest["plugin_version"] = PLUGIN_VERSION
    manifest_after = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    changes.append((manifest_path, manifest_before, manifest_after))
    return "migration-required", changes, manifest


def _preview_hash(root: Path, changes: list[tuple[Path, bytes, bytes]]) -> str:
    digest = hashlib.sha256()
    for path, before, after in sorted(changes, key=lambda item: str(item[0])):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(_hash(before)))
        digest.update(bytes.fromhex(_hash(after)))
    return digest.hexdigest()


def _preview(
    root: Path, status: str, changes: list[tuple[Path, bytes, bytes]]
) -> dict[str, Any]:
    return {
        "status": status,
        "source_schema": SOURCE_SCHEMA if changes else TARGET_SCHEMA,
        "target_schema": TARGET_SCHEMA,
        "changed": False,
        "preview_hash": _preview_hash(root, changes) if changes else None,
        "changes": [
            {
                "path": path.relative_to(root).as_posix(),
                "before_sha256": _hash(before),
                "after_sha256": _hash(after),
                "operation": "frontmatter-schema-version"
                if path.suffix == ".md"
                else "operational-index-version",
                "body_preserved": path.suffix == ".md"
                and before.split(b"---", 2)[-1] == after.split(b"---", 2)[-1],
            }
            for path, before, after in changes
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
        backup.relative_to(root)
    except ValueError:
        pass
    else:
        raise MigrationError("El backup de migración debe estar fuera del proyecto.")
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
        raise MigrationError("La carpeta de archivos del backup es inválida.")
    current = source_root
    for part in requested.parts:
        current = current / part
        if _is_link_like(current):
            raise MigrationError(f"El backup usa un enlace simbólico: {relative}")
    source = (source_root / requested).resolve()
    try:
        source.relative_to(source_root.resolve())
    except ValueError as exc:
        raise MigrationError(f"Ruta fuera del backup: {relative}") from exc
    if not source.is_file():
        raise MigrationError(f"Archivo de backup inválido: {relative}")
    return source


def _apply(
    root: Path, changes: list[tuple[Path, bytes, bytes]], backup: Path
) -> dict[str, Any]:
    records: list[dict[str, str]] = []
    try:
        backup.mkdir()
        for path, before, after in changes:
            relative = path.relative_to(root)
            backup_file = backup / "files" / relative
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file.write_bytes(before)
            records.append(
                {
                    "path": relative.as_posix(),
                    "before_sha256": _hash(before),
                    "after_sha256": _hash(after),
                }
            )
    except OSError as exc:
        shutil.rmtree(backup, ignore_errors=True)
        raise MigrationError(f"No se pudo crear el backup externo: {exc}") from exc
    record = {
        "kind": "lks-sdd-schema-migration-backup",
        "source_schema": SOURCE_SCHEMA,
        "target_schema": TARGET_SCHEMA,
        "project_root": str(root),
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
        for path, before, after in changes:
            if path.read_bytes() != before:
                raise MigrationError(
                    f"Cambió el archivo después del preview: {path.relative_to(root)}"
                )
            temporary = path.with_name(path.name + ".lks-sdd-migration.tmp")
            with temporary.open("xb") as stream:
                temporary_paths.append(temporary)
                stream.write(after)
            os.replace(temporary, path)
            temporary_paths.remove(temporary)
            written.append((path, before))
        validation, _, _ = validate_project(root)
        if not validation.valid:
            raise MigrationError(
                "La versión migrada no valida: " + "; ".join(validation.errors)
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
            f"La migración se revirtió automáticamente: {exc}"
        ) from exc
    return {
        "status": "migrated",
        "changed": True,
        "backup": str(backup),
        "validated": True,
    }


def _rollback(root: Path, backup: Path) -> dict[str, Any]:
    record_path = backup / RECORD_NAME
    if _is_link_like(record_path):
        raise MigrationError("El registro de backup no puede ser un enlace simbólico.")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationError(f"Backup de migración inválido: {exc}") from exc
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
            raise MigrationError("El registro de backup contiene una entrada inválida.")
        if item["path"] in seen:
            raise MigrationError(
                f"Ruta duplicada en el registro de backup: {item['path']}"
            )
        seen.add(item["path"])
    restorations: list[tuple[Path, bytes, bytes]] = []
    for item in files:
        path = _safe_artifact(root, item["path"])
        current_bytes = path.read_bytes()
        current_hash = _hash(current_bytes)
        if current_hash == item["after_sha256"]:
            source = _safe_backup_source(backup, item["path"])
            before_bytes = source.read_bytes()
            if _hash(before_bytes) != item["before_sha256"]:
                raise MigrationError(f"Backup corrupto: {item['path']}")
            restorations.append((path, before_bytes, current_bytes))
        elif current_hash != item["before_sha256"]:
            raise MigrationError(
                f"No se revierte {item['path']}: cambió después de la migración."
            )
    if not restorations:
        return {"status": "already-rolled-back", "changed": False}
    restored: list[tuple[Path, bytes]] = []
    temporary_paths: list[Path] = []
    try:
        for path, before_bytes, current_bytes in restorations:
            if path.read_bytes() != current_bytes:
                raise MigrationError(
                    f"Cambió el archivo durante el rollback: {path.relative_to(root)}"
                )
            temporary = path.with_name(path.name + ".lks-sdd-rollback.tmp")
            with temporary.open("xb") as stream:
                temporary_paths.append(temporary)
                stream.write(before_bytes)
            os.replace(temporary, path)
            temporary_paths.remove(temporary)
            restored.append((path, current_bytes))
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
        for path, current_bytes in reversed(restored):
            path.write_bytes(current_bytes)
        record["status"] = "applied"
        try:
            record_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except OSError:
            pass
        raise MigrationError(f"El rollback se revirtió: {exc}") from exc
    return {"status": "rolled-back", "changed": True, "restored_schema": SOURCE_SCHEMA}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", type=Path)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        root = _safe_root(args.project_root)
        if args.rollback:
            if not args.authorize:
                raise MigrationError("Rollback requiere --authorize.")
            result = _rollback(root, args.rollback.expanduser().resolve())
        else:
            status, changes, _ = _plan(root)
            result = _preview(root, status, changes)
            if args.apply:
                if not changes:
                    result = {
                        "status": "current",
                        "changed": False,
                        "target_schema": TARGET_SCHEMA,
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
                        _apply(root, changes, _backup_target(root, args.backup_dir))
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
