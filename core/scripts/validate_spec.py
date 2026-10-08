#!/usr/bin/env python3
"""Validate one project contract without selecting or certifying technology."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_project import validate_project


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, manifest, _ = validate_project(args.project_root)
    errors, warnings = list(report.errors), list(report.warnings)
    if manifest and manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption", {})
        if adoption.get("status") != "materialized":
            errors.append("La ruta adopt-existing no tiene una baseline materializada.")
        if adoption.get("baseline_freshness") != "current":
            errors.append("La baseline adoptada no está marcada como vigente.")
    result = {"valid": not errors, "project_root": report.project_root,
              "schema_version": manifest.get("schema_version") if manifest else None,
              "plugin_version": manifest.get("plugin_version") if manifest else None,
              "route": manifest.get("route") if manifest else None,
              "errors": errors, "warnings": warnings, "checked_files": report.checked_files}
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
