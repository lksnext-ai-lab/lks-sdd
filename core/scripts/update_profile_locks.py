#!/usr/bin/env python3
"""Generate or check deterministic locks for every LKS-SDD profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from profile_registry import (
    PLUGIN_ROOT,
    capability_digest,
    certification_evidence_errors,
    composition_digest,
    load_catalog,
    load_profile_bundle,
    sha256_file,
    sha256_prepare_sources,
)


def _components(profile: dict[str, Any], driver: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if driver and driver.get("variant"):
        resolution = json.loads((PLUGIN_ROOT / driver["variant"]["resolution"]).read_text(encoding="utf-8"))
        values = []
        for section in ("packages", "runtimes", "tools", "images"):
            for name, version in sorted(resolution.get(section, {}).items()):
                values.append({"name": name, "version": json.dumps(version) if isinstance(version, list) else version,
                               "source": "resolved:" + section,
                               "digest": "sha256:" + version.partition("@sha256:")[2] if section == "images" else None})
        return values
    values: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for dimension, items in profile.get("dimensions", {}).items():
        for item in items:
            if not isinstance(item, dict):
                continue
            key = (
                str(item.get("name", "")),
                str(item.get("version_range", "")),
                str(dimension),
            )
            if key in seen:
                continue
            seen.add(key)
            values.append(
                {
                    "name": key[0],
                    "version": key[1],
                    "source": f"profile:{dimension}",
                    "digest": None,
                }
            )
    return sorted(
        values, key=lambda item: (item["source"], item["name"], item["version"])
    )


def build_lock(profile_id: str) -> dict[str, Any]:
    bundle = load_profile_bundle(profile_id)
    # Existing lock hash errors are intentionally ignored: this command repairs it.
    errors = [
        error
        for error in bundle.errors
        if "lock[" not in error
        and "technology-profile.lock.json" not in error
    ]
    if bundle.root is None or not bundle.profile or not bundle.driver:
        raise ValueError("; ".join(errors) or f"Perfil incompleto: {profile_id}")
    profile = bundle.profile
    driver = bundle.driver
    catalog, catalog_errors = load_catalog()
    if catalog_errors:
        raise ValueError("; ".join(catalog_errors))
    capabilities = {
        item["id"]: item
        for item in catalog.get("capabilities", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    required_caps = sorted(profile.get("required_capabilities", []))
    locked_caps: list[dict[str, Any]] = []
    for cap_id in required_caps:
        capability = capabilities.get(cap_id)
        if capability is None:
            raise ValueError(f"{profile_id}: capability desconocida {cap_id}")
        locked_caps.append(
            {
                "id": cap_id,
                "version": capability["version"],
                "digest": capability_digest(capability),
            }
        )

    checks = {
        item["id"]: item
        for item in driver.get("verify", {}).get("checks", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    composition_gate = profile.get("gates", {}).get("composition_gate_id")
    if not isinstance(composition_gate, str):
        raise ValueError(f"{profile_id}: falta composition_gate_id")
    gate_ids = sorted(
        set(profile.get("gates", {}).get("capability_gate_ids", []))
        | {composition_gate}
    )
    for gate_id in gate_ids:
        check = checks.get(gate_id)
        if check is None:
            raise ValueError(f"{profile_id}: el driver no implementa {gate_id}")
    profile_hash = sha256_file(bundle.root / "technology-profile.yaml")
    driver_hash = sha256_file(bundle.root / "profile-driver.json")
    scaffold_hash = sha256_prepare_sources(driver)
    composition_hash = composition_digest(
        profile_sha256=profile_hash,
        driver_sha256=driver_hash,
        scaffold_sha256=scaffold_hash,
        capabilities=locked_caps,
        gate_ids=gate_ids,
    )
    active = profile.get("lifecycle") == "active"
    certification = profile.get("certification", {})
    declared_certified = active and all(
        certification.get(field) == "passed"
        for field in ("technical_gate", "composition_gate", "e2e_eval")
    )
    evidence_errors = certification_evidence_errors(
        bundle,
        profile_sha256=profile_hash,
        driver_sha256=driver_hash,
        scaffold_sha256=scaffold_hash,
        composition_sha256=composition_hash,
        required_gate_ids=set(gate_ids),
    )
    certified = declared_certified and not evidence_errors
    gate_status = "passed" if certified else "not-run"
    locked_gates = [
        {
            "id": gate_id,
            "phase": checks[gate_id]["phase"],
            "required": bool(checks[gate_id]["required"]),
            "status": gate_status,
            "evidence": (
                f"profiles/{profile_id}/certification-evidence.json"
                if certified
                else f"profile {profile_id}: exact certification not available"
            ),
        }
        for gate_id in gate_ids
    ]
    generated_at = (
        certification.get("validated_at")
        if certified
        else "2026-08-21"
    ) or "2026-08-21"
    evidence = list(certification.get("evidence", []))
    if not evidence:
        evidence = [f"Profile {profile_id} awaits certification."]
    return {
        "schema_version": "2.0",
        "profile_id": profile_id,
        "profile_version": profile["version"],
        "generated_at": generated_at,
        "validated": certified,
        "profile_sha256": profile_hash,
        "driver_sha256": driver_hash,
        "scaffold_sha256": scaffold_hash,
        "capabilities": locked_caps,
        "components": _components(profile, driver),
        "gates": locked_gates,
        "composition": {
            "gate_id": profile["gates"]["composition_gate_id"],
            "status": gate_status,
            "digest": composition_hash,
        },
        "evidence": evidence,
    }


def _bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="append", dest="profiles")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog, errors = load_catalog()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    catalog_ids = [
        item["id"]
        for item in catalog.get("profiles", [])
        if isinstance(item, dict)
    ]
    selected = catalog_ids if args.all else (args.profiles or [])
    if not selected:
        parser.error("use --all or at least one --profile")
    failed = False
    for profile_id in selected:
        try:
            value = build_lock(profile_id)
            bundle = load_profile_bundle(profile_id)
            assert bundle.root is not None
            path = bundle.root / "technology-profile.lock.json"
            expected = _bytes(value)
            if args.check:
                current = path.read_bytes() if path.is_file() else b""
                status = "CURRENT" if current == expected else "STALE"
                failed = failed or current != expected
            else:
                path.write_bytes(expected)
                status = "UPDATED"
            print(f"{status}: {profile_id}")
        except (OSError, ValueError, AssertionError) as exc:
            failed = True
            print(f"ERROR: {profile_id}: {exc}")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
