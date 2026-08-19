#!/usr/bin/env python3
"""Validate the LKS-SDD H0 reference profile, lock, and scaffold contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from validate_project import validate_json_schema


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "WEB-FASTAPI-REACT-KEYCLOAK-PG"
PROFILE_ROOT = PLUGIN_ROOT / "profiles" / PROFILE_ID
REQUIRED_SCAFFOLD = {
    ".github/workflows/ci.yml",
    ".gitlab-ci.yml",
    ".gitignore",
    "apps/backend/pyproject.toml",
    "apps/backend/uv.lock",
    "apps/backend/src/lks_sdd_app/main.py",
    "apps/backend/tests/test_api.py",
    "apps/frontend/package.json",
    "apps/frontend/pnpm-lock.yaml",
    "apps/frontend/src/App.tsx",
    "apps/frontend/src/App.test.tsx",
    "infra/compose/compose.yaml",
    "infra/keycloak/realm-export.json",
    "infra/containers/backend.Dockerfile",
    "infra/containers/frontend.Dockerfile",
}


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"No se puede leer {path.relative_to(PLUGIN_ROOT)}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(PLUGIN_ROOT)} debe contener un objeto.")
        return {}
    return value


def validate_profile(require_validated: bool = True) -> list[str]:
    errors: list[str] = []
    profile_path = PROFILE_ROOT / "technology-profile.yaml"
    lock_path = PROFILE_ROOT / "technology-profile.lock.json"
    profile = _load_json(profile_path, errors)
    lock = _load_json(lock_path, errors)
    if errors:
        return errors

    profile_schema = _load_json(PLUGIN_ROOT / "schemas" / "technology-profile.schema.json", errors)
    lock_schema = _load_json(PLUGIN_ROOT / "schemas" / "technology-profile-lock.schema.json", errors)
    errors.extend(validate_json_schema(profile, profile_schema, "profile"))
    errors.extend(validate_json_schema(lock, lock_schema, "lock"))
    if profile.get("id") != PROFILE_ID or lock.get("profile_id") != PROFILE_ID:
        errors.append("El perfil y el lock deben usar el identificador H0 canónico.")
    if profile.get("version") != lock.get("profile_version"):
        errors.append("La versión del perfil no coincide con el lock.")
    if profile.get("support_level") != "H0":
        errors.append("El perfil de referencia debe declarar soporte H0.")
    capabilities = profile.get("capabilities", {})
    if not all(capabilities.get(name) is True for name in ("documentable", "analyzable", "implementable", "verifiable")):
        errors.append("El perfil H0 debe declarar las cuatro capacidades verificables.")
    if require_validated and lock.get("validated") is not True:
        errors.append("El lock H0 no puede publicarse como válido antes de superar la puerta técnica.")

    component_names = {item.get("name") for item in lock.get("components", []) if isinstance(item, dict)}
    for required in {"Python", "uv", "FastAPI", "Node.js", "pnpm", "React", "PostgreSQL", "Keycloak"}:
        if required not in component_names:
            errors.append(f"Falta el componente bloqueado {required}.")

    scaffold = PROFILE_ROOT / "scaffold"
    for relative in sorted(REQUIRED_SCAFFOLD):
        if not (scaffold / relative).is_file():
            errors.append(f"Falta recurso del scaffold H0: {relative}")

    try:
        backend = tomllib.loads((scaffold / "apps/backend/pyproject.toml").read_text(encoding="utf-8"))
        dependencies = backend["project"]["dependencies"] + backend["dependency-groups"]["dev"]
        for dependency in dependencies:
            if "==" not in dependency:
                errors.append(f"Dependencia Python sin pin exacto: {dependency}")
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        errors.append(f"pyproject.toml del perfil no es validable: {exc}")

    frontend = _load_json(scaffold / "apps/frontend/package.json", errors)
    for section in ("dependencies", "devDependencies"):
        for name, version in frontend.get(section, {}).items():
            if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", str(version)):
                errors.append(f"Dependencia npm sin pin exacto: {name}={version}")
    if frontend.get("packageManager") != "pnpm@10.34.5":
        errors.append("El packageManager debe coincidir con el lock del perfil.")

    runtime_files = [
        scaffold / "infra/compose/compose.yaml",
        scaffold / "infra/containers/backend.Dockerfile",
        scaffold / "infra/containers/frontend.Dockerfile",
    ]
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?i)(?:image:|FROM)\s+\S+:latest\b", text):
            errors.append(f"Etiqueta latest prohibida en {path.relative_to(PLUGIN_ROOT)}")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("image:", "FROM ")) and "@sha256:" not in stripped:
                errors.append(f"Imagen OCI sin digest en {path.relative_to(PLUGIN_ROOT)}: {stripped}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-unvalidated", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    errors = validate_profile(require_validated=not args.allow_unvalidated)
    result = {"valid": not errors, "profile_id": PROFILE_ID, "errors": errors}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif errors:
        print("INVALID")
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print(f"VALID: {PROFILE_ID}")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
