#!/usr/bin/env python3
"""Validate the synthetic fixture inventory and its immutable hashes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_quality_harness import validate_fixture_manifest


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
