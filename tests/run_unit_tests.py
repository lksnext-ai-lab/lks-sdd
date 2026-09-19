#!/usr/bin/env python3
"""Run selected LKS-SDD unittest cases and emit compact JSON evidence."""

from __future__ import annotations

import argparse
import json
import sys
import time
import unittest
from pathlib import Path


TESTS_ROOT = Path(__file__).resolve().parent


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _discover(module: str | None) -> list[unittest.case.TestCase]:
    pattern = f"{module}.py" if module else "test_*.py"
    suite = unittest.defaultTestLoader.discover(
        str(TESTS_ROOT), pattern=pattern, top_level_dir=str(TESTS_ROOT)
    )
    return list(_flatten(suite))


def _select(
    tests: list[unittest.case.TestCase], selectors: list[str]
) -> list[unittest.case.TestCase]:
    if not selectors:
        return tests
    selected: list[unittest.case.TestCase] = []
    seen: set[str] = set()
    for selector in selectors:
        matches = [
            test
            for test in tests
            if test.id() == selector or test.id().endswith(f".{selector}")
        ]
        if len(matches) != 1:
            raise ValueError(
                f"El selector {selector!r} resolvió {len(matches)} tests; debe resolver uno."
            )
        if matches[0].id() not in seen:
            selected.append(matches[0])
            seen.add(matches[0].id())
    return selected


class _Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes: list[dict[str, str]] = []

    def _record(self, test: unittest.case.TestCase, status: str) -> None:
        self.outcomes.append({"id": test.id(), "status": status})

    def addSuccess(self, test):  # noqa: N802
        super().addSuccess(test)
        self._record(test, "passed")

    def addSkip(self, test, reason):  # noqa: N802
        super().addSkip(test, reason)
        self._record(test, "skipped")

    def addFailure(self, test, err):  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failed")

    def addError(self, test, err):  # noqa: N802
        super().addError(test, err)
        self._record(test, "failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--test", action="append", default=[])
    args = parser.parse_args()
    started = time.monotonic()
    try:
        tests = [
            test
            for module in (args.module or [None])
            for test in _discover(module)
        ]
        selected = _select(tests, args.test)
    except ValueError as exc:
        print(
            json.dumps(
                {"passed": False, "results": [], "error": str(exc)},
                ensure_ascii=False,
            )
        )
        return 2
    runner = unittest.TextTestRunner(
        stream=sys.stderr, verbosity=1, resultclass=_Result, buffer=True
    )
    result = runner.run(unittest.TestSuite(selected))
    outcomes = sorted(result.outcomes, key=lambda item: item["id"])
    counts = {
        "total": len(outcomes),
        "passed": sum(item["status"] == "passed" for item in outcomes),
        "skipped": sum(item["status"] == "skipped" for item in outcomes),
        "failed": sum(item["status"] == "failed" for item in outcomes),
    }
    print(
        json.dumps(
            {
                "passed": result.wasSuccessful(),
                "duration_seconds": round(time.monotonic() - started, 3),
                "counts": counts,
                "results": outcomes,
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
