#!/usr/bin/env python3
"""Run the reproducible M0-M1 invariant evals."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from eval_support import (
    run_alternative_stack,
    run_help,
    run_insufficient_information,
    run_management_comprehension,
    run_new_project,
    run_scoped_blocker,
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    runners = [
        run_new_project,
        run_insufficient_information,
        run_alternative_stack,
        run_scoped_blocker,
        run_help,
        run_management_comprehension,
    ]
    results = []
    for runner in runners:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-eval-") as directory:
            results.append(runner(Path(directory)))
    payload = {
        "suite": "LKS-SDD deterministic invariants and product comprehension",
        "passed": all(result["passed"] for result in results),
        "results": results,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
