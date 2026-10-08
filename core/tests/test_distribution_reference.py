from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
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
                        "version": "2.0.3",
                        "source": {
                            "source": "github",
                            "repo": "lksnext-ai-lab/lks-sdd",
                            "ref": "copilot-v2.0.3",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _native_package(path: Path) -> dict[str, str]:
    manifest = json.dumps({"name": "lks-sdd", "version": "2.0.3"}).encode()
    skill = b"---\nname: lks-sdd-help\n---\n"
    attributes = b"* text=auto eol=lf\n"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("lks-sdd/.gitattributes", attributes)
        package.writestr("lks-sdd/plugin.json", manifest)
        package.writestr("lks-sdd/skills/lks-sdd-help/SKILL.md", skill)
    return {
        ".gitattributes": hashlib.sha256(attributes).hexdigest(),
        "plugin.json": hashlib.sha256(manifest).hexdigest(),
        "skills/lks-sdd-help/SKILL.md": hashlib.sha256(skill).hexdigest(),
    }


class DistributionReferenceTests(unittest.TestCase):
    def test_isolated_git_archive_matches_native_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            native_package = root / "copilot.zip"
            expected = _native_package(native_package)
            repository = root / "native-repository"
            repository.mkdir()
            with zipfile.ZipFile(native_package) as package:
                for entry in package.infolist():
                    if entry.is_dir():
                        continue
                    relative = entry.filename.removeprefix("lks-sdd/")
                    destination = repository / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(package.read(entry))
            commands = (
                ["git", "init", "--quiet", str(repository)],
                ["git", "-C", str(repository), "add", "--all"],
                ["git", "-C", str(repository), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "native package"],
                ["git", "-C", str(repository), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "tag", "-a", "copilot-v2.0.3", "-m", "native package"],
            )
            for command in commands:
                subprocess.run(command, check=True, capture_output=True)
            actual = validate_distribution_reference._native_git_inventory(
                "lksnext-ai-lab/lks-sdd", "copilot-v2.0.3", remote_override=str(repository)
            )
        self.assertEqual(expected, actual)

    def test_annotated_native_tag_is_compared_with_exact_package_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            native_package = Path(temporary) / "copilot.zip"
            inventory = _native_package(native_package)
            remote_output = (
                f"{'c' * 40}\trefs/tags/copilot-v2.0.3\n"
                f"{'b' * 40}\trefs/tags/copilot-v2.0.3^{{}}\n"
            )
            with patch.object(validate_distribution_reference, "_remote_refs", return_value=remote_output), patch.object(
                validate_distribution_reference, "_native_git_inventory", return_value=inventory
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    native_package,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("passed", report["status"])
        self.assertEqual(
            [{"kind": "tag", "commit": "b" * 40}], report["resolved_targets"]
        )
        self.assertEqual(3, report["tagged_files"])

    def test_missing_native_tag_is_reported_without_a_success_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            native_package = Path(temporary) / "copilot.zip"
            _native_package(native_package)
            with patch.object(
                validate_distribution_reference,
                "_remote_refs",
                return_value="",
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    native_package,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("failed", report["status"])
        self.assertIn("no existe", report["reason"])

    def test_mismatched_native_bytes_fail_even_when_tag_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            native_package = Path(temporary) / "copilot.zip"
            _native_package(native_package)
            remote_output = f"{'b' * 40}\trefs/tags/copilot-v2.0.3\n"
            with patch.object(validate_distribution_reference, "_remote_refs", return_value=remote_output), patch.object(
                validate_distribution_reference, "_native_git_inventory", return_value={"plugin.json": "wrong"}
            ):
                report = validate_distribution_reference.build_report(
                    marketplace, SOURCE_COMMIT, native_package, observed_at="2026-09-19T07:00:00Z"
                )
        self.assertEqual("failed", report["status"])
        self.assertIn("byte a byte", report["reason"])

    def test_tag_and_branch_with_the_same_name_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marketplace = Path(temporary) / "marketplace.json"
            _marketplace(marketplace)
            native_package = Path(temporary) / "copilot.zip"
            _native_package(native_package)
            remote_output = (
                f"{SOURCE_COMMIT}\trefs/tags/copilot-v2.0.3\n"
                f"{SOURCE_COMMIT}\trefs/heads/copilot-v2.0.3\n"
            )
            with patch.object(
                validate_distribution_reference,
                "_remote_refs",
                return_value=remote_output,
            ):
                report = validate_distribution_reference.build_report(
                    marketplace,
                    SOURCE_COMMIT,
                    native_package,
                    observed_at="2026-09-19T07:00:00Z",
                )

        self.assertEqual("failed", report["status"])
        self.assertIn("ambigua", report["reason"])

    def test_package_rejects_files_outside_plugin_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            native_package = Path(temporary) / "copilot.zip"
            _native_package(native_package)
            with zipfile.ZipFile(native_package, "a") as package:
                package.writestr("outside.txt", b"unexpected")
            with self.assertRaises(validate_distribution_reference.DistributionReferenceError):
                validate_distribution_reference._native_package_inventory(native_package, "2.0.3")


if __name__ == "__main__":
    unittest.main()
