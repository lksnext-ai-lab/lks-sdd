#!/usr/bin/env python3
"""Discover LKS-SDD technology profiles and classify their automation support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROFILES_ROOT = PLUGIN_ROOT / "profiles"


@dataclass(frozen=True)
class ProfileSupport:
    """Resolved support for one selected technology profile."""

    profile_id: str
    discovered: bool
    profile_version: str | None
    support_level: str | None
    documentable: bool
    analyzable: bool
    implementable: bool
    verifiable: bool
    validated_lock: bool
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "discovered": self.discovered,
            "profile_version": self.profile_version,
            "support_level": self.support_level,
            "capabilities": {
                "documentable": self.documentable,
                "analyzable": self.analyzable,
                "implementable": self.implementable,
                "verifiable": self.verifiable,
            },
            "validated_lock": self.validated_lock,
            "errors": list(self.errors),
        }


def _load_object(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"No se puede leer {path.relative_to(PLUGIN_ROOT)}: {exc}"
    if not isinstance(value, dict):
        return {}, f"{path.relative_to(PLUGIN_ROOT)} no contiene un objeto."
    return value, None


def discover_profiles() -> dict[str, Path]:
    """Return profile IDs mapped to their directories without following links."""
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


def resolve_profile(profile_id: str) -> ProfileSupport:
    """Resolve declared capabilities; unknown profiles remain documentable only."""
    root = discover_profiles().get(profile_id)
    if root is None:
        return ProfileSupport(
            profile_id=profile_id,
            discovered=False,
            profile_version=None,
            support_level=None,
            documentable=True,
            analyzable=True,
            implementable=False,
            verifiable=False,
            validated_lock=False,
            errors=(
                "El perfil no está incluido en el registro local; puede documentarse, "
                "pero este plugin no garantiza implementación ni verificación.",
            ),
        )

    profile, profile_error = _load_object(root / "technology-profile.yaml")
    lock, lock_error = _load_object(root / "technology-profile.lock.json")
    errors = [item for item in (profile_error, lock_error) if item]
    capabilities = profile.get("capabilities", {})
    if not isinstance(capabilities, dict):
        capabilities = {}
        errors.append("capabilities no es un objeto.")
    profile_version = profile.get("version")
    if lock.get("profile_id") != profile_id:
        errors.append("El lock no pertenece al perfil seleccionado.")
    if lock.get("profile_version") != profile_version:
        errors.append("La versión del lock no coincide con el perfil.")
    validated_lock = lock.get("validated") is True and not errors
    implementable = capabilities.get("implementable") is True and validated_lock
    verifiable = capabilities.get("verifiable") is True and validated_lock
    return ProfileSupport(
        profile_id=profile_id,
        discovered=True,
        profile_version=profile_version if isinstance(profile_version, str) else None,
        support_level=(
            profile.get("support_level")
            if isinstance(profile.get("support_level"), str)
            else None
        ),
        documentable=capabilities.get("documentable") is True,
        analyzable=capabilities.get("analyzable") is True,
        implementable=implementable,
        verifiable=verifiable,
        validated_lock=validated_lock,
        errors=tuple(errors),
    )
