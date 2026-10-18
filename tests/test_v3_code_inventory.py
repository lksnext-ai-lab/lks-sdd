"""Automatic inventories and strict inputs share the same exclusion policy."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v2_contract import ContractError, path_at, read_bytes, relative_parts, sha
from query_sources import SECRET_NAME
from v3_git import code_inventory, scope_changes, subject


class CodeInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v3-code-inventory-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.write("app.py", b"answer = 42\n")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args],
                              check=True, capture_output=True, timeout=60)

    def write(self, relative, data=b"synthetic placeholder\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_app_and_env_example_inventory_without_reading_excluded_file(self):
        self.write(".env.example", b"DEMO=placeholder\n")
        for tracked in (False, True):
            with self.subTest(tracked=tracked):
                if tracked:
                    self.git("add", "--", "app.py", ".env.example")
                with patch("v3_git.read_bytes", wraps=read_bytes) as reader:
                    self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))
                self.assertEqual(["app.py"], [call.args[1] for call in reader.call_args_list])

    def test_sensitive_names_in_any_component_are_excluded_before_subject(self):
        forbidden = [
            ".env", ".env.example", ".env.local", "config/.ENV.template",
            "nested/.env.example/module.py", "secrets.json", "config/credentials.yaml",
            "secrets/module.py", "config/team-credentials/module.py",
            "config/id_rsa.pub", "config/id_ed25519", "cert.pem", "config/cert.key",
            "config/archive.pfx", "config/archive.p12", "config/app.keystore",
        ]
        for relative in forbidden:
            self.write(relative)
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
                    relative_parts(relative)
        self.git("add", "--", ".")
        with patch("v3_git.subject", wraps=subject) as selected:
            self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))
        self.assertEqual([["app.py"]], [call.args[1] for call in selected.call_args_list])

    def test_git_components_are_excluded_at_any_depth(self):
        forbidden = [".git/config", "src/.git/config", "src/.GiT/config"]
        raw = b"app.py\0" + b"\0".join(p.encode() for p in forbidden) + b"\0"
        with patch("v3_git.git", return_value=raw), patch("v3_git.subject", wraps=subject) as selected:
            self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))
        self.assertEqual([["app.py"]], [call.args[1] for call in selected.call_args_list])
        for relative in forbidden:
            with self.subTest(relative=relative), self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
                subject(self.root, [relative])

    def test_explicit_forbidden_inputs_remain_rejected(self):
        for relative in (".env.example", "config/.env.example", "secrets/module.py", "config/cert.key"):
            self.write(relative)
            for operation in (lambda p: subject(self.root, [p]),
                              lambda p: path_at(self.root, p), lambda p: read_bytes(self.root, p)):
                with self.subTest(relative=relative, operation=operation):
                    with self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
                        operation(relative)
        with self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
            subject(self.root, ["secrets"])
        with self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
            subject(self.root, ["config"])

    def test_package_placeholder_exception_is_not_enabled_for_inventory(self):
        self.write("config/.env.example")
        self.assertEqual(["config", ".env.example"], relative_parts("config/.env.example", package_data=True))
        self.assertEqual(b"synthetic placeholder\n", read_bytes(self.root, "config/.env.example", package_data=True))
        for relative in (".env.example/app.py", "secrets/.env.example", "src/.git/.env.example"):
            with self.subTest(relative=relative), self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
                relative_parts(relative, package_data=True)
        self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))

    def test_policy_updates_are_shared_with_explicit_reader(self):
        relative = "config/synthetic-denied/module.py"
        self.write(relative)
        policy = re.compile(SECRET_NAME.pattern + r"|^synthetic-denied$")
        with patch("v2_contract.SECRET_NAME", policy):
            with self.assertRaisesRegex(ContractError, "Sensitive or Git path"):
                subject(self.root, [relative])
            self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))

    def test_allowed_similar_names_and_sdd_exclusions_are_preserved(self):
        allowed = ["secretary.py", "mycredentials.py", ".environment", "private/keymap.py"]
        for relative in allowed + ["docs/lks-sdd/note.md", ".lks-sdd/project.json"]:
            self.write(relative)
        (self.root / ".gitignore").write_bytes(b"ignored.py\n")
        self.write("ignored.py")
        expected = {"app.py": sha(b"answer = 42\n"), ".gitignore": sha(b"ignored.py\n")}
        expected.update({relative: sha(b"synthetic placeholder\n") for relative in allowed})
        self.assertEqual(expected, code_inventory(self.root))

    def test_allowed_changes_and_deletions_survive_excluded_changes(self):
        self.write("src/changed.py", b"before\n")
        self.write("src/deleted.py")
        self.write("src/removed.py")
        self.write("src/untracked.py")
        self.write("outside.py", b"before\n")
        self.write(".env.example")
        self.git("add", "--", "src/changed.py", "src/deleted.py", "src/removed.py", ".env.example")
        baseline = code_inventory(self.root)
        self.write("src/changed.py", b"after\n")
        self.write("src/added.py")
        self.write("outside.py", b"after\n")
        (self.root / "src/deleted.py").unlink()
        (self.root / "src/removed.py").unlink()
        (self.root / "src/untracked.py").unlink()
        self.git("rm", "--cached", "--", "src/removed.py")
        self.write(".env.example", b"DEMO=changed-placeholder\n")
        self.write("config/credentials.json")
        changes = scope_changes(self.root, baseline, ["src"])
        self.assertEqual(["outside.py", "src/added.py", "src/changed.py", "src/deleted.py",
                          "src/removed.py", "src/untracked.py"], changes["changed"])
        self.assertEqual(["outside.py"], changes["outside"])
        self.assertIsNone(changes["current"]["src/deleted.py"])
        self.assertNotIn("src/removed.py", changes["current"])
        self.assertEqual(sha(b"after\n"), changes["current"]["src/changed.py"])
        self.assertNotIn(".env.example", changes["current"])
        self.assertNotIn("config/credentials.json", changes["current"])

    def test_excluded_creation_modification_and_deletion_do_not_change_inventory(self):
        baseline = code_inventory(self.root)
        excluded = self.write(".env.example")
        self.git("add", "--", ".env.example")
        for data in (b"first placeholder\n", b"second placeholder\n", None):
            with self.subTest(data=data):
                if data is None:
                    excluded.unlink()
                else:
                    excluded.write_bytes(data)
                self.assertEqual({"changed": [], "outside": [], "current": baseline},
                                 scope_changes(self.root, baseline, ["app.py"]))

    def test_unsafe_paths_are_errors_even_when_they_contain_sensitive_names(self):
        for relative in ("../app.py", "./app.py", "src//app.py", "/app.py", r"src\app.py",
                         "src:app.py", "../secrets/app.py", "src//.env.example"):
            with self.subTest(relative=relative), patch("v3_git.git", return_value=relative.encode() + b"\0"):
                with self.assertRaisesRegex(ContractError, "Unsafe project-relative path"):
                    code_inventory(self.root)
        with patch("v3_git.git", return_value=b"invalid-\xff.py\0"), self.assertRaises(UnicodeDecodeError):
            code_inventory(self.root)

    def test_other_read_errors_propagate_through_inventory_and_scope_changes(self):
        operations = [lambda: code_inventory(self.root), lambda: scope_changes(self.root, {}, ["app.py"])]
        errors = [ContractError("Source identity changed before reading"),
                  ContractError("Source changed during reading"), PermissionError("synthetic denied read"),
                  OSError("synthetic filesystem failure")]
        for operation in operations:
            for error in errors:
                with self.subTest(operation=operation, error=error), patch("v3_git.read_bytes", side_effect=error):
                    with self.assertRaises(type(error)) as caught:
                        operation()
                    self.assertIs(error, caught.exception)

    def test_link_and_nested_repository_guards_remain_active(self):
        import stat
        from types import SimpleNamespace
        original_lstat = Path.lstat
        from v2_contract import file_attributes
        def linked_info(path, *args, **kwargs):
            if path.name == "app.py": return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0x400)
            return original_lstat(path, *args, **kwargs)
        # Inject the observed filesystem condition, rather than the former
        # implementation's helper call. Link rejection remains before reading.
        with patch.object(Path, "lstat", new=linked_info), \
             patch("v2_contract.file_attributes", side_effect=lambda p: 0x400 if p.name == "app.py" else file_attributes(p)):
            with self.assertRaisesRegex(ContractError, "Link/junction rejected"):
                code_inventory(self.root)
        self.write("nested/app.py")
        self.git("add", "--", "nested/app.py")
        (self.root / "nested/.git").mkdir()
        with self.assertRaisesRegex(ContractError, "Nested repository rejected"):
            code_inventory(self.root)

    def test_file_read_budget_is_preserved(self):
        with (self.root / "app.py").open("wb") as stream:
            stream.truncate(64 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(ContractError, "Not a bounded regular source"):
            code_inventory(self.root)

    def test_large_internal_and_sensitive_histories_do_not_consume_code_limit(self):
        for prefix in (".lks-sdd/objects/sha256", "docs/lks-sdd/00-control/history", "secrets"):
            raw = b"app.py\0" + b"\0".join(f"{prefix}/{i}".encode() for i in range(20001)) + b"\0"
            with self.subTest(prefix=prefix), patch("v3_git.git", return_value=raw), \
                 patch("v3_git.subject", wraps=subject) as selected:
                self.assertEqual({"app.py": sha(b"answer = 42\n")}, code_inventory(self.root))
                self.assertEqual([["app.py"]], [call.args[1] for call in selected.call_args_list])

    def test_report_census_counts_only_eligible_code_and_deduplicates(self):
        paths = [f".lks-sdd/objects/{i}" for i in range(18847)]
        paths += [f"src/{i}.py" for i in range(1180)]
        raw = b"\0".join(p.encode() for p in paths + paths[:3]) + b"\0"
        def selected(root, scope): return {"files": {scope[0]: "0" * 64}}
        with patch("v3_git.git", return_value=raw), patch("v3_git.subject", side_effect=selected) as reader:
            self.assertEqual(1180, len(code_inventory(self.root)))
            self.assertEqual(1180, reader.call_count)

    def test_eligible_boundary_is_checked_before_reading_bodies(self):
        def selected(root, scope): return {"files": {scope[0]: "0" * 64}}
        for count in (20000, 20001):
            raw = b"\0".join(f"src/{i}.py".encode() for i in range(count)) + b"\0"
            with self.subTest(count=count), patch("v3_git.git", return_value=raw), \
                 patch("v3_git.subject", side_effect=selected) as reader:
                if count == 20000:
                    self.assertEqual(count, len(code_inventory(self.root)))
                else:
                    with self.assertRaisesRegex(ContractError, "Inventario de código demasiado amplio"):
                        code_inventory(self.root)
                    reader.assert_not_called()

    def test_raw_bound_and_partial_observations_are_independent(self):
        for raw, message in [(b"secrets/a\0" * 4, "Enumeración Git"),
                             (b"app.py", "Inventario Git incompleto")]:
            with self.subTest(message=message), patch("v3_git.RAW_PATH_LIMIT", 3), \
                 patch("v3_git.git", return_value=raw), patch("v3_git.subject") as reader:
                with self.assertRaisesRegex(ContractError, message): code_inventory(self.root)
                reader.assert_not_called()

    def test_internal_prefix_lookalikes_are_code(self):
        for path in (".lks-sdd-other/app.py", "docs/lks-sdd-other/app.py"):
            self.write(path)
        self.assertEqual(3, len(code_inventory(self.root)))

    def test_long_path_prefix_cannot_repair_incomplete_git_output(self):
        incomplete = subprocess.CompletedProcess([], 0, b"nested/app.py", b"")
        with patch("v3_git._invocation", return_value=(["git"], None, "nested/", self.root)), \
             patch("v3_git._bounded_ls_files", return_value=incomplete):
            with self.assertRaisesRegex(ContractError, "Inventario Git incompleto"):
                code_inventory(self.root)

    def test_git_errors_output_budget_and_timeout_remain_errors(self):
        results = [
            (subprocess.CompletedProcess([], 1, b"", b"synthetic git failure"), ContractError, "Git no pudo"),
            (subprocess.CompletedProcess([], 0, b"x" * (16 * 1024 * 1024 + 1), b""), ContractError, "Salida Git excesiva"),
        ]
        for result, error, message in results:
            with self.subTest(message=message), patch("v3_git._bounded_ls_files", return_value=result):
                with self.assertRaisesRegex(error, message):
                    code_inventory(self.root)
        timeout = subprocess.TimeoutExpired("git", 60)
        with patch("v3_git._bounded_ls_files", side_effect=timeout), self.assertRaisesRegex(ContractError, "60 s"):
            code_inventory(self.root)


class BoundedGitCaptureTests(unittest.TestCase):
    def invoke(self, source, **limits):
        import contextlib
        import v3_git
        with contextlib.ExitStack() as stack:
            for name, value in limits.items(): stack.enter_context(patch.object(v3_git, name, value))
            return v3_git._bounded_ls_files([sys.executable, "-B", "-c", source])

    def test_both_pipes_complete_without_shell_and_preserve_exit_status(self):
        result = self.invoke("import os,sys; os.write(1,b'app.py\\0'); os.write(2,b'diagnostic'); sys.exit(3)")
        self.assertEqual((3, b"app.py\0", b"diagnostic"), (result.returncode, result.stdout, result.stderr))

    def test_exact_byte_and_record_limits_accept_complete_output(self):
        result = self.invoke("import os; os.write(1,b'a\\0b\\0'); os.write(2,b'err')",
                             GIT_STDOUT_LIMIT=4, GIT_STDERR_LIMIT=3, RAW_PATH_LIMIT=2)
        self.assertEqual((0, b"a\0b\0", b"err"), (result.returncode, result.stdout, result.stderr))

    def test_large_concurrent_pipes_are_drained_completely(self):
        result = self.invoke("import os; "
                             "[(os.write(1,b'p\\0'*2048),os.write(2,b'e'*4096)) for _ in range(32)]",
                             GIT_STDERR_LIMIT=131072)
        self.assertEqual((0, b"p\0" * 65536, b"e" * 131072),
                         (result.returncode, result.stdout, result.stderr))

    def test_limits_stop_live_producers_and_release_reader_threads(self):
        import threading
        cases = [
            ("os.write(1,b'x'*129)", {"GIT_STDOUT_LIMIT": 128}, "Salida Git excesiva"),
            ("os.write(2,b'x'*129)", {"GIT_STDERR_LIMIT": 128}, "Error Git excesivo"),
            ("os.write(1,b'p\\0'*4)", {"RAW_PATH_LIMIT": 3}, "Enumeración Git demasiado amplia"),
        ]
        for output, limits, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ContractError, message):
                self.invoke("import os,time; " + output + "; time.sleep(30)",
                            GIT_INVENTORY_TIMEOUT=2, **limits)
            self.assertFalse(any(t.name == "lks-git-pipe" for t in threading.enumerate()))

    def test_timeout_kills_child_and_releases_readers(self):
        import threading
        with self.assertRaises(subprocess.TimeoutExpired):
            self.invoke("import os,time; os.write(1,b'app.py\\0'); time.sleep(30)",
                        GIT_INVENTORY_TIMEOUT=0.2)
        self.assertFalse(any(t.name == "lks-git-pipe" for t in threading.enumerate()))

    def test_timeout_releases_pipes_retained_by_a_descendant(self):
        import os
        import signal
        import threading
        with tempfile.TemporaryDirectory(prefix="git-retained-pipe-") as directory:
            pid_file = Path(directory) / "child.pid"
            source = ("import os,subprocess,sys,pathlib; "
                      "child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(30)']); "
                      f"pathlib.Path({str(pid_file)!r}).write_text(str(child.pid)); "
                      "os.write(1,b'app.py\\0')")
            try:
                owned = []
                popen = subprocess.Popen
                def launch(*args, **kwargs):
                    process = popen(*args, **kwargs); owned.append(process)
                    return process
                with patch("v3_git.subprocess.Popen", side_effect=launch):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        self.invoke(source, GIT_INVENTORY_TIMEOUT=0.5)
                self.assertTrue(pid_file.exists(), "The retained-pipe descendant must actually start")
                self.assertEqual(1, len(owned))
                self.assertIsNotNone(owned[0].poll())
                self.assertTrue(owned[0].stdout.closed and owned[0].stderr.closed)
                self.assertFalse(any(t.name == "lks-git-pipe" for t in threading.enumerate()))
            finally:
                if pid_file.exists():
                    try: os.kill(int(pid_file.read_text()), signal.SIGTERM)
                    except ProcessLookupError: pass
                # Clean up the old implementation's readers after a failing regression.
                for reader in threading.enumerate():
                    if reader.name == "lks-git-pipe": reader.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
