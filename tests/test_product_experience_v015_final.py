"""Final deterministic shard for the LKS-SDD 0.15 product experience."""

from __future__ import annotations

import unittest

from test_product_experience_v015 import (
    PRODUCT_EXPERIENCE_SECOND_BOUNDARY,
    ProductExperienceV015Tests,
)


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del standard_tests, pattern
    names = loader.getTestCaseNames(ProductExperienceV015Tests)
    return unittest.TestSuite(
        ProductExperienceV015Tests(name)
        for name in names[PRODUCT_EXPERIENCE_SECOND_BOUNDARY:]
    )
