from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import release_readiness  # noqa: E402


SOURCE_COMMIT = "a" * 40


class ReleaseReadinessTests(unittest.TestCase):
    def _ready_git(self, arguments: list[str]) -> str:
        if arguments == ["rev-parse", "HEAD"]:
            return SOURCE_COMMIT
        if arguments == ["status", "--porcelain", "--untracked-files=all"]:
            return ""
        if arguments[:3] == ["ls-remote", "--heads", "--tags"]:
            return f"{SOURCE_COMMIT}\trefs/heads/main"
        self.fail(f"Git inesperado: {arguments}")

    @patch.object(release_readiness, "_approval_check", return_value=None)
    @patch.object(release_readiness, "_contract_check", return_value=None)
    @patch.object(
        release_readiness.validate_plugin_contract,
        "validate_copilot_catalog",
        return_value=[],
    )
    @patch.object(release_readiness.run_release_gate, "_plugin_version", return_value="2.0.3")
    def test_stable_release_is_ready_when_all_preconditions_pass(
        self, _version, _catalog, _contract, _approval
    ) -> None:
        with patch.object(release_readiness, "_git", side_effect=self._ready_git):
            report = release_readiness.build_report("stable")

        self.assertEqual("ready", report["readiness"])
        self.assertEqual([], report["blockers"])
        self.assertEqual(SOURCE_COMMIT, report["source_commit"])

    @patch.object(release_readiness, "_approval_check", return_value=None)
    @patch.object(release_readiness, "_contract_check", return_value=None)
    @patch.object(
        release_readiness.validate_plugin_contract,
        "validate_copilot_catalog",
        return_value=[],
    )
    @patch.object(release_readiness.run_release_gate, "_plugin_version", return_value="2.0.3")
    def test_dirty_worktree_blocks_release(
        self, _version, _catalog, _contract, _approval
    ) -> None:
        def dirty_git(arguments: list[str]) -> str:
            if arguments == ["status", "--porcelain", "--untracked-files=all"]:
                return "?? generated.txt"
            return self._ready_git(arguments)

        with patch.object(release_readiness, "_git", side_effect=dirty_git):
            report = release_readiness.build_report("stable")

        self.assertEqual("blocked", report["readiness"])
        self.assertIn("worktree", report["blockers"])

    @patch.object(release_readiness, "_approval_check", return_value=None)
    @patch.object(release_readiness, "_contract_check", return_value=None)
    @patch.object(
        release_readiness.validate_plugin_contract,
        "validate_copilot_catalog",
        return_value=[],
    )
    @patch.object(release_readiness.run_release_gate, "_plugin_version", return_value="2.0.3")
    def test_existing_remote_tag_blocks_release(
        self, _version, _catalog, _contract, _approval
    ) -> None:
        def tagged_git(arguments: list[str]) -> str:
            if arguments[:3] == ["ls-remote", "--heads", "--tags"]:
                return (
                    f"{SOURCE_COMMIT}\trefs/heads/main\n"
                    f"{SOURCE_COMMIT}\trefs/tags/v2.0.3"
                )
            return self._ready_git(arguments)

        with patch.object(release_readiness, "_git", side_effect=tagged_git):
            report = release_readiness.build_report("stable")

        self.assertEqual("blocked", report["readiness"])
        self.assertIn("release-tag", report["blockers"])

    @patch.object(release_readiness, "_contract_check", return_value=None)
    @patch.object(
        release_readiness.validate_plugin_contract,
        "validate_copilot_catalog",
        return_value=[],
    )
    @patch.object(release_readiness.run_release_gate, "_plugin_version", return_value="2.0.3")
    def test_candidate_channel_does_not_require_stable_approval(
        self, _version, _catalog, _contract
    ) -> None:
        with patch.object(release_readiness, "_git", side_effect=self._ready_git):
            report = release_readiness.build_report("candidate")

        approval = next(check for check in report["checks"] if check["id"] == "approval")
        self.assertEqual("not-applicable", approval["status"])
        self.assertEqual("ready", report["readiness"])

    def test_catalog_requires_the_native_copilot_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = root / ".github" / "plugin" / "marketplace.json"
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(
                json.dumps(
                    {
                        "plugins": [
                            {
                                "name": "lks-sdd",
                                "version": "2.0.3",
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

            errors = release_readiness.validate_plugin_contract.validate_copilot_catalog(
                root, "2.0.3"
            )

        self.assertEqual(1, len(errors))
        self.assertIn("etiqueta nativa", errors[0])

    @patch.object(
        release_readiness.run_release_gate,
        "_plugin_version",
        side_effect=release_readiness.run_release_gate.ReleaseGateError("Manifest inválido."),
    )
    def test_context_error_keeps_a_machine_readable_blocker(self, _version) -> None:
        report = release_readiness.build_report("stable")

        self.assertEqual("blocked", report["readiness"])
        self.assertEqual(["source-context"], report["blockers"])
        self.assertEqual("error", report["checks"][0]["status"])

    def test_report_output_cannot_write_inside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = root / "release-readiness.json"
            with patch.object(release_readiness, "PLUGIN_ROOT", root):
                with self.assertRaisesRegex(
                    release_readiness.ReleaseReadinessError, "fuera del repositorio"
                ):
                    release_readiness._write_report(output, {"readiness": "ready"})

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
