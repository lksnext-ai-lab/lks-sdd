from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import validate_release_artifacts  # noqa: E402


VERSION = "2.0.3"
SOURCE_COMMIT = "b" * 40


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _candidate(root: Path) -> Path:
    candidate = root / "candidate"
    candidate.mkdir()
    assets = {
        f"lks-sdd-copilot-plugin-v{VERSION}.zip": b"copilot",
        f"lks-sdd-plugin-v{VERSION}.zip": b"plugin",
        f"lks-sdd-marketplace-v{VERSION}.zip": b"marketplace",
    }
    for name, content in assets.items():
        (candidate / name).write_bytes(content)
    manifest = {
        "plugin_version": VERSION,
        "source_commit": SOURCE_COMMIT,
        "artifacts": [
            {"path": name, "sha256": _sha256(content), "size": len(content)}
            for name, content in assets.items()
        ],
    }
    (candidate / "release-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return candidate


class ReleasePackageValidationTests(unittest.TestCase):
    @patch.object(validate_release_artifacts, "_validate_bundle")
    @patch.object(validate_release_artifacts.validate_copilot_package, "validate")
    def test_report_binds_all_existing_package_checks(
        self, _validate_copilot, validate_bundle
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = _candidate(Path(temporary))
            report = validate_release_artifacts.validate_candidate(candidate)

            validate_release_artifacts.validate_report(candidate, report)

        self.assertEqual("passed", report["status"])
        self.assertEqual(
            [("plugin",), ("marketplace",)],
            [call.args[1:] for call in validate_bundle.call_args_list],
        )

    @patch.object(validate_release_artifacts, "_validate_bundle")
    @patch.object(validate_release_artifacts.validate_copilot_package, "validate")
    def test_changed_asset_blocks_validation(self, _validate_copilot, _validate_bundle) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = _candidate(Path(temporary))
            (candidate / f"lks-sdd-plugin-v{VERSION}.zip").write_bytes(b"altered")

            with self.assertRaisesRegex(
                validate_release_artifacts.ReleasePackageValidationError,
                "no coincide",
            ):
                validate_release_artifacts.validate_candidate(candidate)

    def test_report_with_wrong_manifest_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = _candidate(Path(temporary))
            report = {
                "schema_version": "release-package-validation-1.0",
                "status": "passed",
                "plugin_version": VERSION,
                "source_commit": SOURCE_COMMIT,
                "release_manifest_sha256": "0" * 64,
                "checks": [
                    {"id": "copilot-package", "status": "passed"},
                    {"id": "plugin-bundle", "status": "passed"},
                    {"id": "marketplace-bundle", "status": "passed"},
                ],
            }

            with self.assertRaisesRegex(
                validate_release_artifacts.ReleasePackageValidationError,
                "no está vinculada",
            ):
                validate_release_artifacts.validate_report(candidate, report)


if __name__ == "__main__":
    unittest.main()
