#!/usr/bin/env python3
"""Run the high-signal development gate without release-only repetition."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from quality_execution import (
    PLUGIN_ROOT,
    QualityExecutionError,
    impacted_modules,
    load_impact_map,
    run_managed_command,
)


def _run(check_id: str, command: list[str], timeout: int) -> dict[str, Any]:
    process = run_managed_command(
        command,
        cwd=PLUGIN_ROOT,
        timeout=timeout,
        label=check_id,
    )
    output = f"{process.stdout}\n{process.stderr}".strip()
    passed = process.returncode == 0 and not process.timed_out
    return {
        "id": check_id,
        "status": "passed" if passed else "failed",
        "exit_code": process.returncode,
        "duration_seconds": process.duration_seconds,
        "timeout_seconds": timeout,
        "termination": process.termination,
        "process_cleanup": process.process_cleanup,
        "detail": output[-4000:] if not passed else "",
    }


def _git_changed_paths(reference: str) -> list[str]:
    process = subprocess.run(
        ["git", "diff", "--name-only", "-z", reference, "--"],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise QualityExecutionError(
            f"No se pueden resolver cambios desde {reference!r}: {detail}"
        )
    return [
        item.decode("utf-8", errors="strict")
        for item in process.stdout.split(b"\0")
        if item
    ]


def _focused_modules(focus: str) -> list[str]:
    return {
        "jira-reporting": [
            "test_jira_reporting_v15",
            "test_task_tracking_v14",
            "test_task_tracking_v14_middle",
            "test_task_tracking_v14_extended",
            "test_task_tracking_v14_final",
        ],
        "compatibility": ["test_contract_engine", "test_definition_experience", "test_product_experience_v015"],
        "contracts": [],
    }[focus]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--focus",
        choices=("jira-reporting", "compatibility", "contracts"),
        default=None,
    )
    parser.add_argument("--changed-from")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.focus and args.changed_from:
        print("ERROR: use --focus o --changed-from, no ambos.", file=sys.stderr)
        return 2
    try:
        selection: dict[str, Any]
        if args.changed_from:
            selection = impacted_modules(
                _git_changed_paths(args.changed_from), load_impact_map()
            )
            modules = selection["modules"]
            mode = "changed-from"
            selector = args.changed_from
        else:
            focus = args.focus or "jira-reporting"
            modules = _focused_modules(focus)
            selection = {"modules": modules, "fallback_applied": False, "unmatched_paths": []}
            mode = "focus"
            selector = focus
    except QualityExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    checks: list[tuple[str, list[str], int]] = [
        (
            "plugin-contract",
            [sys.executable, "-X", "utf8", "scripts/validate_plugin_contract.py", "."],
            120,
        ),
        (
            "reference-profile-structure",
            [
                sys.executable,
                "-X",
                "utf8",
                "scripts/validate_reference_profile.py",
                "--all",
                "--allow-unvalidated",
            ],
            120,
        ),
        (
            "unit-fast",
            [sys.executable, "-X", "utf8", "tests/run_unit_tests.py", "--suite", "fast"],
            120,
        ),
    ]
    if modules:
        command = [
            sys.executable,
            "-X",
            "utf8",
            "tests/run_unit_tests.py",
            "--suite",
            "all",
        ]
        for module in modules:
            command.extend(["--module", module])
        checks.append(("unit-impacted", command, 480))
    results = [_run(*check) for check in checks]
    passed = all(item["status"] == "passed" for item in results)
    payload = {
        "schema_version": "1.1",
        "gate": "development-fast",
        "selection_mode": mode,
        "selection": selector,
        "impact": selection,
        "release_evidence": False,
        "passed": passed,
        "duration_seconds": round(sum(item["duration_seconds"] for item in results), 3),
        "results": results,
        "note": (
            "Este gate acelera el feedback local; una release sigue exigiendo el "
            "harness integral desde un checkout limpio."
        ),
    }
    if args.as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("PASSED" if passed else "FAILED")
        for item in results:
            print(f"{item['status'].upper()}: {item['id']} ({item['duration_seconds']}s)")
            if item["detail"]:
                print(item["detail"])
        print(payload["note"])
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
