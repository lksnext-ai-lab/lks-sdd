"""Middle deterministic shard for the LKS-SDD task-tracking contract."""

from __future__ import annotations

import unittest

from test_task_tracking_v14 import TaskTrackingV14Tests
from test_task_tracking_v14_initial_tail import TASK_TRACKING_INITIAL_TAIL_BOUNDARY


TASK_TRACKING_SECOND_BOUNDARY = 16


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
            TASK_TRACKING_INITIAL_TAIL_BOUNDARY:TASK_TRACKING_SECOND_BOUNDARY
        ]
    )
