from __future__ import annotations

import importlib.util
import io
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dual_distribution import artifacts, digest, project_files, copilot_plugin_files, SKILLS, filesystem_root
from runtime_doctor import check

spec = importlib.util.spec_from_file_location("dual_installer", ROOT / "distribution/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def core_fixture(version="1.1.0-rc.1"):
    core = {".codex-plugin/plugin.json": json.dumps({"name": "lks-sdd", "version": version}).encode()}
    core["distribution/dual.json"] = json.dumps({"project_schema": "2.0" if version.startswith("2.") else "1.5"}).encode()
    for path in ("distribution/host-copilot.md", "distribution/install.py", "distribution/install.ps1",
                 "distribution/marketplace.template.json", "docs/INSTALLATION.md",
                 "docs/LEARNING-GUIDE.md", "docs/COPILOT-PILOT.md"):
        core[path] = (ROOT / path).read_bytes()
    for suffix in SKILLS:
        core[f"skills/lks-sdd-{suffix}/SKILL.md"] = (ROOT / f"skills/lks-sdd-{suffix}/SKILL.md").read_bytes()
    core["scripts/example.py"] = b"print('shared core')\n"
    return core


class DualDistributionTests(unittest.TestCase):
    def test_team_catalog_pins_generated_version_in_same_repository(self):
        version = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())["version"]
        catalog = json.loads((ROOT / ".github/plugin/marketplace.json").read_text())
        self.assertEqual(catalog["name"], "lks-sdd-copilot")
        self.assertEqual(len(catalog["plugins"]), 1)
        plugin = catalog["plugins"][0]
        self.assertEqual(plugin["name"], "lks-sdd")
        self.assertEqual(plugin["version"], version)
        self.assertEqual(plugin["source"], {
            "source": "github", "repo": "lksnext-ai-lab/lks-sdd", "ref": f"copilot-v{version}"})

    def test_native_archive_validator_rejects_corruption_and_duplicates(self):
        from dual_distribution import zip_bytes
        from validate_copilot_package import validate
        files = {f"lks-sdd/{p}": data for p, data in copilot_plugin_files(
            self.core, "synthetic", "development-not-certified").items()}
        self.assertEqual(validate(zip_bytes(files))["status"], "valid")
        changed = {**files, "lks-sdd/setup/install.py": b"damaged"}
        with self.assertRaisesRegex(ValueError, "integrity"):
            validate(zip_bytes(changed))
        changed = {**files, "lks-sdd/skills/unexpected/SKILL.md": b"extra"}
        with self.assertRaisesRegex(ValueError, "six"):
            validate(zip_bytes(changed))

    def native_setup(self, core=None):
        files = copilot_plugin_files(core or self.core, "synthetic-test", "development-not-certified")
        bundle = self.root / "native" / "setup"
        for name, data in files.items():
            path = self.root / "native" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return files, bundle

    def test_native_plugin_layout_and_project_bootstrap(self):
        files, bundle = self.native_setup()
        manifest = json.loads(files["plugin.json"])
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(manifest["name"], "lks-sdd")
        self.assertEqual(len([p for p in files if p.startswith("skills/") and p.endswith("/SKILL.md")]), 6)
        for name, data in self.core.items():
            self.assertEqual(files["core/" + name], data)
        self.assertFalse(any(p.startswith(("hooks/", "com.github.copilot/agents/")) or p == "mcp.json" for p in files))
        self.assertEqual(list(self.consumer.iterdir()), [])
        preview = installer.plan(bundle, self.consumer, "copilot")
        self.assertEqual(list(self.consumer.iterdir()), [])
        installer.apply(preview, preview["preview_hash"])
        lock = json.loads((self.consumer / ".lks-sdd/distribution-lock.json").read_text())
        self.assertEqual(lock["entrypoints"], "plugin")
        self.assertFalse((self.consumer / ".github/skills").exists())
        self.assertEqual(check(self.consumer)["status"], "valid")
        duplicate = self.consumer / ".github/skills/lks-sdd-help/SKILL.md"
        duplicate.parent.mkdir(parents=True)
        duplicate.write_bytes(b"duplicate")
        self.assertEqual(check(self.consumer)["status"], "blocked")
        self.assertTrue(any("Duplicate" in error for error in check(self.consumer)["errors"]))

    def test_migrate_to_native_and_back_without_duplicate_skills(self):
        self.install()
        _, bundle = self.native_setup()
        preview = installer.plan(bundle, self.consumer, "copilot")
        installer.apply(preview, preview["preview_hash"])
        self.assertEqual(list((self.consumer / ".github/skills").rglob("SKILL.md")), [])
        self.assertEqual(check(self.consumer)["status"], "valid")
        self.install()
        self.assertEqual(len(list((self.consumer / ".github/skills").rglob("SKILL.md"))), 6)
        self.assertEqual(check(self.consumer)["status"], "valid")

    def test_personal_plugin_update_does_not_change_pinned_project(self):
        _, bundle = self.native_setup()
        preview = installer.plan(bundle, self.consumer, "copilot")
        installer.apply(preview, preview["preview_hash"])
        before = (self.consumer / ".lks-sdd/distribution-lock.json").read_bytes()
        self.native_setup(core_fixture("1.1.0-rc.2"))
        self.assertEqual((self.consumer / ".lks-sdd/distribution-lock.json").read_bytes(), before)
        self.assertEqual(check(self.consumer)["version"], "1.1.0-rc.1")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-dual-test-")
        self.root = filesystem_root(Path(self.temporary.name))
        # Cleanup must use extended paths too, not just the installation itself.
        self.temporary.name = str(self.root)
        self.bundle = self.root / "setup"
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        self.core = core_fixture()
        self.unpack(self.core)

    def tearDown(self):
        self.temporary.cleanup()

    def unpack(self, core):
        built = artifacts(core, "synthetic-test", "development-not-certified")
        setup = next(data for name, data in built.items() if name.startswith("lks-sdd-setup"))
        with zipfile.ZipFile(io.BytesIO(setup)) as archive:
            archive.extractall(self.bundle)
        return built

    def install(self, remove=False, host="copilot", destination=None):
        target = destination or self.consumer
        preview = installer.plan(self.bundle, target, host, remove)
        installer.apply(preview, preview["preview_hash"])
        return preview

    def test_deterministic_archives_and_equal_runtime(self):
        a = artifacts(self.core, "source", "development-not-certified")
        b = artifacts(dict(reversed(list(self.core.items()))), "source", "development-not-certified")
        self.assertEqual(a, b)
        files = project_files(self.core, "source", "development-not-certified")
        lock = json.loads(files[".lks-sdd/distribution-lock.json"])
        for name, data in self.core.items():
            self.assertEqual(files[lock["runtime"] + "/" + name], data)
        self.assertEqual(len([p for p in files if p.startswith(".github/skills/") and p.endswith("/SKILL.md")]), 6)

    def test_preview_no_write_and_exact_authorization(self):
        preview = installer.plan(self.bundle, self.consumer, "copilot")
        self.assertEqual(list(self.consumer.iterdir()), [])
        with self.assertRaisesRegex(ValueError, "hash"):
            installer.apply(preview, "wrong")
        self.assertEqual(list(self.consumer.iterdir()), [])

    def test_install_doctor_repeat_and_shared_clone(self):
        self.install()
        self.assertEqual(check(self.consumer)["status"], "valid")
        self.assertEqual(self.install()["changes"], [])
        import shutil
        clone = self.root / "clone with spaces"
        shutil.copytree(self.consumer, clone)
        self.assertEqual(check(clone)["status"], "valid")
        lock_text = (clone / ".lks-sdd/distribution-lock.json").read_text()
        self.assertNotIn(str(self.consumer), lock_text)

    def test_preserve_instructions_and_uninstall_keeps_consumer_data(self):
        (self.consumer / "AGENTS.md").write_text("# Team rules\n", encoding="utf-8")
        self.install()
        path = self.consumer / "AGENTS.md"
        path.write_text(path.read_text() + "\n# Later human rule\n", encoding="utf-8")
        assets = self.consumer / "docs/lks-sdd/03-solution/ui-prototypes"
        assets.mkdir(parents=True)
        (assets / "approved.png").write_bytes(b"consumer-owned")
        self.assertEqual(check(self.consumer)["status"], "valid")
        self.install(remove=True)
        self.assertIn("# Team rules", path.read_text())
        self.assertIn("# Later human rule", path.read_text())
        self.assertNotIn(installer.BEGIN, path.read_text())
        self.assertEqual((assets / "approved.png").read_bytes(), b"consumer-owned")

    def test_unowned_collision_fails_without_writes(self):
        path = self.consumer / ".github/skills/lks-sdd-help/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"my custom skill")
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install()
        self.assertEqual(path.read_bytes(), b"my custom skill")
        self.assertFalse((self.consumer / ".lks-sdd/installation.json").exists())

    def test_modified_owned_file_blocks_update_and_remove(self):
        self.install()
        path = self.consumer / ".github/skills/lks-sdd-help/SKILL.md"
        path.write_bytes(b"human edit")
        self.assertEqual(check(self.consumer)["status"], "blocked")
        for remove in (False, True):
            with self.assertRaisesRegex(ValueError, "modified"):
                self.install(remove=remove)
        self.assertEqual(path.read_bytes(), b"human edit")

    def test_update_removes_only_old_owned_runtime(self):
        self.install()
        old = json.loads((self.consumer / ".lks-sdd/distribution-lock.json").read_text())["runtime"]
        new_core = core_fixture("1.1.0-rc.2")
        self.unpack(new_core)
        self.install()
        self.assertEqual(check(self.consumer)["version"], "1.1.0-rc.2")
        self.assertFalse((self.consumer / old / "scripts/example.py").exists())

    def test_damaged_payload_rejected_before_writes(self):
        path = self.bundle / "payload/copilot.zip"
        path.write_bytes(b"damaged")
        with self.assertRaisesRegex(ValueError, "Damaged"):
            self.install()
        self.assertEqual(list(self.consumer.iterdir()), [])

    def test_concurrent_edit_after_preview_rejected(self):
        preview = installer.plan(self.bundle, self.consumer, "copilot")
        (self.consumer / "AGENTS.md").write_bytes(b"new rules")
        with self.assertRaisesRegex(ValueError, "Concurrent"):
            installer.apply(preview, preview["preview_hash"])
        self.assertEqual((self.consumer / "AGENTS.md").read_bytes(), b"new rules")

    def test_interrupted_install_can_recover(self):
        preview = installer.plan(self.bundle, self.consumer, "copilot")
        original = installer.atomic_write
        counter = [0]
        def interrupted(path, content):
            counter[0] += 1
            if counter[0] == 4:
                raise OSError("synthetic crash")
            return original(path, content)
        with mock.patch.object(installer, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "synthetic"):
                installer.apply(preview, preview["preview_hash"])
        self.assertTrue((self.consumer / installer.JOURNAL).exists())
        installer.recover(self.consumer)
        self.assertFalse((self.consumer / ".lks-sdd/distribution-lock.json").exists())
        self.install()
        self.assertEqual(check(self.consumer)["status"], "valid")

    def test_codex_marketplace_is_prepared_not_activated(self):
        destination = self.root / "codex source"
        self.install(host="codex", destination=destination)
        self.assertTrue((destination / ".agents/plugins/marketplace.json").is_file())
        self.assertTrue((destination / "plugins/lks-sdd/.codex-plugin/plugin.json").is_file())

    def test_unsafe_paths_rejected(self):
        for name in ("../outside", "/absolute", "C:/absolute", "x\\y", "x/../y"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                installer.safe(self.consumer, name)

    def test_pending_visual_handoff_blocks_runtime_upgrade(self):
        self.install()
        pending = self.consumer / ".lks-sdd/handoffs/visual/VH-synthetic/request.json"
        pending.parent.mkdir(parents=True)
        pending.write_text("{}")
        self.unpack(core_fixture("1.1.0-rc.2"))
        with self.assertRaisesRegex(ValueError, "pending visual"):
            self.install()

    def test_git_checkout_with_autocrlf_preserves_shared_lock(self):
        import subprocess
        self.install()
        for arguments in (["init", "--quiet"], ["config", "core.autocrlf", "true"], ["add", "--all"]):
            result = subprocess.run(["git", *arguments], cwd=self.consumer, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        clone = self.root / "git-copy"
        # checkout-index tests a real Git round trip without creating any commit.
        prefix = str(clone).replace("\\", "/").removeprefix("//?/") + "/"
        result = subprocess.run(["git", "checkout-index", "--all", "--prefix=" + prefix],
                                cwd=self.consumer, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(check(clone)["status"], "valid", check(clone))

    def test_native_plugin_git_roundtrip_preserves_setup(self):
        import subprocess
        _, bundle = self.native_setup()
        plugin = bundle.parent
        for arguments in (["init", "--quiet"], ["config", "core.autocrlf", "true"], ["add", "--all"]):
            result = subprocess.run(["git", *arguments], cwd=plugin, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        clone = self.root / "native-git-copy"
        prefix = str(clone).replace("\\", "/").removeprefix("//?/") + "/"
        result = subprocess.run(["git", "checkout-index", "--all", "--prefix=" + prefix],
                                cwd=plugin, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = installer.plan(clone / "setup", self.consumer, "copilot")
        installer.apply(preview, preview["preview_hash"])
        self.assertEqual(check(self.consumer)["status"], "valid", check(self.consumer))

    def test_release_dual_manifest_matches_actual_archives(self):
        from build_candidate_package import build
        from dual_distribution import json_bytes
        import build_candidate_package as builder
        report = {"gate": {"status": "passed"}, "channel": "candidate", "comparison": {"baseline_commit": "synthetic"}}
        core = {**self.core, "distribution/dual.json": b'{"schema_version":"1.0","project_schema":"1.5"}'}
        output = self.root / "release"
        source = self.root / "source"
        source.mkdir()
        with mock.patch.object(builder, "_validate_source_checkout", return_value=source), \
             mock.patch.object(builder, "collect_source_files", return_value=list(core.items())), \
             mock.patch.object(builder, "_validated_quality_report", return_value=(report, json_bytes(report))):
            build(output, "2026-09-11", "synthetic", source, self.root / "synthetic-report.json")
        manifest = json.loads((output / "distribution-manifest.json").read_text())
        for name, expected in manifest["artifacts"].items():
            self.assertEqual(digest((output / name).read_bytes()), expected, name)

    def test_compact_core_rejects_malformed_certification_artifacts(self):
        from dual_distribution import compact_distribution_core

        active = b'{"gate_id":"GATE-TEST","status":"passed"}\n'
        active_hash = digest(active)
        evidence = {
            "profile_id": "DEMO",
            "evidence_manifest": [{
                "path": f"certification-details/{active_hash}/GATE-TEST.json",
                "sha256": active_hash,
                "size": len(active),
                "gate_id": "GATE-TEST",
            }],
        }
        core = {
            "profiles/DEMO/certification-evidence.json": json.dumps(evidence).encode(),
            f"profiles/DEMO/certification-details/{active_hash}/GATE-TEST.json": active,
        }
        malformed_size = json.loads(json.dumps(evidence))
        malformed_size["evidence_manifest"][0]["size"] += 1
        with self.assertRaisesRegex(ValueError, "Invalid certification artifact"):
            compact_distribution_core({
                **core,
                "profiles/DEMO/certification-evidence.json": json.dumps(malformed_size).encode(),
            })
        noncanonical_path = json.loads(json.dumps(evidence))
        noncanonical_path["evidence_manifest"][0]["path"] = (
            f"other-details/{active_hash}/GATE-TEST.json"
        )
        with self.assertRaisesRegex(ValueError, "Noncanonical certification artifact path"):
            compact_distribution_core({
                **core,
                "profiles/DEMO/certification-evidence.json": json.dumps(noncanonical_path).encode(),
                f"profiles/DEMO/other-details/{active_hash}/GATE-TEST.json": active,
            })
        with self.assertRaisesRegex(ValueError, "Unsupported historical certification artifact path"):
            compact_distribution_core({
                **core,
                "profiles/DEMO/certification-details/not-a-content-hash/GATE-OLD.json": b"old\n",
            })

    def test_release_builder_compacts_the_codex_and_copilot_cores_equally(self):
        from build_candidate_package import build
        from dual_distribution import runtime_identity
        from validate_copilot_package import validate
        import build_candidate_package as builder

        active = b'{"gate_id":"GATE-TEST","status":"passed"}\n'
        historical = b'{"gate_id":"GATE-OLD","status":"passed"}\n'
        active_hash, historical_hash = digest(active), digest(historical)
        core = {
            **self.core,
            "distribution/dual.json": b'{"schema_version":"1.0","project_schema":"1.5"}',
            "profiles/DEMO/certification-evidence.json": json.dumps({
                "profile_id": "DEMO",
                "evidence_manifest": [{
                    "path": f"certification-details/{active_hash}/GATE-TEST.json",
                    "sha256": active_hash,
                    "size": len(active),
                    "gate_id": "GATE-TEST",
                }],
            }).encode(),
            f"profiles/DEMO/certification-details/{active_hash}/GATE-TEST.json": active,
            f"profiles/DEMO/certification-details/{historical_hash}/GATE-OLD.json": historical,
        }
        report = {"gate": {"status": "passed"}, "channel": "candidate", "comparison": {"baseline_commit": "synthetic"}}
        output = self.root / "release-hosts"
        source = self.root / "release-source"
        source.mkdir()
        with mock.patch.object(builder, "_validate_source_checkout", return_value=source), \
             mock.patch.object(builder, "collect_source_files", return_value=sorted(core.items())), \
             mock.patch.object(builder, "_validated_quality_report", return_value=(report, json.dumps(report).encode())):
            build(output, "2026-09-11", "synthetic", source, self.root / "synthetic-report.json")

        def unpack(data: bytes) -> dict[str, bytes]:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                return {name: archive.read(name) for name in archive.namelist()}

        version = json.loads(self.core[".codex-plugin/plugin.json"])["version"]
        plugin = unpack((output / f"lks-sdd-plugin-v{version}.zip").read_bytes())
        marketplace = unpack((output / f"lks-sdd-marketplace-v{version}.zip").read_bytes())
        native_archive = (output / f"lks-sdd-copilot-plugin-v{version}.zip").read_bytes()
        native = unpack(native_archive)
        plugin_core = {name.removeprefix("lks-sdd/"): data for name, data in plugin.items()}
        marketplace_core = {
            name.removeprefix("plugins/lks-sdd/"): data
            for name, data in marketplace.items()
            if name.startswith("plugins/lks-sdd/")
        }
        native_core = {
            name.removeprefix("lks-sdd/core/"): data
            for name, data in native.items()
            if name.startswith("lks-sdd/core/")
        }
        project = unpack((output / f"lks-sdd-copilot-v{version}.zip").read_bytes())
        lock = json.loads(project[".lks-sdd/distribution-lock.json"])
        runtime = lock["runtime"] + "/"
        project_core = {
            name.removeprefix(runtime): data
            for name, data in project.items()
            if name.startswith(runtime)
        }
        self.assertEqual(plugin_core, marketplace_core)
        self.assertEqual(plugin_core, native_core)
        self.assertEqual(plugin_core, project_core)
        self.assertEqual(lock["runtime_digest"], runtime_identity(project_core))
        for files in (plugin_core, marketplace_core, native_core, project_core):
            self.assertFalse(any(re.search(r"certification-details/[0-9a-f]{64}/", path) for path in files))
            self.assertIn(f"profiles/DEMO/certification-history/{historical_hash[:12]}.json", files)
        evidence = json.loads(plugin_core["profiles/DEMO/certification-evidence.json"])
        artifact = evidence["evidence_manifest"][0]
        self.assertEqual(artifact["path"], f"certification-details/{active_hash[:12]}.json")
        self.assertEqual(digest(plugin_core["profiles/DEMO/" + artifact["path"]]), artifact["sha256"])
        self.assertEqual(len(plugin_core["profiles/DEMO/" + artifact["path"]]), artifact["size"])
        integrity = json.loads(plugin_core["package-integrity.json"])
        for item in integrity["files"]:
            self.assertEqual(digest(plugin_core[item["path"]]), item["sha256"])
            self.assertEqual(len(plugin_core[item["path"]]), item["size"])
        self.assertEqual(validate(native_archive)["status"], "valid")

    def test_full_runtime_installs_initializes_and_rejects_wrong_global_cli(self):
        from build_dual_distribution import collect_development
        import subprocess
        core = collect_development(ROOT)
        files, bundle = self.native_setup(core)
        # Every native adapter links to a real full workflow and onboarding guide.
        self.assertIn("core/docs/LEARNING-GUIDE.md", files)
        self.assertIn("core/docs/COPILOT-PILOT.md", files)
        for suffix in SKILLS:
            self.assertIn(f"core/skills/lks-sdd-{suffix}/SKILL.md", files)
        preview = installer.plan(bundle, self.consumer, "copilot")
        installer.apply(preview, preview["preview_hash"])
        lock = json.loads((self.consumer / ".lks-sdd/distribution-lock.json").read_text())
        cli = self.consumer / lock["runtime"] / "scripts/lks_sdd.py"
        def command(path, *args):
            return subprocess.run([sys.executable, "-X", "utf8", str(path), *args], capture_output=True,
                                  text=True, encoding="utf-8", cwd=self.consumer)
        proposed = command(cli, "define", str(self.consumer), "--project-id", "synthetic-dual", "--json")
        self.assertEqual(proposed.returncode, 0, proposed.stdout + proposed.stderr)
        self.assertFalse((self.consumer / ".lks-sdd/project.json").exists())
        defined = command(cli, "define", str(self.consumer), "--project-id", "synthetic-dual", "--json",
                          "--apply", "--authorize", json.loads(proposed.stdout)["preview_hash"])
        self.assertEqual(defined.returncode, 0, defined.stdout + defined.stderr)
        self.assertEqual(json.loads((self.consumer / ".lks-sdd/project.json").read_text())["schema_version"], "2.0")
        validated = command(cli, "validate-project", str(self.consumer), "--json")
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
        wrong = command(ROOT / "scripts/lks_sdd.py", "validate-project", str(self.consumer), "--json")
        self.assertEqual(wrong.returncode, 2)
        self.assertIn("project-pinned", wrong.stdout)
        self.assertEqual(check(self.consumer)["status"], "valid")

    def test_native_plugin_paths_fit_a_windows_plugin_cache(self):
        from build_dual_distribution import collect_development
        core = collect_development(ROOT)
        files = copilot_plugin_files(core, "synthetic-test", "development-not-certified")
        longest = max(len(str(PurePosixPath("lks-sdd") / path)) for path in files)
        self.assertLessEqual(longest, 110)
        standard_cache = PureWindowsPath(
            r"C:\Users\very-long-local-profile\AppData\Roaming\Code\User\globalStorage\github.copilot-chat\plugins"
        )
        absolute_longest = max(
            len(str(standard_cache / "lks-sdd" / PureWindowsPath(path)))
            for path in files
        )
        # Keep a margin below the legacy 260-character Windows path limit.
        self.assertLessEqual(absolute_longest, 240)
        self.assertFalse(any(re.search(r"certification-details/[0-9a-f]{64}/", path) for path in files))


if __name__ == "__main__":
    unittest.main()
