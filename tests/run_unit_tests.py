#!/usr/bin/env python3
"""Run classified unittest suites with visible progress and JSON evidence."""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Iterable


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from quality_execution import (  # noqa: E402
    QualityExecutionError,
    load_performance_policy,
    load_suite_registry,
    modules_for_suite,
    performance_assessment,
    run_managed_command,
    runner_fingerprint,
)
from evidence_safety import sanitize  # noqa: E402


PROGRESS_STREAM = sys.stderr


def _flatten(suite: unittest.TestSuite) -> Iterable[unittest.case.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _discover_module(module: str) -> unittest.TestSuite:
    return unittest.defaultTestLoader.discover(
        str(TESTS_ROOT), pattern=f"{module}.py", top_level_dir=str(TESTS_ROOT)
    )


def _select_tests(suite: unittest.TestSuite, selectors: list[str]) -> unittest.TestSuite:
    tests = list(_flatten(suite))
    if not selectors:
        return unittest.TestSuite(tests)
    selected: list[unittest.case.TestCase] = []
    seen: set[str] = set()
    for selector in selectors:
        matches = [
            test
            for test in tests
            if test.id() == selector or test.id().endswith(f".{selector}")
        ]
        if len(matches) != 1:
            raise QualityExecutionError(
                f"El selector {selector!r} resolvió {len(matches)} tests; debe resolver uno."
            )
        if matches[0].id() not in seen:
            selected.append(matches[0])
            seen.add(matches[0].id())
    return unittest.TestSuite(selected)


class JsonTestResult(unittest.TextTestResult):
    """Collect one timed explicit outcome for every executed unittest."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.outcomes: list[dict[str, Any]] = []
        self._started: dict[str, float] = {}
        self._outcome_by_id: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _identity(test: unittest.case.TestCase) -> dict[str, str]:
        test_id = test.id()
        return {
            "id": test_id,
            "name": test_id.rsplit(".", 1)[-1],
            "module": test_id.split(".", 1)[0],
        }

    def startTest(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        self._started[test.id()] = time.monotonic()
        print(f"TEST {test.id()}", file=PROGRESS_STREAM, flush=True)
        super().startTest(test)

    def stopTest(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        outcome = self._outcome_by_id.get(test.id())
        if outcome is not None:
            outcome["duration_seconds"] = round(
                time.monotonic() - self._started.pop(test.id(), time.monotonic()), 3
            )
        super().stopTest(test)

    def _record(
        self,
        test: unittest.case.TestCase,
        status: str,
        reason: str | None = None,
    ) -> None:
        outcome: dict[str, Any] = {**self._identity(test), "status": status}
        if reason:
            outcome["reason"] = reason
            if status == "failed":
                print(f"FAIL {test.id()}: {reason}", file=PROGRESS_STREAM, flush=True)
        self.outcomes.append(outcome)
        self._outcome_by_id[test.id()] = outcome

    def addSuccess(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().addSuccess(test)
        self._record(test, "passed")

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:  # noqa: N802
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addFailure(self, test: unittest.case.TestCase, err: Any) -> None:  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failed", sanitize(self._exc_info_to_string(err, test).strip())[0])

    def addError(self, test: unittest.case.TestCase, err: Any) -> None:  # noqa: N802
        super().addError(test, err)
        self._record(test, "failed", sanitize(self._exc_info_to_string(err, test).strip())[0])

    def addExpectedFailure(  # noqa: N802
        self, test: unittest.case.TestCase, err: Any
    ) -> None:
        super().addExpectedFailure(test, err)
        self._record(test, "skipped", "expected-failure")

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().addUnexpectedSuccess(test)
        self._record(test, "failed", "unexpected-success")


def _counts(outcomes: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(outcomes),
        "passed": sum(item["status"] == "passed" for item in outcomes),
        "skipped": sum(item["status"] == "skipped" for item in outcomes),
        "failed": sum(item["status"] == "failed" for item in outcomes),
    }


def _run_worker(module: str, selectors: list[str]) -> tuple[int, dict[str, Any]]:
    started = time.monotonic()
    suite = _select_tests(_discover_module(module), selectors)
    runner = unittest.TextTestRunner(
        stream=io.StringIO(),
        verbosity=0,
        buffer=True,
        resultclass=JsonTestResult,
    )
    result = runner.run(suite)
    outcomes = sorted(result.outcomes, key=lambda item: item["id"])
    payload = {
        "schema_version": "1.0",
        "module": module,
        "passed": result.wasSuccessful(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "counts": _counts(outcomes),
        "results": outcomes,
    }
    return (0 if result.wasSuccessful() else 1), payload


def _failure_results(module: str, ids: list[str], reason: str) -> list[dict[str, Any]]:
    if not ids:
        ids = [f"{module}.__module_execution__"]
    return [
        {
            "id": test_id,
            "name": test_id.rsplit(".", 1)[-1],
            "module": module,
            "status": "failed",
            "reason": reason,
            "duration_seconds": 0.0,
        }
        for test_id in ids
    ]


def _run_parent(
    selected_suite: str,
    selected_modules: list[str],
    selectors: list[str],
) -> tuple[int, dict[str, Any]]:
    registry = load_suite_registry()
    configured = modules_for_suite(selected_suite, registry)
    if selected_modules:
        unknown = sorted(set(selected_modules) - {module for module, _, _ in configured})
        if unknown:
            raise QualityExecutionError(
                f"Los módulos no pertenecen a la suite {selected_suite}: {unknown}"
            )
        selected_set = set(selected_modules)
        configured = [item for item in configured if item[0] in selected_set]

    selector_ids_by_module: dict[str, list[str]] = {}
    if selectors:
        all_tests = [
            (module, test)
            for module, _, _ in configured
            for test in _flatten(_discover_module(module))
        ]
        for selector in selectors:
            matches = [
                (module, test.id())
                for module, test in all_tests
                if test.id() == selector or test.id().endswith(f".{selector}")
            ]
            if len(matches) != 1:
                raise QualityExecutionError(
                    f"El selector {selector!r} resolvió {len(matches)} tests; debe resolver uno."
                )
            module, test_id = matches[0]
            selector_ids_by_module.setdefault(module, []).append(test_id)
        configured = [item for item in configured if item[0] in selector_ids_by_module]

    started = time.monotonic()
    all_results: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    termination = "normal"

    def execute_module(
        index: int, module: str, tier: str, timeout: int
    ) -> tuple[int, dict[str, Any], list[dict[str, Any]], bool]:
        exact_selectors = selector_ids_by_module.get(module, [])
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(Path(__file__).resolve()),
            "--module-worker",
            module,
        ]
        for selector in exact_selectors:
            command.extend(["--test", selector])
        expected_ids = exact_selectors or [test.id() for test in _flatten(_discover_module(module))]
        managed = run_managed_command(
            command,
            cwd=PLUGIN_ROOT,
            timeout=timeout,
            label=f"{tier}:{module}",
            stream_stderr=True,
        )
        parsed: dict[str, Any] | None = None
        if managed.stdout.strip():
            try:
                value = json.loads(managed.stdout)
                parsed = value if isinstance(value, dict) else None
            except json.JSONDecodeError:
                parsed = None
        reason = None
        if managed.timed_out:
            reason = f"module-timeout-{timeout}s"
            termination = "timeout"
        elif managed.returncode != 0:
            reason = f"module-exit-{managed.returncode}"
        elif parsed is None:
            reason = "module-invalid-json"
        module_results = (
            parsed.get("results", [])
            if not managed.timed_out and isinstance(parsed, dict) and isinstance(parsed.get("results"), list)
            else _failure_results(module, expected_ids, reason or "module-failed")
        )
        module_payload = {
            "module": module,
            "tier": tier,
            "status": "passed"
            if reason is None and parsed.get("passed") is True
            else "failed",
            "duration_seconds": managed.duration_seconds,
            "timeout_seconds": timeout,
            "termination": managed.termination,
            "process_cleanup": managed.process_cleanup,
            **({"reason": reason} if reason else {}),
        }
        return index, module_payload, module_results, managed.timed_out

    if selected_suite == "all":
        configured_workers = max(
            int(config["max_workers"])
            for config in registry["tiers"].values()
        )
    else:
        configured_workers = int(
            registry["tiers"][selected_suite]["max_workers"]
        )
    workers = min(configured_workers, max(1, len(configured)))
    completed_modules: list[
        tuple[int, dict[str, Any], list[dict[str, Any]], bool]
    ] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(execute_module, index, module, tier, timeout)
            for index, (module, tier, timeout) in enumerate(configured)
        ]
        for future in concurrent.futures.as_completed(futures):
            completed_modules.append(future.result())
    for _index, module_payload, module_results, timed_out in sorted(
        completed_modules, key=lambda item: item[0]
    ):
        all_results.extend(module_results)
        modules.append(module_payload)
        if timed_out:
            termination = "timeout"
    all_results.sort(key=lambda item: item["id"])
    counts = _counts(all_results)
    duration = round(time.monotonic() - started, 3)
    fingerprint = runner_fingerprint()
    performance = None
    if not selected_modules and not selectors:
        actual: dict[str, float] = {}
        if selected_suite != "all":
            actual[selected_suite] = duration
        else:
            for tier in sorted({item["tier"] for item in modules}):
                actual[tier] = round(
                    max(
                        float(item["duration_seconds"])
                        for item in modules
                        if item["tier"] == tier
                    ),
                    3,
                )
        if selected_suite == "all":
            actual["candidate"] = duration
        performance = performance_assessment(
            actual, load_performance_policy(), fingerprint
        )
    passed = counts["failed"] == 0 and all(item["status"] == "passed" for item in modules) and (
        performance is None or performance["status"] == "passed"
    )
    if counts["failed"] == 0 and performance and performance["status"] == "failed":
        termination = "budget-exceeded"
    payload = {
        "schema_version": "1.0",
        "suite": "LKS-SDD unittest",
        "selected_suite": selected_suite,
        "passed": passed,
        "duration_seconds": duration,
        "runner_fingerprint": fingerprint,
        "command": [Path(sys.argv[0]).name, *sys.argv[1:]],
        "termination": termination,
        "counts": counts,
        "modules": modules,
        **({"performance": performance} if performance is not None else {}),
        "slowest_tests": sorted(
            all_results,
            key=lambda item: (-float(item.get("duration_seconds", 0)), item["id"]),
        )[:10],
        "results": all_results,
    }
    return (0 if passed else 1), payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(target)


def main() -> int:
    global PROGRESS_STREAM
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    PROGRESS_STREAM = sys.stderr
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        choices=("fast", "integration", "package", "profile", "all"),
        default="all",
    )
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--test", action="append", default=[])
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--module-worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.module_worker:
            code, payload = _run_worker(args.module_worker, args.test)
        else:
            code, payload = _run_parent(args.suite, args.module, args.test)
    except QualityExecutionError as exc:
        payload = {
            "schema_version": "1.0",
            "suite": "LKS-SDD unittest",
            "selected_suite": args.suite,
            "passed": False,
            "termination": "configuration-error",
            "counts": {"total": 0, "passed": 0, "skipped": 0, "failed": 0},
            "results": [],
            "error": str(exc),
        }
        code = 2
    if args.json_out and not args.module_worker:
        _write_json(args.json_out, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
