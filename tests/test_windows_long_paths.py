"""Windows extended-length path regressions for the packaged runtime."""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_candidate_package import _package_integrity_bytes
from build_dual_distribution import collect_development
from dual_distribution import project_files
from path_utils import filesystem_root


def _tree_snapshot(root: Path) -> dict[str, str]:
    result = {}
    for path in root.rglob("*"):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _write_tree(root: Path, files: dict[str, bytes]) -> None:
    for relative, data in files.items():
        target = filesystem_root(root / relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _runtime_core() -> dict[str, bytes]:
    return collect_development(ROOT)


class WindowsLongPathTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows extended-length path regression")
    def test_long_plugin_and_migration_paths_match_short_paths(self):
        container = Path(tempfile.mkdtemp(prefix="lks-long-path-"))
        self.addCleanup(lambda: shutil.rmtree(filesystem_root(container), ignore_errors=True))
        long_container = filesystem_root(
            container
            / ("segment-" + "a" * 38)
            / ("segment-" + "b" * 38)
            / ("segment-" + "c" * 38)
            / ("segment-" + "d" * 38)
            / ("segment-" + "e" * 38)
        )
        long_container.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(long_container, ignore_errors=True))

        long_plugin = long_container / "plugin"
        ignore = shutil.ignore_patterns(".git", "site", "__pycache__", "*.pyc")
        shutil.copytree(ROOT, long_plugin, ignore=ignore)
        source_relative = Path(
            "schemas/technology-declaration-2.0.schema.json"
        )
        short_plugin = ROOT
        if len(os.fspath(short_plugin / source_relative)) >= 260:
            short_plugin = container / "short-plugin"
            shutil.copytree(ROOT, short_plugin, ignore=ignore)
        self.assertLess(len(os.fspath(short_plugin / source_relative)), 260)
        self.assertGreater(len(os.fspath(long_plugin / source_relative)), 260)

        def command(
            plugin: Path, *args: str, cwd: Path | None = None
        ) -> subprocess.CompletedProcess[str]:
            script = (
                plugin / args[0]
                if args[0].startswith(("scripts/", "skills/"))
                else plugin / "scripts" / args[0]
            )
            return subprocess.run(
                [sys.executable, "-B", "-X", "utf8", str(script), *args[1:]],
                cwd=cwd or ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=240,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            contract_short, contract_long = pool.map(
                lambda item: command(item[0], "validate_plugin_contract.py", str(item[0])),
                ((short_plugin, short_plugin), (long_plugin, long_plugin)),
            )
        self.assertEqual(contract_short.returncode, 0, contract_short.stdout + contract_short.stderr)
        self.assertEqual(contract_long.returncode, 0, contract_long.stdout + contract_long.stderr)



        core = _runtime_core()
        core["scripts/path_utils.py"] = (ROOT / "scripts/path_utils.py").read_bytes()
        core["scripts/import_bootstrap.py"] = (ROOT / "scripts/import_bootstrap.py").read_bytes()
        version = json.loads(core[".codex-plugin/plugin.json"])["version"]
        core["package-integrity.json"] = _package_integrity_bytes(
            list(core.items()), version, "windows-long-path-regression"
        )
        long_runtime = long_plugin / "runtime-v2"
        _write_tree(long_runtime, core)
        short_runtime = container / "short-runtime-v2"
        _write_tree(short_runtime, core)

        def integrity(runtime: Path) -> tuple[int, list[str], list[str]]:
            manifest = json.loads((runtime / "package-integrity.json").read_bytes())
            missing, mismatched = [], []
            for item in manifest["files"]:
                candidate = filesystem_root(runtime / item["path"])
                if not candidate.is_file():
                    missing.append(item["path"])
                elif hashlib.sha256(candidate.read_bytes()).hexdigest() != item["sha256"]:
                    mismatched.append(item["path"])
            return len(manifest["files"]), missing, mismatched

        expected_integrity_count = None
        with ThreadPoolExecutor(max_workers=2) as pool:
            integrity_results = list(pool.map(integrity, (short_runtime, long_runtime)))
        for count, missing, mismatched in integrity_results:
            if expected_integrity_count is None:
                expected_integrity_count = count
            self.assertEqual(count, expected_integrity_count)
            self.assertGreater(count, 0)
            self.assertEqual(missing, [])
            self.assertEqual(mismatched, [])

        long_project = long_container / "project"
        source_core = dict(core)
        source_core["distribution/dual.json"] = source_core["distribution/dual.json"].replace(
            b'"project_schema": "2.0"', b'"project_schema": "1.5"'
        )
        source_core.pop("package-integrity.json", None)
        source_core["package-integrity.json"] = _package_integrity_bytes(
            list(source_core.items()), version, "windows-long-path-legacy-source"
        )
        source_files = project_files(source_core, "windows-long-path-legacy-source", "regression")
        _write_tree(long_project, source_files)
        short_project = container / "short-project"
        _write_tree(short_project, source_files)
        def initialize(item):
            plugin, project = item
            return command(
                plugin,
                "skills/lks-sdd-define/scripts/init_project.py",
                str(project),
                "--project-id",
                "windows-long-path-regression",
                "--date",
                "2026-09-18",
                "--json",
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            initialized_results = list(pool.map(initialize, ((short_plugin, short_project), (long_plugin, long_project))))
        for initialized in initialized_results:
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)

        def migration(plugin: Path, project: Path, runtime: Path, action: str) -> dict:
            result = command(
                plugin,
                "scripts/lks_sdd.py",
                "v2",
                action,
                str(project),
                "--target-runtime",
                str(runtime),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)

        short_before = _tree_snapshot(short_project)
        long_before = _tree_snapshot(long_project)
        with ThreadPoolExecutor(max_workers=2) as pool:
            short_diagnose, long_diagnose = pool.map(
                lambda item: migration(*item, "migration-diagnose"),
                ((short_plugin, short_project, short_runtime), (long_plugin, long_project, long_runtime)),
            )
        self.assertEqual(short_diagnose, long_diagnose)
        with ThreadPoolExecutor(max_workers=2) as pool:
            short_preview, long_preview = pool.map(
                lambda item: migration(*item, "migration-preview"),
                ((short_plugin, short_project, short_runtime), (long_plugin, long_project, long_runtime)),
            )
        self.assertEqual(short_preview["preview_hash"], long_preview["preview_hash"])
        self.assertEqual(short_preview["writes"], long_preview["writes"])
        self.assertEqual(short_before, _tree_snapshot(short_project))
        self.assertEqual(long_before, _tree_snapshot(long_project))
        self.assertFalse(any("MAX_PATH" in str(value) for value in long_preview.values()))
