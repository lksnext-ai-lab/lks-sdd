#!/usr/bin/env python3
"""Validate the complete LKS-SDD specification contract for one project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_project import validate_project
from validate_reference_profile import PROFILE_ID, validate_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, manifest, _ = validate_project(args.project_root)
    errors = list(report.errors)
    warnings = list(report.warnings)
    if manifest:
        selected = manifest.get("technology", {}).get("selected_profile")
        if selected == PROFILE_ID:
            errors.extend(
                f"Perfil H0: {item}"
                for item in validate_profile(require_validated=True)
            )
        elif selected is not None:
            warnings.append(
                f"El perfil {selected} es documentable, pero no dispone de validación H0 en este plugin."
            )
        if manifest.get("route") == "adopt-existing":
            adoption = manifest.get("adoption", {})
            if adoption.get("status") != "materialized":
                errors.append(
                    "La ruta adopt-existing no tiene una baseline materializada."
                )
            if adoption.get("baseline_freshness") != "current":
                errors.append("La baseline adoptada no está marcada como vigente.")
    result = {
        "valid": not errors,
        "project_root": report.project_root,
        "schema_version": manifest.get("schema_version") if manifest else None,
        "plugin_version": manifest.get("plugin_version") if manifest else None,
        "route": manifest.get("route") if manifest else None,
        "errors": errors,
        "warnings": warnings,
        "checked_files": report.checked_files,
    }
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("VALID" if result["valid"] else "INVALID")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
