"""Third deterministic execution shard for the LKS-SDD tracking contract."""

from __future__ import annotations

import unittest

from test_task_tracking_v14 import (
    TaskTrackingV14Tests,
)
from test_task_tracking_v14_middle import TASK_TRACKING_SECOND_BOUNDARY


TASK_TRACKING_THIRD_BOUNDARY = 24


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del standard_tests, pattern
    names = loader.getTestCaseNames(TaskTrackingV14Tests)
    return unittest.TestSuite(
        TaskTrackingV14Tests(name)
        for name in names[
            TASK_TRACKING_SECOND_BOUNDARY:TASK_TRACKING_THIRD_BOUNDARY
        ]
    )
