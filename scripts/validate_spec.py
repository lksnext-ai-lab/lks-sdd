#!/usr/bin/env python3
"""Validate the complete LKS-SDD specification contract for one project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_project import validate_project
from profile_registry import resolve_profile
from validate_reference_profile import PROFILE_ID, validate_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, manifest, _ = validate_project(args.project_root)
    errors = list(report.errors)
    warnings = list(report.warnings)
    automation_support = None
    if manifest:
        selected = manifest.get("technology", {}).get("selected_profile")
        if selected is not None:
            support = resolve_profile(selected)
            support_errors = list(support.errors)
            if selected == PROFILE_ID:
                support_errors.extend(validate_profile(require_validated=True))
            automation_support = {
                **support.as_dict(),
                "errors": list(dict.fromkeys(support_errors)),
            }
            if support_errors or not support.implementable:
                warnings.append(
                    f"El perfil {selected} es documentable, pero la automatización de implementación no está garantizada."
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
        "automation_support": automation_support,
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
