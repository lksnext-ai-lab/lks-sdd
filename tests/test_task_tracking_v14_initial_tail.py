"""Second half of the initial LKS-SDD task-tracking shard."""

from __future__ import annotations

import unittest

from test_task_tracking_v14 import (
    TASK_TRACKING_SHARD_BOUNDARY,
    TaskTrackingV14Tests,
)


TASK_TRACKING_INITIAL_TAIL_BOUNDARY = 8


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
            TASK_TRACKING_SHARD_BOUNDARY:TASK_TRACKING_INITIAL_TAIL_BOUNDARY
        ]
    )
