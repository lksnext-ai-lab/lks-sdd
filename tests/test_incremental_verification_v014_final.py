"""Final deterministic shard for incremental verification regressions."""

from __future__ import annotations

import unittest

from test_incremental_verification_v014 import (
    INCREMENTAL_VERIFICATION_THIRD_BOUNDARY,
    incremental_verification_tests,
)


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del standard_tests, pattern
    return unittest.TestSuite(
        incremental_verification_tests(loader)[
            INCREMENTAL_VERIFICATION_THIRD_BOUNDARY:
        ]
    )
