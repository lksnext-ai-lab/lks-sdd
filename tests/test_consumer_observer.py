"""Regression coverage for consumer observer error normalization."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from consumer_observer import ObserverError, validate_schema


class ConsumerObserverTests(unittest.TestCase):
    def test_schema_validation_error_is_normalized(self):
        with self.assertRaisesRegex(ObserverError, "Observer schema validation failed"):
            validate_schema({}, "consumer-observation.schema.json")


if __name__ == "__main__":
    unittest.main()
