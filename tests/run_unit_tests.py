#!/usr/bin/env python3
"""Run the unittest suite and emit machine-readable per-test outcomes."""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from typing import Any


class JsonTestResult(unittest.TextTestResult):
    """Collect one explicit outcome for every discovered unittest."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.outcomes: list[dict[str, Any]] = []

    @staticmethod
    def _identity(test: unittest.case.TestCase) -> dict[str, str]:
        test_id = test.id()
        return {"id": test_id, "name": test_id.rsplit(".", 1)[-1]}

    def _record(
        self,
        test: unittest.case.TestCase,
        status: str,
        reason: str | None = None,
    ) -> None:
        outcome: dict[str, Any] = {**self._identity(test), "status": status}
        if reason:
            outcome["reason"] = reason
        self.outcomes.append(outcome)

    def addSuccess(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().addSuccess(test)
        self._record(test, "passed")

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:  # noqa: N802
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addFailure(self, test: unittest.case.TestCase, err: Any) -> None:  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test).splitlines()[-1])

    def addError(self, test: unittest.case.TestCase, err: Any) -> None:  # noqa: N802
        super().addError(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test).splitlines()[-1])

    def addExpectedFailure(  # noqa: N802
        self, test: unittest.case.TestCase, err: Any
    ) -> None:
        super().addExpectedFailure(test, err)
        self._record(test, "skipped", "expected-failure")

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().addUnexpectedSuccess(test)
        self._record(test, "failed", "unexpected-success")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tests_root = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(
        str(tests_root), pattern="test_*.py", top_level_dir=str(tests_root)
    )
    runner = unittest.TextTestRunner(
        stream=io.StringIO(),
        verbosity=0,
        buffer=True,
        resultclass=JsonTestResult,
    )
    result = runner.run(suite)
    outcomes = sorted(result.outcomes, key=lambda item: item["id"])
    counts = {
        "total": len(outcomes),
        "passed": sum(item["status"] == "passed" for item in outcomes),
        "skipped": sum(item["status"] == "skipped" for item in outcomes),
        "failed": sum(item["status"] == "failed" for item in outcomes),
    }
    payload = {
        "suite": "LKS-SDD unittest",
        "passed": result.wasSuccessful(),
        "counts": counts,
        "results": outcomes,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
