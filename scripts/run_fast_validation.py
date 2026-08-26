#!/usr/bin/env python3
"""Run the high-signal development gate without release-only repetition."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _run(check_id: str, command: list[str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            cwd=PLUGIN_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
        output = f"{process.stdout}\n{process.stderr}".strip()
        return {
            "id": check_id,
            "status": "passed" if process.returncode == 0 else "failed",
            "exit_code": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "detail": output[-4000:] if process.returncode else "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "id": check_id,
            "status": "failed",
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "detail": f"timeout tras {exc.timeout}s",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--focus",
        choices=("jira-reporting", "migration", "contracts"),
        default="jira-reporting",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    common = [
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
    ]
    focused = {
        "jira-reporting": [
            (
                "jira-reporting-v15",
                [sys.executable, "-X", "utf8", "-m", "unittest", "tests.test_jira_reporting_v15"],
                240,
            ),
            (
                "tracking-current-schema",
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "unittest",
                    "tests.test_task_tracking_v14.TaskTrackingV14Tests.test_new_project_requires_mode_choice_without_external_dependency",
                ],
                120,
            ),
        ],
        "migration": [
            (
                "migration-12-through-15",
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "unittest",
                    "tests.test_migration_v11.Schema11MigrationTests.test_12_to_13_and_13_to_14_are_conservative_and_reversible",
                ],
                180,
            )
        ],
        "contracts": [],
    }[args.focus]
    results = [_run(*check) for check in [*common, *focused]]
    passed = all(item["status"] == "passed" for item in results)
    payload = {
        "schema_version": "1.0",
        "gate": "development-fast",
        "focus": args.focus,
        "release_evidence": False,
        "passed": passed,
        "duration_seconds": round(
            sum(item["duration_seconds"] for item in results), 3
        ),
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
            print(
                f"{item['status'].upper()}: {item['id']} "
                f"({item['duration_seconds']}s)"
            )
            if item["detail"]:
                print(item["detail"])
        print(payload["note"])
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
