#!/usr/bin/env python3
"""Validate the synthetic fixture inventory and its immutable hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON ilegible {path}: {exc}") from exc


def validate_fixture_manifest(plugin_root: Path) -> dict[str, object]:
    manifest_path = plugin_root / "quality" / "fixture-manifest.json"
    try:
        manifest = _load_json(manifest_path)
    except ValueError as exc:
        return {"status": "failed", "fixture_count": 0, "errors": [str(exc)]}
    if not isinstance(manifest, dict):
        return {
            "status": "failed",
            "fixture_count": 0,
            "errors": ["El manifiesto de fixtures debe ser un objeto JSON."],
        }

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
        path_parts = Path(relative).parts if isinstance(relative, str) else ()
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in path_parts
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
        if path.is_symlink() or (
            hasattr(path, "is_junction") and path.is_junction()
        ):
            errors.append(f"Fixture enlazado no permitido: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Fixture ausente: {relative}")
            continue
        try:
            payload = _load_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict) or payload.get("id") != entry.get("id"):
            errors.append(f"ID no coincidente en {relative}.")
        expected_hash = entry.get("sha256")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = validate_fixture_manifest(args.plugin_root.expanduser().resolve())
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("VALID" if result["status"] == "passed" else "INVALID")
        print(f"fixtures={result['fixture_count']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
