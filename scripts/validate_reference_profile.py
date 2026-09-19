#!/usr/bin/env python3
"""Validate one or all closed LKS-SDD technology profile compositions."""

from __future__ import annotations

import sys
from pathlib import Path

if str(__file__).startswith("\\\\?\\"):
    _bootstrap = Path(__file__).with_name("import_bootstrap.py")
    _namespace = {}
    exec(compile(_bootstrap.read_bytes(), str(_bootstrap), "exec"), _namespace)
    _namespace["ensure_import_path"](__file__)
    del _bootstrap, _namespace

import argparse
import hashlib
import json
import re
import tomllib
from typing import Any

from profile_registry import (
    PLUGIN_ROOT,
    PROFILES_ROOT,
    load_catalog,
    load_profile_bundle,
    profile_source_files,
    validate_profile_bundle,
)


# Compatibility aliases for 1.1 callers. New code must resolve bindings.
PROFILE_ID = "WEB-FASTAPI-REACT-KEYCLOAK-PG"
PROFILE_ROOT = PROFILES_ROOT / PROFILE_ID
EXACT_NPM_VERSION = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$"
)


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"No se puede leer {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path} debe contener un objeto.")
        return {}
    return value


def _validate_dependency_pins(profile_id: str) -> list[str]:
    bundle = load_profile_bundle(profile_id)
    if bundle.root is None:
        return []
    errors: list[str] = []
    scaffold = bundle.root / "scaffold"
    files = profile_source_files(scaffold)
    if bundle.driver.get("variant"):
        for source in bundle.driver.get("prepare", {}).get("sources", []):
            origin = (PLUGIN_ROOT / source["from"]).resolve()
            origin.relative_to(PLUGIN_ROOT.resolve())
            files.extend([origin] if origin.is_file() else profile_source_files(origin))
        files = sorted(set(files))
    for path in files:
        relative = path.relative_to(PLUGIN_ROOT).as_posix()
        if path.name == "package.json":
            package = _load_json(path, errors)
            for section in (
                "dependencies",
                "devDependencies",
                "optionalDependencies",
            ):
                for name, version in package.get(section, {}).items():
                    if not EXACT_NPM_VERSION.fullmatch(str(version)):
                        errors.append(
                            f"{profile_id}: dependencia npm sin pin exacto "
                            f"en {relative}: {name}={version}"
                        )
            sibling_locks = {
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
            }
            if not any((path.parent / name).is_file() for name in sibling_locks):
                errors.append(
                    f"{profile_id}: {relative} no tiene lock npm/pnpm/yarn."
                )
        elif path.name == "pyproject.toml":
            try:
                project = tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError) as exc:
                errors.append(f"{profile_id}: {relative} no es TOML válido: {exc}")
                continue
            dependencies = list(project.get("project", {}).get("dependencies", []))
            for group in project.get("dependency-groups", {}).values():
                if isinstance(group, list):
                    dependencies.extend(group)
            for dependency in dependencies:
                if "==" not in str(dependency):
                    errors.append(
                        f"{profile_id}: dependencia Python sin pin exacto "
                        f"en {relative}: {dependency}"
                    )
            if not (path.parent / "uv.lock").is_file():
                errors.append(f"{profile_id}: {relative} no tiene uv.lock.")

    for path in files:
        if path.name == "compose.yaml" or path.name.endswith("Dockerfile"):
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if re.search(r"(?i)(?:image:|FROM)\s+\S+:latest\b", stripped):
                    errors.append(
                        f"{profile_id}: etiqueta latest prohibida en "
                        f"{path.relative_to(PLUGIN_ROOT).as_posix()}."
                    )
                if stripped.startswith(("image:", "FROM ")) and (
                    "@sha256:" not in stripped
                ):
                    errors.append(
                        f"{profile_id}: imagen OCI sin digest en "
                        f"{path.relative_to(PLUGIN_ROOT).as_posix()}: {stripped}"
                    )
    return errors


def validate_profile(
    profile_id: str = PROFILE_ID, *, require_validated: bool = True
) -> list[str]:
    errors = validate_profile_bundle(
        profile_id, require_validated=require_validated
    )
    errors.extend(_validate_dependency_pins(profile_id))
    return list(dict.fromkeys(errors))


def validate_consumer_profile_lock(
    project_root: Path,
    *,
    profile_id: str = PROFILE_ID,
    binding_id: str | None = None,
    required: bool = True,
) -> tuple[list[str], dict[str, str | None]]:
    """Require a consumer binding lock to equal the packaged immutable lock."""
    errors: list[str] = []
    root = project_root.expanduser().resolve()
    if binding_id is None:
        relative = Path(".lks-sdd/profile.lock.json")
    else:
        if not re.fullmatch(r"BIND-[0-9]{3}", binding_id):
            return ["binding_id debe usar BIND-###."], {
                "path": None,
                "sha256": None,
                "expected_sha256": None,
                "profile_id": profile_id,
                "binding_id": binding_id,
            }
        relative = Path(f".lks-sdd/profiles/{binding_id}.lock.json")
    consumer_path = root / relative
    bundle = load_profile_bundle(profile_id)
    packaged_path = (
        bundle.root / "technology-profile.lock.json"
        if bundle.root is not None
        else PROFILES_ROOT / profile_id / "technology-profile.lock.json"
    )
    details: dict[str, str | None] = {
        "path": relative.as_posix(),
        "sha256": None,
        "expected_sha256": None,
        "profile_id": profile_id,
        "binding_id": binding_id,
    }
    if bundle.driver.get("variant") and bundle.profile.get("profile_scope") == "system":
        return ["La variante de sistema se selecciona mediante INT.Exact composition, no mediante un binding de unidad."], details
    try:
        packaged = packaged_path.read_bytes()
    except OSError as exc:
        errors.append(
            f"No se puede leer el lock empaquetado de {profile_id}: {exc}"
        )
        return errors, details
    details["expected_sha256"] = hashlib.sha256(packaged).hexdigest()
    is_link = consumer_path.is_symlink() or (
        hasattr(consumer_path, "is_junction")
        and consumer_path.is_junction()
    )
    if is_link:
        errors.append(
            f"El lock consumidor {relative.as_posix()} no puede ser un enlace."
        )
        return errors, details
    if consumer_path.exists() and not consumer_path.is_file():
        errors.append(
            f"El lock consumidor {relative.as_posix()} debe ser un archivo."
        )
        return errors, details
    if not consumer_path.is_file():
        if required:
            errors.append(
                f"Falta el lock exacto de {profile_id} en "
                f"{relative.as_posix()}."
            )
        return errors, details
    try:
        consumer = consumer_path.read_bytes()
        decoded = json.loads(consumer.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(
            f"El lock consumidor {relative.as_posix()} no es legible: {exc}"
        )
        return errors, details
    details["sha256"] = hashlib.sha256(consumer).hexdigest()
    if (
        not isinstance(decoded, dict)
        or decoded.get("profile_id") != profile_id
    ):
        errors.append(
            f"El lock consumidor no pertenece a {profile_id}."
        )
    if consumer != packaged:
        errors.append(
            f"El lock de {profile_id} diverge del lock exacto empaquetado."
        )
    if bundle.driver.get("variant") and binding_id:
        from technology_resolution import diagnose
        manifest_path = root / ".lks-sdd/project.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            bindings = manifest.get("technology", {}).get("profile_bindings", [])
            binding = next(item for item in bindings if item.get("binding_id") == binding_id)
            unit_root = (root / binding.get("unit_path", ".")).resolve()
            unit_root.relative_to(root)
            snapshot_path = root / f".lks-sdd/profiles/{binding_id}.resolution.json"
            snapshot = json.loads(snapshot_path.read_text()) if snapshot_path.is_file() else None
            if required and snapshot is None:
                errors.append(f"{binding_id}: dependency resolution snapshot is missing; explicit preparation is required")
            diagnosis = diagnose(unit_root, profile_id, snapshot=snapshot)
            details["dependency_fingerprint"] = diagnosis["dependency_fingerprint"]
            details["compatibility"] = diagnosis["compatibility"]
            if required and (diagnosis["compatibility"] != "catalog-match" or diagnosis["dependency_drift"]):
                errors.append(f"{binding_id}: consumer technology requires reconciliation: " + "; ".join(diagnosis["reasons"]))
        except (OSError, ValueError, KeyError, StopIteration):
            errors.append(f"{binding_id}: consumer dependency inventory cannot be resolved safely")
    return errors, details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="append", dest="profiles")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--allow-unvalidated", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    catalog, catalog_errors = load_catalog()
    catalog_ids = [
        item["id"]
        for item in catalog.get("profiles", [])
        if isinstance(item, dict)
    ]
    selected = catalog_ids if args.all else (args.profiles or [PROFILE_ID])
    results = []
    for profile_id in selected:
        errors = list(catalog_errors)
        errors.extend(
            validate_profile(
                profile_id,
                require_validated=not args.allow_unvalidated,
            )
        )
        results.append(
            {
                "valid": not errors,
                "profile_id": profile_id,
                "errors": list(dict.fromkeys(errors)),
            }
        )
    valid = all(item["valid"] for item in results)
    output: dict[str, Any] = {
        "valid": valid,
        "profile_count": len(results),
        "profiles": results,
    }
    if len(results) == 1:
        output.update(results[0])
    if args.as_json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for item in results:
            print(
                f"{'VALID' if item['valid'] else 'INVALID'}: "
                f"{item['profile_id']}"
            )
            for error in item["errors"]:
                print(f"ERROR: {error}")
    return 0 if valid else 2


if __name__ == "__main__":
    sys.exit(main())
