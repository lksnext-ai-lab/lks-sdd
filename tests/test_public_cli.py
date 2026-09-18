import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "lks_sdd.py"


class PublicCliTests(unittest.TestCase):
    def _run(self, *arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_top_level_help_lists_public_commands_from_consumer_directory(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-cli-") as temporary:
            result = self._run("--help", cwd=Path(temporary))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("assess-readiness", result.stdout)
        self.assertIn("validate-project", result.stdout)

    def test_subcommand_help_is_forwarded_from_consumer_directory(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-cli-") as temporary:
            result = self._run("assess-readiness", "--help", cwd=Path(temporary))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("project_root", result.stdout)
        self.assertIn("--increment", result.stdout)

    def test_every_documented_subcommand_resolves_from_consumer_directory(self):
        expected = {
            "query",
            "help",
            "define",
            "adopt-inspect",
            "adopt-validate",
            "adopt-materialize",
            "assess-readiness",
            "implement",
            "verify",
            "validate-project",
            "validate-spec",
            "traceability",
            "client-view",
            "status",
            "work",
            "doctor",
        }
        with tempfile.TemporaryDirectory(prefix="lks-sdd-cli-") as temporary:
            consumer = Path(temporary)
            for command in sorted(expected):
                with self.subTest(command=command):
                    result = self._run(command, "--help", cwd=consumer)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("usage:", result.stdout.casefold())


if __name__ == "__main__":
    unittest.main()
