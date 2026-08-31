"""Conservative read-only impact report; never waives recertification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from profile_registry import CERTIFICATION_ENGINE_FILES, load_catalog, load_profile_bundle


def impact(paths: list[str]) -> dict:
    catalog, errors = load_catalog()
    affected = []
    unknown = any(not p.startswith(("profiles/", "scripts/", "schemas/", "skills/", "tests/", "quality/", "docs/", ".github/")) for p in paths)
    shared = set(paths) & set(CERTIFICATION_ENGINE_FILES)
    for entry in catalog.get("profiles", []):
        bundle = load_profile_bundle(entry["id"])
        prefixes = [entry["path"] + "/"] + [s["from"].rstrip("/") + "/" for s in bundle.driver.get("prepare", {}).get("sources", [])]
        reasons = []
        for path in paths:
            if any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in prefixes):
                reasons.append("profile input changed: " + path)
            elif path in shared or path in {"profiles/catalog.json", "profiles/architecture-contracts.json"}:
                reasons.append("shared qualification contract changed: " + path)
            elif path.startswith(("schemas/", "skills/", "scripts/", "quality/", "tests/")):
                reasons.append("possible semantic or fixture dependency: " + path)
        if unknown or errors:
            reasons.append("uncertain impact expands to all profiles")
        if reasons:
            affected.append({"profile_id": entry["id"], "contract_id": bundle.driver.get("variant", {}).get("contract_id"),
                             "variant": entry["id"] if bundle.driver.get("variant") else None,
                             "lock": entry["path"] + "/technology-profile.lock.json",
                             "certification": entry["path"] + "/certification-evidence.json",
                             "fixtures": [s["from"] for s in bundle.driver.get("prepare", {}).get("sources", [])],
                             "reasons": sorted(set(reasons))})
    return {"schema_version": "1.0", "read_only": True, "recertification_waived": False,
            "changed_paths": sorted(set(paths)), "affected": affected, "uncertainty": unknown or bool(errors), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print(json.dumps(impact([Path(p).as_posix() for p in args.paths]), indent=2))


if __name__ == "__main__": main()
