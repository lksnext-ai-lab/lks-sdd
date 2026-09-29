"""Actual v2 runtime bytes, explicit cutover and the portable v3 command boundary."""
import io
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from build_dual_distribution import collect_development
from build_candidate_package import _package_integrity_bytes
from dual_distribution import artifacts
from path_utils import filesystem_root
import test_v3_migration as migration_fixtures
from v3_migration import preview
from v3_storage import apply
from runtime_doctor import check


class DistributionTests(migration_fixtures.MigrationTests):
    # Do not inherit the source-format scenarios a second time.
    test_conversion_preserves_identity_originals_and_code = None
    test_unknown_method_is_diagnosed_without_writes = None
    test_interruption_and_later_edit_are_protected = None
    test_published_native_initializers_preserve_their_formats = None
    test_open_plan_reuses_exact_content_and_requires_current_execution_authority = None

    def test_pinned_runtime_cutover_and_cli_preserve_host_contract(self):
        source = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=zip", "v2.3.1"], capture_output=True, check=True)
        with zipfile.ZipFile(io.BytesIO(source.stdout)) as archive:
            old_core = {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}
        old_core["package-integrity.json"] = _package_integrity_bytes(list(old_core.items()), "2.3.1", "published-v2.3.1-fixture")
        spec = importlib.util.spec_from_file_location("fixture_installer", ROOT/"distribution/install.py")
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory(prefix="v3-cutover-") as temp:
            def setup(core, name):
                bundle = Path(temp)/name; bundle.mkdir()
                packages = artifacts(core, "fixture", "regression")
                data = next(v for k, v in packages.items() if k.startswith("lks-sdd-setup-"))
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for i in archive.infolist():
                        target = installer.safe(bundle, i.filename)
                        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(i))
                return bundle
            old_bundle = setup(old_core, "old")
            prepared = installer.plan(old_bundle, self.root, "copilot")
            installer.apply(prepared, prepared["preview_hash"])
            self.assertEqual("valid", check(self.root)["status"])
            new_bundle = setup(collect_development(ROOT), "new")
            with self.assertRaisesRegex(ValueError, "explicit"):
                installer.plan(new_bundle, self.root, "copilot")
            packet = preview(self.root, "Responsable", "individual-brief", self.controls,
                             "Valido conjuntamente el cambio de contrato y runtime", target="main", runtime_bundle=new_bundle)
            apply(self.root, packet, packet["preview"]["preview_hash"])
            self.assertEqual("valid", check(self.root)["status"])
            lock = json.loads((self.root/".lks-sdd/distribution-lock.json").read_bytes())
            self.assertEqual("3.0", lock["project_schema"])
            cli = self.root/lock["runtime"]/"scripts/lks_sdd.py"
            result = subprocess.run([sys.executable, "-B", str(cli), "v3", "validate", str(self.root)], capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("valid", json.loads(result.stdout)["status"])
            for host in ("AGENTS.md", ".github/copilot-instructions.md"):
                self.assertIn("3.0", (self.root/host).read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
