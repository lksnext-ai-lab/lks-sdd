from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import verify_draft_promotion  # noqa: E402


VERSION = "2.0.3"
SOURCE_COMMIT = "a" * 40


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_fixture(
    root: Path,
    *,
    altered_checksum: bool = False,
    changelog_text: str | None = None,
) -> tuple[Path, Path]:
    evidence = root / "evidence"
    candidate = evidence / "candidate"
    candidate.mkdir(parents=True)
    changelog = root / "CHANGELOG.md"
    changelog.write_text(
        changelog_text
        or (
            "# Changelog\n\n"
            f"## {VERSION} — 2026-09-19\n\n"
            "- Promoción protegida desde una sección acreditada del changelog.\n\n"
            "## 2.0.2 — 2026-09-18\n\n"
            "- Referencia histórica.\n"
        ),
        encoding="utf-8",
    )
    gate = {
        "plugin_version": VERSION,
        "channel": "stable",
        "source": {"commit": SOURCE_COMMIT, "tree_state": "clean"},
        "gate": {"status": "passed", "blockers": []},
    }
    gate_bytes = (json.dumps(gate, indent=2) + "\n").encode("utf-8")
    (evidence / "release-gate.json").write_bytes(gate_bytes)
    copilot_name = f"lks-sdd-copilot-plugin-v{VERSION}.zip"
    copilot_bytes = b"copilot-zip"
    marketplace_name = f"lks-sdd-marketplace-v{VERSION}.zip"
    marketplace_bytes = b"marketplace-zip"
    quality_name = "quality-report.json"
    (candidate / copilot_name).write_bytes(copilot_bytes)
    (candidate / marketplace_name).write_bytes(marketplace_bytes)
    (candidate / quality_name).write_bytes(gate_bytes)
    artifacts = [
        {"path": copilot_name, "sha256": _sha256(copilot_bytes), "size": len(copilot_bytes)},
        {
            "path": marketplace_name,
            "sha256": _sha256(marketplace_bytes),
            "size": len(marketplace_bytes),
        },
        {"path": quality_name, "sha256": _sha256(gate_bytes), "size": len(gate_bytes)},
    ]
    manifest = {
        "plugin_version": VERSION,
        "source_commit": SOURCE_COMMIT,
        "quality": {
            "gate": "passed",
            "channel": "stable",
            "report_sha256": _sha256(gate_bytes),
        },
        "artifacts": artifacts,
        "source_files": [
            {
                "path": "CHANGELOG.md",
                "sha256": _sha256(changelog.read_bytes()),
                "size": len(changelog.read_bytes()),
            }
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    (candidate / "release-manifest.json").write_bytes(manifest_bytes)
    checksums = {
        **{artifact["path"]: artifact["sha256"] for artifact in artifacts},
        "release-manifest.json": _sha256(manifest_bytes),
    }
    if altered_checksum:
        checksums[copilot_name] = "0" * 64
    (candidate / "SHA256SUMS").write_text(
        "".join(f"{digest}  {path}\n" for path, digest in checksums.items()),
        encoding="utf-8",
    )
    return evidence, changelog


class DraftPromotionTests(unittest.TestCase):
    @patch.object(verify_draft_promotion.validate_copilot_package, "validate")
    def test_plan_binds_every_manifest_asset_to_the_tag(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(Path(temporary))
            plan = verify_draft_promotion.build_plan(
                evidence,
                f"v{VERSION}",
                SOURCE_COMMIT,
                changelog,
            )
            release_section = verify_draft_promotion.release_notes.extract(
                changelog.read_bytes(), VERSION
            )

        self.assertEqual(f"v{VERSION}", plan["tag"])
        self.assertEqual(SOURCE_COMMIT, plan["source_commit"])
        self.assertEqual(
            [
                f"lks-sdd-copilot-plugin-v{VERSION}.zip",
                f"lks-sdd-marketplace-v{VERSION}.zip",
                "quality-report.json",
                "release-manifest.json",
                "SHA256SUMS",
            ],
            [asset["path"] for asset in plan["assets"]],
        )
        self.assertEqual(
            {
                "source_path": "CHANGELOG.md",
                "sha256": _sha256(release_section),
                "size": len(release_section),
            },
            plan["release_notes"],
        )

    @patch.object(verify_draft_promotion.validate_copilot_package, "validate")
    def test_checksum_mismatch_blocks_promotion(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(
                Path(temporary), altered_checksum=True
            )
            with self.assertRaisesRegex(
                verify_draft_promotion.DraftPromotionError, "SHA256SUMS"
            ):
                verify_draft_promotion.build_plan(
                    evidence,
                    f"v{VERSION}",
                    SOURCE_COMMIT,
                    changelog,
                )

    @patch.object(verify_draft_promotion.validate_copilot_package, "validate")
    def test_tag_mismatch_blocks_promotion(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(Path(temporary))
            with self.assertRaisesRegex(
                verify_draft_promotion.DraftPromotionError, "etiqueta"
            ):
                verify_draft_promotion.build_plan(
                    evidence,
                    "v2.0.4",
                    SOURCE_COMMIT,
                    changelog,
                )

    @patch.object(
        verify_draft_promotion.validate_copilot_package,
        "validate",
        side_effect=zipfile.BadZipFile("archivo corrupto"),
    )
    def test_corrupted_copilot_zip_blocks_promotion(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(Path(temporary))
            with self.assertRaisesRegex(
                verify_draft_promotion.DraftPromotionError, "ZIP Copilot"
            ):
                verify_draft_promotion.build_plan(
                    evidence,
                    f"v{VERSION}",
                    SOURCE_COMMIT,
                    changelog,
                )

    @patch.object(verify_draft_promotion.validate_copilot_package, "validate")
    def test_missing_changelog_section_blocks_promotion(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(
                Path(temporary),
                changelog_text="# Changelog\n\n## 2.0.2\n\n- Historial.\n",
            )
            with self.assertRaisesRegex(
                verify_draft_promotion.DraftPromotionError, "no existe"
            ):
                verify_draft_promotion.build_plan(
                    evidence,
                    f"v{VERSION}",
                    SOURCE_COMMIT,
                    changelog,
                )

    @patch.object(verify_draft_promotion.validate_copilot_package, "validate")
    def test_unaccredited_changelog_blocks_promotion(self, _validate) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog = _write_fixture(Path(temporary))
            changelog.write_text(
                changelog.read_text(encoding="utf-8") + "\n- Alteración no acreditada.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                verify_draft_promotion.DraftPromotionError, "CHANGELOG.md"
            ):
                verify_draft_promotion.build_plan(
                    evidence,
                    f"v{VERSION}",
                    SOURCE_COMMIT,
                    changelog,
                )

    def test_writes_exact_changelog_section_for_draft_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, changelog = _write_fixture(root)
            output = root / "release-notes.md"

            verify_draft_promotion._write_release_notes(output, changelog, VERSION)

            self.assertEqual(
                verify_draft_promotion.release_notes.extract(
                    changelog.read_bytes(), VERSION
                ),
                output.read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
