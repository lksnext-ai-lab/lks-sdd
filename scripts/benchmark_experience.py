#!/usr/bin/env python3
"""Measure the v0.15 public fast path and compare its operation inventory."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PLUGIN_ROOT / "scripts/lks_sdd.py"
TESTS_ROOT = PLUGIN_ROOT / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from eval_support import authorize_implementation, materialize_ready_project  # noqa: E402
from experience_fixture import create_representative_fixture  # noqa: E402


BASELINE_OPERATIONS = [
    "help/context",
    "validate-project",
    "validate-spec",
    "assess-readiness",
    "planning-assess",
    "authorization-preview/apply",
    "implementation-preview/apply",
    "task-transition",
    "continuity-checkpoint",
    "verification-plan/execute/record",
]
CANDIDATE_OPERATIONS = ["status", "work-start", "work-verify", "work-complete"]


def _run_cli(arguments: list[str]) -> tuple[float, int, dict[str, Any]]:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(ENTRYPOINT), *arguments],
        cwd=PLUGIN_ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"La CLI pública no devolvió JSON: {completed.stdout or completed.stderr}"
        ) from exc
    return elapsed_ms, completed.returncode, payload


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="strict")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("--iterations debe ser mayor que cero")

    with tempfile.TemporaryDirectory(prefix="lks-sdd-v015-benchmark-") as temporary:
        base = Path(temporary)
        representative = create_representative_fixture(base / "representative")
        status_timings: list[float] = []
        status_payload: dict[str, Any] = {}
        for _ in range(args.iterations):
            elapsed, code, status_payload = _run_cli(
                ["status", str(representative), "--view", "management", "--json"]
            )
            if code != 0:
                raise RuntimeError(f"status falló con código {code}: {status_payload}")
            status_timings.append(elapsed)

        transition_root = base / "transition"
        transition_root.mkdir()
        materialize_ready_project(transition_root, "v015-benchmark-transition")
        authorize_implementation(transition_root)
        transition_ms, transition_code, transition_payload = _run_cli(
            [
                "work", "start", str(transition_root),
                "--increment", "INC-001", "--task", "TASK-001",
                "--actor", "benchmark-authority", "--json",
            ]
        )

    management_bytes = len(
        json.dumps(status_payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    reduction = round(
        (1 - len(CANDIDATE_OPERATIONS) / len(BASELINE_OPERATIONS)) * 100, 1
    )
    status_passed = max(status_timings) < 5000 and management_bytes < 8192
    transition_passed = (
        transition_code == 0
        and transition_payload.get("status") == "started"
        and transition_payload.get("administrative_operations") == 1
        and transition_ms < 8000
    )
    result = {
        "schema_version": "1.0",
        "fixture": {
            "tasks": 13,
            "planning_relations": 420,
            "bindings": 3,
            "checkpoints": 3,
            "evidence_documents": 2,
            "active_and_resolved_problems": True,
            "jira_configured": True,
        },
        "status_management": {
            "measurement": "public-cli-subprocess",
            "iterations": args.iterations,
            "median_ms": round(statistics.median(status_timings), 3),
            "max_ms": round(max(status_timings), 3),
            "json_bytes": management_bytes,
            "target_ms": 2000,
            "limit_ms": 5000,
            "passed": status_passed,
        },
        "local_composed_transition": {
            "measurement": "public-cli-subprocess",
            "operation": "work start",
            "elapsed_ms": round(transition_ms, 3),
            "target_ms": 3000,
            "limit_ms": 8000,
            "exit_code": transition_code,
            "administrative_operations": transition_payload.get(
                "administrative_operations"
            ),
            "human_confirmations_required": transition_payload.get(
                "human_confirmations_required"
            ),
            "passed": transition_passed,
        },
        "administrative_cycle": {
            "0.14.2": {
                "source_commit": "a303370c2555236c1778f276e187a4bb3c1926f5",
                "operations": BASELINE_OPERATIONS,
                "commands": len(BASELINE_OPERATIONS),
                "basis": "public command contract reconstructed from the exact 0.14.2 source commit",
            },
            "0.15.0": {
                "operations": CANDIDATE_OPERATIONS,
                "commands": len(CANDIDATE_OPERATIONS),
                "basis": "public composed commands; status and work-start measured in this run",
            },
            "command_reduction_percent": reduction,
            "required_reduction_percent": 50.0,
            "passed": reduction >= 50.0,
        },
        "passed": status_passed and transition_passed and reduction >= 50.0,
        "limitations": [
            "Los gates técnicos y peers externos quedan fuera del overhead administrativo.",
            "El inventario 0.14.2 se deriva de su CLI pública exacta; no se modelan tiempos retrospectivos.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
