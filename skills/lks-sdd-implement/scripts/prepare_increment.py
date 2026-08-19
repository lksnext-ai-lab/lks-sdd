#!/usr/bin/env python3
"""Validate an increment gate and safely materialize the selected H0 scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "skills" / "lks-sdd-assess-readiness" / "scripts"))

from assess_readiness import assess  # noqa: E402
from validate_reference_profile import PROFILE_ID, PROFILE_ROOT, validate_profile  # noqa: E402


class PreparationError(Exception):
    """Expected, actionable preparation failure."""


def _safe_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise PreparationError(f"La raíz no es una carpeta: {root}")
    return root


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / ".lks-sdd" / "project.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparationError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict):
        raise PreparationError("project.json debe ser un objeto.")
    return value


def _assert_safe_destination(root: Path, destination: Path) -> None:
    try:
        destination.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise PreparationError(f"Destino fuera de la raíz autorizada: {destination}") from exc
    parent = destination.parent
    while parent != root:
        if parent.exists() and parent.is_symlink():
            raise PreparationError(f"No se escribe a través de enlaces simbólicos: {parent}")
        parent = parent.parent


def _planned_files(root: Path) -> tuple[list[tuple[Path, bytes]], list[str], list[str]]:
    scaffold = PROFILE_ROOT / "scaffold"
    planned: list[tuple[Path, bytes]] = []
    preserved: list[str] = []
    manual_integrations: list[str] = []
    ignored_parts = {".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    sources = [
        (path, path.relative_to(scaffold))
        for path in sorted(scaffold.rglob("*"))
        if path.is_file()
        and not ignored_parts.intersection(path.relative_to(scaffold).parts)
        and path.suffix not in {".pyc", ".tsbuildinfo"}
    ]
    sources.extend(
        [
            (PROFILE_ROOT / "technology-profile.yaml", Path(".lks-sdd/profile.yaml")),
            (PROFILE_ROOT / "technology-profile.lock.json", Path(".lks-sdd/profile.lock.json")),
        ]
    )
    for source, relative in sources:
        destination = root / relative
        _assert_safe_destination(root, destination)
        content = source.read_bytes()
        if destination.exists():
            if not destination.is_file():
                raise PreparationError(f"Colisión con una ruta que no es archivo: {relative.as_posix()}")
            if destination.read_bytes() == content:
                preserved.append(relative.as_posix())
                continue
            if relative.as_posix() == ".gitignore":
                manual_integrations.append(relative.as_posix())
                continue
            raise PreparationError(f"Colisión; no se sobrescribirá {relative.as_posix()}")
        planned.append((destination, content))
    return planned, preserved, manual_integrations


def _preview_hash(root: Path, planned: list[tuple[Path, bytes]]) -> str:
    digest = hashlib.sha256()
    for destination, content in planned:
        digest.update(destination.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def prepare(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = _safe_root(args.project_root)
    manifest = _load_manifest(root)
    readiness_code, readiness = assess(root, args.increment)
    blockers = list(readiness.get("blockers", []))
    technology = manifest.get("technology", {})
    if technology.get("selected_profile") != PROFILE_ID:
        blockers.append(f"El perfil seleccionado no es el H0 implementable: {technology.get('selected_profile')!r}.")
    if not technology.get("selection_decision"):
        blockers.append("Falta la ADR confirmada de selección del perfil.")
    blockers.extend(validate_profile(require_validated=True))
    if manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption", {})
        if adoption.get("status") != "materialized" or adoption.get("baseline_freshness") != "current":
            blockers.append("La baseline adoptada debe estar materializada y vigente.")
    if readiness_code != 0 or blockers:
        return 3, {
            "status": "blocked",
            "increment": args.increment,
            "changed": False,
            "blockers": list(dict.fromkeys(blockers)),
        }

    planned, preserved, manual_integrations = _planned_files(root)
    preview_hash = _preview_hash(root, planned)
    result = {
        "status": "dry-run" if args.dry_run else "prepared",
        "increment": args.increment,
        "profile_id": PROFILE_ID,
        "changed": False,
        "preview_hash": preview_hash,
        "created": [path.relative_to(root).as_posix() for path, _ in planned],
        "preserved": preserved,
        "manual_integrations": manual_integrations,
        "readiness": readiness["status"],
    }
    if args.dry_run:
        return 0, result
    if not args.apply or not args.authorize:
        raise PreparationError("Aplicar el scaffold requiere --apply y --authorize tras revisar el dry-run.")
    if args.preview_hash != preview_hash:
        raise PreparationError("El preview hash no coincide; repita el dry-run antes de escribir.")

    manifest_path = root / ".lks-sdd" / "project.json"
    original_manifest = manifest_path.read_bytes()
    created_files: list[Path] = []
    created_dirs: set[Path] = set()
    try:
        for destination, content in planned:
            missing: list[Path] = []
            parent = destination.parent
            while parent != root and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.update(missing)
            with destination.open("xb") as stream:
                stream.write(content)
            created_files.append(destination)

        manifest["phase"] = "implementation"
        manifest["gate"] = "G3"
        manifest["active_increment"] = args.increment
        manifest["implementation"] = {
            "status": "in-progress",
            "increment": args.increment,
            "profile_id": PROFILE_ID,
            "profile_version": "1.0.0-candidate.1",
            "changed_paths": [path.relative_to(root).as_posix() for path in created_files],
            "evidence_ids": [],
        }
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, manifest_path)
    except (OSError, FileExistsError) as exc:
        manifest_path.write_bytes(original_manifest)
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for directory in sorted(created_dirs, key=lambda item: len(item.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise PreparationError(f"La materialización se revirtió: {exc}") from exc
    result.update({"status": "prepared", "changed": True})
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        code, result = prepare(args)
    except PreparationError as exc:
        code, result = 2, {"status": "error", "changed": False, "error": str(exc)}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        for blocker in result.get("blockers", []):
            print(f"BLOCKER: {blocker}")
        if result.get("preview_hash"):
            print(f"preview_hash={result['preview_hash']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
