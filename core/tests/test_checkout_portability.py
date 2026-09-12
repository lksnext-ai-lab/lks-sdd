from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_plugin_contract import CANONICAL_HASHES  # noqa: E402


class CheckoutPortabilityTests(unittest.TestCase):
    def _git(
        self,
        *arguments: str,
        cwd: Path,
        env: dict[str, str],
        text: bool = True,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        process = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
            errors="replace" if text else None,
            check=False,
            timeout=60,
        )
        stderr = process.stderr if text else process.stderr.decode("utf-8", "replace")
        self.assertEqual(process.returncode, 0, stderr)
        return process

    def test_hash_locked_files_remain_lf_with_autocrlf_checkout(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="lks-eol-"
        ) as directory:
            temporary = Path(directory).resolve()
            source = temporary / "source"
            checkout = temporary / "checkout"
            isolated_config = temporary / "isolated-global.gitconfig"
            isolated_config.write_bytes(b"[core]\n\tautocrlf = true\n")

            git_env = {
                name: value
                for name, value in os.environ.items()
                if not name.upper().startswith("GIT_")
            }
            git_env["GIT_CONFIG_NOSYSTEM"] = "1"
            git_env["GIT_CONFIG_GLOBAL"] = str(isolated_config)

            fixture_manifest = json.loads(
                (PLUGIN_ROOT / "quality" / "fixture-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            portable_files = [
                *(Path("specs/canonical") / name for name in CANONICAL_HASHES),
                Path("quality/fixture-manifest.json"),
                *(
                    Path(fixture_manifest["root"]) / entry["path"]
                    for entry in fixture_manifest["fixtures"]
                ),
            ]
            declared_fixture_hashes = {
                Path(fixture_manifest["root"]) / entry["path"]: entry["sha256"]
                for entry in fixture_manifest["fixtures"]
            }
            # The harness validates the complete checkout independently. This
            # fixture verifies the autocrlf property only for exact files whose
            # bytes and hashes are contractual, so unrelated source files cannot
            # turn a byte-preservation test into a full-repository integration run.
            fixture_paths = [Path(".gitattributes"), *portable_files]
            self.assertEqual(len(fixture_paths), len(set(fixture_paths)))

            source.mkdir()
            for relative in fixture_paths:
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                origin = PLUGIN_ROOT / relative
                self.assertTrue(origin.is_file(), relative.as_posix())
                destination = source / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, destination)

            self._git("init", "--quiet", cwd=source, env=git_env)
            self._git("config", "core.autocrlf", "false", cwd=source, env=git_env)
            self._git("config", "user.name", "LKS-SDD Test", cwd=source, env=git_env)
            self._git(
                "config",
                "user.email",
                "lks-sdd-test@example.invalid",
                cwd=source,
                env=git_env,
            )
            self._git("add", "--all", cwd=source, env=git_env)
            self._git(
                "commit", "--quiet", "-m", "portable snapshot", cwd=source, env=git_env
            )

            self._git(
                "clone",
                "--quiet",
                "--local",
                str(source),
                str(checkout),
                cwd=temporary,
                env=git_env,
            )
            effective_autocrlf = self._git(
                "config", "--get", "core.autocrlf", cwd=checkout, env=git_env
            )
            self.assertEqual(effective_autocrlf.stdout.strip(), "true")

            for relative in fixture_paths:
                with self.subTest(path=relative.as_posix()):
                    expected_bytes = (PLUGIN_ROOT / relative).read_bytes()
                    checkout_bytes = (checkout / relative).read_bytes()
                    self.assertIn(b"\n", checkout_bytes)
                    self.assertNotIn(b"\r\n", checkout_bytes)
                    self.assertEqual(checkout_bytes, expected_bytes)

                    digest = hashlib.sha256(checkout_bytes).hexdigest()
                    if relative.parent == Path("specs/canonical"):
                        self.assertEqual(digest.upper(), CANONICAL_HASHES[relative.name])
                    if relative in declared_fixture_hashes:
                        self.assertEqual(digest, declared_fixture_hashes[relative])

            self._git("diff", "--check", cwd=checkout, env=git_env)


if __name__ == "__main__":
    unittest.main()
