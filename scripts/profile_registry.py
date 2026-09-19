#!/usr/bin/env python3
"""Discover and strictly qualify LKS-SDD technology profiles.

Capabilities are reusable implementation units, but a closed profile is the
smallest selectable unit. A profile is supported when its descriptor, driver,
scaffold and generated structural lock agree.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROFILES_ROOT = PLUGIN_ROOT / "profiles"
CATALOG_PATH = PROFILES_ROOT / "catalog.json"
TRANSIENT_PARTS = {
    ".git", ".venv", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".next", ".angular", "test-results", "playwright-report",
}
TRANSIENT_SUFFIXES = {".pyc", ".pyo", ".tsbuildinfo"}
@dataclass(frozen=True)
class ProfileBundle:
    """Resolved files and parsed contracts for one catalogued profile."""

    profile_id: str
    root: Path | None
    catalog_entry: dict[str, Any]
    profile: dict[str, Any]
    driver: dict[str, Any]
    lock: dict[str, Any]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ProfileSupport:
    """Product-facing automation support for one selected profile."""

    profile_id: str
    discovered: bool
    catalogued: bool
    profile_version: str | None
    family_id: str | None
    profile_scope: str | None
    lifecycle: str | None
    support_level: str | None
    documentable: bool
    analyzable: bool
    implementable: bool
    verifiable: bool
    validated_lock: bool
    structural_composition: bool
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "discovered": self.discovered,
            "catalogued": self.catalogued,
            "profile_version": self.profile_version,
            "family_id": self.family_id,
            "profile_scope": self.profile_scope,
            "lifecycle": self.lifecycle,
            "support_level": self.support_level,
            "capabilities": {
                "documentable": self.documentable,
                "analyzable": self.analyzable,
                "implementable": self.implementable,
                "verifiable": self.verifiable,
            },
            "validated_lock": self.validated_lock,
            "structural_composition": self.structural_composition,
            "errors": list(self.errors),
        }


def _relative(path: Path) -> str:
    try:
        return path.relative_to(PLUGIN_ROOT).as_posix()
    except ValueError:
        return str(path)


def _load_object(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {}, f"No se puede leer {_relative(path)}: {exc}"
    if not isinstance(value, dict):
        return {}, f"{_relative(path)} no contiene un objeto JSON."
    return value, None


def _schema_errors(
    instance: dict[str, Any], schema_name: str, label: str
) -> list[str]:
    # Imported lazily so lightweight discovery does not load the full engine.
    from validate_project import validate_json_schema

    schema, error = _load_object(PLUGIN_ROOT / "schemas" / schema_name)
    if error:
        return [error]
    return validate_json_schema(instance, schema, label)


def load_catalog() -> tuple[dict[str, Any], list[str]]:
    catalog, error = _load_object(CATALOG_PATH)
    errors = [error] if error else []
    if catalog:
        errors.extend(
            _schema_errors(
                catalog, "profile-catalog.schema.json", "profile_catalog"
            )
        )
        for key in ("families", "capabilities", "profiles"):
            values = catalog.get(key, [])
            identifiers = [
                item.get("id") for item in values if isinstance(item, dict)
            ]
            if len(identifiers) != len(set(identifiers)):
                errors.append(
                    f"profiles/catalog.json contiene IDs duplicados en {key}."
                )
        family_ids = {
            item.get("id")
            for item in catalog.get("families", [])
            if isinstance(item, dict)
        }
        for entry in catalog.get("profiles", []):
            if (
                isinstance(entry, dict)
                and entry.get("family_id") not in family_ids
            ):
                errors.append(
                    f"{entry.get('id')}: family_id no existe en el catálogo."
                )
    return catalog, list(dict.fromkeys(item for item in errors if item))


def _catalog_entries(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): item
        for item in catalog.get("profiles", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _capability_entries(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): item
        for item in catalog.get("capabilities", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def discover_profiles() -> dict[str, Path]:
    """Return descriptor-declared profile IDs mapped to local directories."""
    discovered: dict[str, Path] = {}
    if not PROFILES_ROOT.is_dir():
        return discovered
    for candidate in sorted(PROFILES_ROOT.iterdir()):
        if not candidate.is_dir() or candidate.is_symlink():
            continue
        profile_file = candidate / "technology-profile.yaml"
        if not profile_file.is_file():
            continue
        profile, error = _load_object(profile_file)
        profile_id = profile.get("id") if error is None else None
        if isinstance(profile_id, str) and profile_id:
            discovered[profile_id] = candidate
    return discovered


def profile_source_files(scaffold: Path) -> list[Path]:
    """List deterministic, distributable scaffold inputs."""
    if not scaffold.is_dir() or scaffold.is_symlink():
        return []
    files: list[Path] = []
    for current, directories, names in os.walk(scaffold, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            name
            for name in directories
            if name not in TRANSIENT_PARTS
            and not (current_path / name).is_symlink()
        )
        for name in sorted(names):
            path = current_path / name
            if path.is_symlink() or path.suffix in TRANSIENT_SUFFIXES:
                continue
            files.append(path)
    return files


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in profile_source_files(root):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def sha256_prepare_sources(driver: dict[str, Any]) -> str:
    """Hash every exact source consumed by the prepare driver."""
    digest = hashlib.sha256()
    sources = driver.get("prepare", {}).get("sources", [])
    for source in sorted(
        (item for item in sources if isinstance(item, dict)),
        key=lambda item: (str(item.get("to", "")), str(item.get("from", ""))),
    ):
        declared = str(source.get("from", ""))
        path = (PLUGIN_ROOT / declared).resolve()
        try:
            path.relative_to(PLUGIN_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"Fuente de perfil fuera del plugin: {declared}") from exc
        if path.is_symlink() or not path.exists():
            raise ValueError(f"Fuente de perfil ausente o enlazada: {declared}")
        if path.is_file():
            files = [path]
            base = path.parent
        else:
            files = profile_source_files(path)
            base = path
        if not files:
            raise ValueError(f"Fuente de perfil vacía: {declared}")
        digest.update(declared.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(source.get("to", "")).encode("utf-8"))
        digest.update(b"\0")
        for item in files:
            digest.update(item.relative_to(base).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(item.read_bytes()).digest())
    variant = driver.get("variant")
    if variant:
        for relative in [variant["resolution"], "profiles/architecture-contracts.json"]:
            path = (PLUGIN_ROOT / relative).resolve()
            path.relative_to(PLUGIN_ROOT.resolve())
            digest.update(relative.encode("utf-8"))
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def capability_digest(capability: dict[str, Any]) -> str:
    canonical = json.dumps(
        capability, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def composition_digest(
    *,
    profile_sha256: str,
    driver_sha256: str,
    scaffold_sha256: str,
    capabilities: list[dict[str, Any]],
    gate_ids: list[str],
) -> str:
    canonical = json.dumps(
        {
            "profile_sha256": profile_sha256,
            "driver_sha256": driver_sha256,
            "scaffold_sha256": scaffold_sha256,
            "capabilities": capabilities,
            "gate_ids": sorted(gate_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_profile_bundle(profile_id: str) -> ProfileBundle:
    catalog, catalog_errors = load_catalog()
    entries = _catalog_entries(catalog)
    entry = entries.get(profile_id, {})
    errors = list(catalog_errors)
    if not entry:
        errors.append(
            f"El perfil {profile_id} no está incluido en profiles/catalog.json."
        )
        root = discover_profiles().get(profile_id)
    else:
        expected = PLUGIN_ROOT / str(entry.get("path", ""))
        try:
            expected.resolve().relative_to(PROFILES_ROOT.resolve())
        except ValueError:
            errors.append(f"{profile_id}: path de catálogo fuera de profiles/.")
        root = expected
    if root is None or not root.is_dir() or root.is_symlink():
        errors.append(
            f"{profile_id}: no existe un directorio de perfil regular."
        )
        return ProfileBundle(
            profile_id, None, entry, {}, {}, {}, tuple(dict.fromkeys(errors))
        )

    profile, profile_error = _load_object(root / "technology-profile.yaml")
    driver, driver_error = _load_object(root / "profile-driver.json")
    lock, lock_error = _load_object(root / "technology-profile.lock.json")
    errors.extend(
        item for item in (profile_error, driver_error, lock_error) if item
    )
    if profile:
        errors.extend(
            _schema_errors(
                profile, "technology-profile.schema.json", f"profile[{profile_id}]"
            )
        )
    if driver:
        errors.extend(
            _schema_errors(
                driver, "profile-driver.schema.json", f"driver[{profile_id}]"
            )
        )
    if lock:
        errors.extend(
            _schema_errors(
                lock,
                "technology-profile-lock.schema.json",
                f"lock[{profile_id}]",
            )
        )
    return ProfileBundle(
        profile_id,
        root,
        entry,
        profile,
        driver,
        lock,
        tuple(dict.fromkeys(errors)),
    )


def validate_profile_bundle(
    profile_id: str, *, require_validated: bool = True
) -> list[str]:
    """Validate one exact catalogued composition and its structural lock."""
    bundle = load_profile_bundle(profile_id)
    errors = list(bundle.errors)
    if bundle.root is None:
        return errors
    profile, driver, lock, entry = (
        bundle.profile,
        bundle.driver,
        bundle.lock,
        bundle.catalog_entry,
    )
    if driver.get("variant"):
        variant = driver["variant"]
        try:
            architecture = json.loads((PROFILES_ROOT / "architecture-contracts.json").read_text())
            contract = next(c for c in architecture["contracts"] if c["id"] == variant["contract_id"])
            if contract.get("selectable") is not False or profile_id not in contract["profile_ids"]:
                raise ValueError("variant contract mismatch")
            path = (PLUGIN_ROOT / variant["resolution"]).resolve()
            path.relative_to(PROFILES_ROOT.resolve())
            resolution = json.loads(path.read_text())
            if resolution.get("profile_id") != profile_id or not resolution.get("runtimes") or not resolution.get("images"):
                raise ValueError("exact technology resolution incomplete")
        except (OSError, ValueError, KeyError, StopIteration):
            errors.append(f"{profile_id}: arquitectura o variante exacta inválida/incompleta.")
    catalog, _ = load_catalog()
    capabilities = _capability_entries(catalog)
    profile_path = bundle.root / "technology-profile.yaml"
    driver_path = bundle.root / "profile-driver.json"
    scaffold = bundle.root / "scaffold"

    if (
        profile.get("id") != profile_id
        or driver.get("profile_id") != profile_id
        or lock.get("profile_id") != profile_id
    ):
        errors.append(
            f"{profile_id}: descriptor, driver y lock deben usar el mismo ID."
        )
    version = profile.get("version")
    if (
        driver.get("profile_version") != version
        or lock.get("profile_version") != version
    ):
        errors.append(
            f"{profile_id}: las versiones de descriptor, driver y lock divergen."
        )
    for field in ("family_id", "profile_scope", "lifecycle"):
        if entry.get(field) != profile.get(field):
            errors.append(
                f"{profile_id}: {field} diverge entre catálogo y descriptor."
            )
    try:
        source_hash = sha256_prepare_sources(driver)
    except (OSError, ValueError) as exc:
        source_hash = ""
        errors.append(f"{profile_id}: fuentes de preparación inválidas: {exc}.")

    required_caps = profile.get("required_capabilities", [])
    bound_caps = {
        item.get("capability_id")
        for item in profile.get("capability_bindings", [])
        if isinstance(item, dict)
    }
    locked_caps = {
        item.get("id"): item
        for item in lock.get("capabilities", [])
        if isinstance(item, dict)
    }
    expected_gate_ids: set[str] = set()
    for cap_id in required_caps:
        cap = capabilities.get(cap_id)
        if cap is None:
            errors.append(f"{profile_id}: capability desconocida {cap_id}.")
            continue
        if cap_id not in bound_caps:
            errors.append(f"{profile_id}: capability sin binding {cap_id}.")
        expected_gate_ids.update(cap.get("gate_ids", []))
        locked = locked_caps.get(cap_id)
        if locked is None:
            errors.append(f"{profile_id}: capability ausente del lock {cap_id}.")
        else:
            if locked.get("version") != cap.get("version"):
                errors.append(
                    f"{profile_id}: versión bloqueada incorrecta para {cap_id}."
                )
            if locked.get("digest") != capability_digest(cap):
                errors.append(
                    f"{profile_id}: digest de capability incorrecto para {cap_id}."
                )
    excluded = set(profile.get("excluded_capabilities", []))
    overlap = sorted(set(required_caps) & excluded)
    if overlap:
        errors.append(
            f"{profile_id}: capabilities requeridas y excluidas: {overlap}."
        )

    declared_gates = set(
        profile.get("gates", {}).get("capability_gate_ids", [])
    )
    if declared_gates != expected_gate_ids:
        errors.append(
            f"{profile_id}: capability_gate_ids no coincide con el catálogo."
        )
    composition_gate = profile.get("gates", {}).get("composition_gate_id")
    driver_checks = {
        item.get("id"): item
        for item in driver.get("verify", {}).get("checks", [])
        if isinstance(item, dict)
    }
    required_driver_gates = expected_gate_ids | (
        {composition_gate} if composition_gate else set()
    )
    missing_driver = sorted(required_driver_gates - set(driver_checks))
    if missing_driver:
        errors.append(
            f"{profile_id}: el driver no resuelve gates: {missing_driver}."
        )
    locked_gates = {
        item.get("id"): item
        for item in lock.get("gates", [])
        if isinstance(item, dict)
    }
    missing_lock_gates = sorted(required_driver_gates - set(locked_gates))
    if missing_lock_gates:
        errors.append(
            f"{profile_id}: el lock no cubre gates: {missing_lock_gates}."
        )

    if (
        profile_path.is_file()
        and lock.get("profile_sha256") != sha256_file(profile_path)
    ):
        errors.append(
            f"{profile_id}: profile_sha256 no coincide con el descriptor."
        )
    if (
        driver_path.is_file()
        and lock.get("driver_sha256") != sha256_file(driver_path)
    ):
        errors.append(f"{profile_id}: driver_sha256 no coincide con el driver.")
    if lock.get("scaffold_sha256") != source_hash:
        errors.append(
            f"{profile_id}: scaffold_sha256 no coincide con los recursos."
        )

    locked_capability_list = [
        locked_caps[cap_id]
        for cap_id in sorted(required_caps)
        if cap_id in locked_caps
    ]
    expected_composition = composition_digest(
        profile_sha256=lock.get("profile_sha256", ""),
        driver_sha256=lock.get("driver_sha256", ""),
        scaffold_sha256=lock.get("scaffold_sha256", ""),
        capabilities=locked_capability_list,
        gate_ids=sorted(required_driver_gates),
    )
    composition = lock.get("composition", {})
    if composition.get("gate_id") != composition_gate:
        errors.append(
            f"{profile_id}: el gate de composición del lock diverge."
        )
    if composition.get("digest") != expected_composition:
        errors.append(
            f"{profile_id}: el digest de composición no coincide."
        )

    active = profile.get("lifecycle") == "active"
    if require_validated and active and lock.get("structural") is not True:
        errors.append(f"{profile_id}: el perfil active requiere un lock estructural válido.")
    if require_validated and not active and lock.get("structural") is True:
        errors.append(f"{profile_id}: un perfil no active no puede declarar un lock validado.")
    return list(dict.fromkeys(errors))

def resolve_profile(profile_id: str) -> ProfileSupport:
    """Resolve support from the catalogued structural profile contract."""
    bundle = load_profile_bundle(profile_id)
    profile = bundle.profile
    catalogued = bool(bundle.catalog_entry)
    discovered = bundle.root is not None
    errors = validate_profile_bundle(profile_id, require_validated=True)
    lifecycle = (
        profile.get("lifecycle")
        if isinstance(profile.get("lifecycle"), str)
        else None
    )
    lock_valid = bool(bundle.lock.get("structural") is True and not errors)
    structural_composition = lock_valid
    supported = (
        catalogued
        and discovered
        and lifecycle == "active"
        and lock_valid
        and structural_composition
    )
    if not catalogued:
        errors = [
            "El perfil no está incluido en el catálogo local; puede "
            "documentarse, pero este plugin no garantiza implementación "
            "ni verificación."
        ]
    return ProfileSupport(
        profile_id=profile_id,
        discovered=discovered,
        catalogued=catalogued,
        profile_version=(
            profile.get("version")
            if isinstance(profile.get("version"), str)
            else None
        ),
        family_id=(
            profile.get("family_id")
            if isinstance(profile.get("family_id"), str)
            else None
        ),
        profile_scope=(
            profile.get("profile_scope")
            if isinstance(profile.get("profile_scope"), str)
            else None
        ),
        lifecycle=lifecycle,
        support_level=(
            profile.get("support_level")
            if isinstance(profile.get("support_level"), str)
            else None
        ),
        documentable=True,
        analyzable=True,
        implementable=supported,
        verifiable=supported,
        validated_lock=lock_valid,
        structural_composition=structural_composition,
        errors=tuple(dict.fromkeys(errors)),
    )
