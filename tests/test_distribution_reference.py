from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import validate_distribution_reference  # noqa: E402


SOURCE_COMMIT = "a" * 40


def _marketplace(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "name": "lks-sdd",
                        "source": {
                            "source": "github",
                            "repo": "lksnext-ai-lab/lks-sdd",
                            "ref": "v2.0.3",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class DistributionReferenceTests(unittest.TestCase):
    def test_annotated_tag_is_compared_using_its_peeled_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            remote_output = (
                f"{'b' * 40}\trefs/tags/v2.0.3\n"
                f"{SOURCE_COMMIT}\trefs/tags/v2.0.3^{{}}\n"
            )
            with patch.object(
                validate_distribution_reference,
                "_remote_refs",
                return_value=remote_output,
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("passed", report["status"])
        self.assertEqual(
            [{"kind": "tag", "commit": SOURCE_COMMIT}], report["resolved_targets"]
        )

    def test_mismatched_reference_is_reported_without_a_success_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            with patch.object(
                validate_distribution_reference,
                "_remote_refs",
                return_value=f"{'b' * 40}\trefs/heads/v2.0.3\n",
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("failed", report["status"])
        self.assertIn("no apunta", report["reason"])

    def test_tag_and_branch_with_the_same_name_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            remote_output = (
                f"{SOURCE_COMMIT}\trefs/tags/v2.0.3\n"
                f"{SOURCE_COMMIT}\trefs/heads/v2.0.3\n"
            )
            with patch.object(
                validate_distribution_reference,
                "_remote_refs",
                return_value=remote_output,
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("failed", report["status"])
        self.assertIn("ambigua", report["reason"])


if __name__ == "__main__":
    unittest.main()
