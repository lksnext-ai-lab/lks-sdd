#!/usr/bin/env python3
"""Deliberately update the performance baseline from three clean all-suite runs."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

from quality_execution import PERFORMANCE_POLICY_PATH, QualityExecutionError


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QualityExecutionError(f"No se puede leer {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualityExecutionError(f"{path} no contiene un resultado JSON.")
    return value


def build_baseline(
    results: list[dict[str, Any]], *, reason: str, commit: str
) -> dict[str, Any]:
    if len(results) != 3:
        raise QualityExecutionError("La baseline requiere exactamente tres ejecuciones.")
    if len(reason.strip()) < 12:
        raise QualityExecutionError("--reason debe explicar el cambio de baseline.")
    fingerprints = [item.get("runner_fingerprint") for item in results]
    if not all(isinstance(item, dict) for item in fingerprints) or len(
        {json.dumps(item, sort_keys=True) for item in fingerprints}
    ) != 1:
        raise QualityExecutionError("Las tres ejecuciones deben usar el mismo runner.")
    signatures: list[list[tuple[str, str]]] = []
    durations: dict[str, list[float]] = {}
    required_suites = {"fast", "integration", "package", "profile", "candidate"}
    for result in results:
        if (
            result.get("selected_suite") != "all"
            or result.get("passed") is not True
            or result.get("termination") != "normal"
        ):
            raise QualityExecutionError(
                "Cada input debe ser una ejecución all pasada y terminada normalmente."
            )
        signatures.append(
            sorted(
                (str(item.get("id")), str(item.get("status")))
                for item in result.get("results", [])
                if isinstance(item, dict)
            )
        )
        comparisons = result.get("performance", {}).get("comparisons", [])
        observed = {
            str(item.get("suite")): float(item.get("actual_seconds"))
            for item in comparisons
            if isinstance(item, dict)
            and isinstance(item.get("actual_seconds"), (int, float))
        }
        if set(observed) != required_suites:
            raise QualityExecutionError(
                "Cada resultado debe contener tiempos de todos los tiers y candidate."
            )
        for suite, duration in observed.items():
            durations.setdefault(suite, []).append(duration)
    if any(signature != signatures[0] for signature in signatures[1:]):
        raise QualityExecutionError(
            "Las tres ejecuciones no tienen resultados funcionales idénticos."
        )
    return {
        "version": f"commit-{commit[:12]}",
        "reason": reason.strip(),
        "source_commit": commit,
        "sample_count": 3,
        "runner_fingerprint": fingerprints[0],
        "durations_seconds": {
            suite: round(statistics.median(values), 3)
            for suite, values in sorted(durations.items())
        },
    }


def _clean_head(root: Path) -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if status.returncode != 0 or status.stdout:
        raise QualityExecutionError(
            "La baseline solo puede actualizarse desde un checkout Git limpio."
        )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="ascii",
        check=False,
    )
    commit = head.stdout.strip().lower()
    if head.returncode != 0 or len(commit) != 40:
        raise QualityExecutionError("No se puede resolver HEAD para la baseline.")
    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", action="append", type=Path, required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        commit = _clean_head(PERFORMANCE_POLICY_PATH.parents[1])
        policy = _load(PERFORMANCE_POLICY_PATH)
        policy["baseline"] = build_baseline(
            [_load(path) for path in args.result], reason=args.reason, commit=commit
        )
        if args.apply:
            temporary = PERFORMANCE_POLICY_PATH.with_name(
                ".performance-policy.json.tmp"
            )
            temporary.write_text(
                json.dumps(policy, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            temporary.replace(PERFORMANCE_POLICY_PATH)
        print(
            json.dumps(
                {
                    "status": "applied" if args.apply else "preview",
                    "changed": args.apply,
                    "baseline": policy["baseline"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    except QualityExecutionError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
