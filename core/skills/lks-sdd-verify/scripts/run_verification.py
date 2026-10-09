#!/usr/bin/env python3
"""Legacy verification entrypoint retained only to direct projects to contract v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args, _ = parser.parse_known_args(argv)
    result = {"status": "blocked", "project_root": str(args.project_root),
              "reason": "Use lks_sdd.py v3 migration-diagnose before continuing through the current governed workflow."}
    print(json.dumps(result, ensure_ascii=False) if args.json else result["reason"])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
