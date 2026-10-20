"""Bounded consent and exact recovery, without volume campaigns or host activity."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import contextlib
import io
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import capacity as cap
from v2_contract import ContractError, canonical, fingerprint, read_bytes, sha
from content_store import object_path, publish_object, read_object, reference
from v3_presentation_guard import ACTIVE, stamp


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cap-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.data = {"actor": "synthetic", "request": "synthetic-request"}

    def request(self, name="source_bytes", observed=5*cap.MiB, normal=4*cap.MiB, **kwargs):
        with cap.session(self.root, "context", self.data, **kwargs):
            with self.assertRaises(cap.CapacityRequired) as raised:
                cap.require(name, observed, normal, "ordinary capacity reached")
        return raised.exception.request

    def approve(self, request):
        return {"request": request, "approved": True, "statement": "Synthetic explicit user OK for these resources"}

    def test_every_supported_budget_requires_specific_consent_and_resets(self):
        for name, normal in cap.DEFAULTS.items():
            with self.subTest(resource=name):
                request = self.request(name, normal + 1, normal)
                approval = self.approve(request)
                with cap.session(self.root, "context", self.data, approval=approval):
                    self.assertGreaterEqual(cap.require(name, normal+1, normal, "limit"), normal+1)
                    self.assertEqual(approval, cap.consent())
                self.assertIsNone(cap.consent())

    def test_denial_changed_inputs_project_and_tampering_are_rejected(self):
        approval = self.approve(self.request())
        for changed in [dict(approval, approved=False), dict(approval, statement=""),
                        {**approval, "request": {**approval["request"], "limits": {"source_bytes": 2**50}}}]:
            with self.subTest(value=str(changed)[:50]):
                with self.assertRaises(ContractError):
                    with cap.session(self.root, "context", self.data, approval=changed): pass
        for root, action, data in [(self.root/"other", "context", self.data),
                                   (self.root, "author", self.data),
                                   (self.root, "context", {**self.data, "request": "another"})]:
            with self.assertRaises(ContractError):
                with cap.session(root, action, data, approval=approval): pass

    def test_same_decision_view_and_operation_share_capacity_without_granting_authority(self):
        with cap.session(self.root, "decision-view", {"event": "context", "data": self.data}):
            with self.assertRaises(cap.CapacityRequired) as raised:
                cap.require("source_bytes", 5*cap.MiB, 4*cap.MiB, "large source")
        approval = self.approve(raised.exception.request)
        with cap.session(self.root, "context", {**self.data, "presented": {"fresh": "receipt"}}, approval=approval):
            self.assertEqual(64*cap.MiB, cap.limit("source_bytes", 4*cap.MiB))
        self.assertEqual({"actor", "request"}, set(self.data))

    def test_larger_requirement_needs_new_ok_and_format_limit_is_not_overridden(self):
        approval = self.approve(self.request("document_files", 10001, 10000))
        maximum = approval["request"]["limits"]["document_files"]
        with cap.session(self.root, "context", self.data, approval=approval):
            with self.assertRaises(cap.CapacityRequired):
                cap.require("document_files", maximum + 1, 10000, "more files")
            with self.assertRaisesRegex(ContractError, "compatible format"):
                cap.require("source_bytes", 64*cap.MiB + 1, 4*cap.MiB, "too large")

    def test_recovery_extension_preserves_both_user_responses(self):
        original = self.approve(self.request("document_files", 10001, 10000))
        maximum = original["request"]["limits"]["document_files"]
        extension = self.approve(self.request("document_files", maximum+1, 10000, approval=original))
        saved = copy.deepcopy((original, extension))
        with cap.session(self.root, "context", self.data, approval=extension):
            with cap.recorded(self.root, original):
                self.assertGreater(cap.limit("document_files", 10000), maximum)
                self.assertEqual(original, cap.consent())
        self.assertEqual(saved, (original, extension))

    def test_regular_large_source_requires_ok_but_cas_guard_does_not(self):
        raw = b"x" * (5 * cap.MiB)
        (self.root/"large.log").write_bytes(raw)
        with cap.session(self.root, "context", self.data):
            with self.assertRaises(cap.CapacityRequired) as raised:
                read_bytes(self.root, "large.log")
        approval = self.approve(raised.exception.request)
        with cap.session(self.root, "context", self.data, approval=approval):
            self.assertEqual(raw, read_bytes(self.root, "large.log"))
        ref = reference(raw); name = object_path(ref)
        publish_object(self.root, name, raw)
        token = ACTIVE.set({"root": str(self.root), "receipt": {"synthetic": True},
                            "basis": {"source_files": {name: ref["sha256"]}, "attachments": []}})
        try:
            sources = {}; stamp(self.root, [], sources, {})
            self.assertEqual({name: ref["sha256"]}, sources)
        finally: ACTIVE.reset(token)
        (self.root/name).write_bytes(b"tampered")
        with self.assertRaises(ContractError): read_object(self.root, ref)

    def test_caps_never_suppress_link_or_source_integrity_checks(self):
        approval = self.approve(self.request())
        with cap.session(self.root, "context", self.data, approval=approval):
            with self.assertRaises(ContractError): read_bytes(self.root, "../escape.log")
            with self.assertRaises(ContractError): read_bytes(self.root, ".git/config")

    def test_maintenance_consent_survives_apply_and_recovery(self):
        import store_compaction as core
        import test_store_compaction as support
        import object_zip as codec
        from v2_storage import write_one
        case = support.CompactionTests("runTest"); case.setUp(); self.addCleanup(case.doCleanups)
        root = case.root.resolve()
        lock_path = core.legacy.PIN
        lock = json.loads((root/lock_path).read_bytes())
        raw = (ROOT/"scripts/capacity.py").read_bytes()
        write_one(root, lock["runtime"]+"/scripts/capacity.py", raw)
        lock["runtime_files"]["scripts/capacity.py"] = sha(raw)
        write_one(root, lock_path, canonical(lock))
        data = {"backup_dir": str(case.base/"backup-dir"), "restore": str(case.base/"restore-v2")}
        with cap.session(root, "store-preview", data):
            with self.assertRaises(cap.CapacityRequired) as reached:
                cap.require("zip_index_bytes", cap.DEFAULTS["zip_index_bytes"]+1,
                            cap.DEFAULTS["zip_index_bytes"], "synthetic index boundary")
        approval = self.approve(reached.exception.request)
        with cap.session(root, "store-preview", data, approval=approval):
            plan = core.preview(root, data["backup_dir"], data["restore"])
        self.assertEqual(approval, plan["manifest"]["capacity"])
        key = plan["preview_hash"]
        with patch.object(codec, "MAX_INDEX_TOTAL", 1):
            result = core.apply(root, plan, key)
            self.assertEqual("awaiting-removal-authorization", result["status"])
            self.assertIsNone(cap.consent())
            with self.assertRaises(ContractError): read_object(root, reference(case.bodies[0]))
            result = core.recover(root, key, remove_authorized=key)
            self.assertEqual("compacted", result["status"])
            with cap.recorded(root, approval): case.assert_logical()
        self.assertIsNone(cap.consent())

    def test_historical_state_link_uses_the_approved_source_budget(self):
        import document_state as state
        from v2_storage import write_one
        raw = b"x"*(5*cap.MiB)
        (self.root/"source.txt").write_bytes(raw)
        changes = {}; identity = state.prepare(self.root, {"source.txt": sha(raw)}, changes)
        for name, content in changes.items(): write_one(self.root, name, content)
        name = state.PREFIX+identity+"/tree/source.txt"
        with cap.session(self.root, "context", self.data):
            with self.assertRaises(cap.CapacityRequired) as reached: read_bytes(self.root, name)
        with cap.session(self.root, "context", self.data, approval=self.approve(reached.exception.request)):
            self.assertEqual(raw, read_bytes(self.root, name))

    def test_large_usage_receipt_reuses_the_approved_batch_budget(self):
        from types import SimpleNamespace
        from usage_test_support import observation
        from v3_usage import validate_receipt, FORMAT
        row = observation(); row["input"]["synthetic_large"] = "x"*(cap.MiB+1)
        raw = canonical({"format": FORMAT, "observations": [row]})
        ref = reference(raw); publish_object(self.root, object_path(ref), raw)
        entry = SimpleNamespace(meta={"data": {"count": 1, "observations_ref": ref,
            "run_id": row["run_id"], "request": row["binding"]["request"],
            "tasks": row["binding"]["tasks"], "observation_ids": [row["observation_id"]]}})
        with cap.session(self.root, "context", self.data):
            with self.assertRaises(cap.CapacityRequired) as reached:
                validate_receipt(SimpleNamespace(root=self.root, hashes={}), entry)
        with cap.session(self.root, "context", self.data, approval=self.approve(reached.exception.request)):
            model = SimpleNamespace(root=self.root, hashes={})
            validate_receipt(model, entry)
            self.assertEqual(ref["sha256"], model.hashes[object_path(ref)])

    def test_composed_capacity_failure_keeps_preceding_stage_receipts(self):
        from types import SimpleNamespace
        import v4_work_operations as work
        chosen = {"operation_id": "synthetic-op", "task": "task", "actor": "actor", "basis": {}, "parameters": {}}
        rows = {0: {"stage": "synthetic-stage", "preview_hash": "a"*64, "receipt": ".lks-sdd/transactions.json"}}
        needed = cap.CapacityRequired("synthetic late capacity", self.request())
        with patch.object(work, "request", return_value=chosen), patch.object(work, "_steps", return_value=["first", "second"]), \
             patch.object(work, "_receipts", side_effect=[(rows, None), (rows, None)]), \
             patch.object(work, "_fresh", return_value=(None, SimpleNamespace(uid="task"))), \
             patch("v3_context.context", return_value={"sources": ["literal contract"], "attachments": []}), \
             patch.object(work, "_prepare", side_effect=needed):
            with self.assertRaises(cap.CapacityRequired) as caught:
                work.run(self.root, "work-continue", {}, apply=True)
        self.assertEqual("partial", caught.exception.operation_result["status"])
        self.assertEqual("a"*64, caught.exception.operation_result["effects"][0]["preview_hash"])

    def test_legacy_maintenance_never_offers_an_unrecoverable_expansion(self):
        data = {"backup": "external.zip", "restore": "external-restore"}
        with cap.session(self.root, "store-preview", data):
            with self.assertRaisesRegex(ContractError, "compatible bounds"):
                cap.require("zip_index_bytes", cap.DEFAULTS["zip_index_bytes"]+1,
                            cap.DEFAULTS["zip_index_bytes"], "synthetic legacy index budget")

    def test_consent_file_rejects_duplicate_fields_and_a_new_transaction_generation(self):
        approval = self.approve(self.request())
        with tempfile.TemporaryDirectory(prefix="cap-external-") as external:
            source = Path(external)/"approval.json"
            source.write_text('{"request":'+json.dumps(approval["request"])+
                              ',"approved":false,"approved":true,"statement":"ambiguous"}', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "Duplicate"):
                with cap.session(self.root, "context", self.data, approval_path=source): pass
        folder = self.root/".lks-sdd"; folder.mkdir()
        (folder/"transactions.json").write_bytes(canonical({"schema_version":"2.0", "transactions":{}}))
        with self.assertRaisesRegex(ContractError, "stale"):
            with cap.session(self.root, "context", self.data, approval=approval): pass

    def test_approved_packet_recovery_and_rollback_retain_capacity(self):
        from v3_authoring import author
        from v3_contract import element, load
        from v3_storage import apply, recover
        from test_v3_workflow import ProjectFixture
        case = ProjectFixture("runTest"); case.setUp(); self.addCleanup(case.doCleanups)
        root = case.root
        item = element("rule", "Large permitted contract", "literal requirement " + "x"*(4*cap.MiB))
        data = {"actor": case.actor, "items": [item]}
        before = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
        with cap.session(root, "author", data):
            with self.assertRaises(cap.CapacityRequired) as raised:
                author(root, case.actor, [item])
        self.assertEqual(before, {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()})
        approval = self.approve(raised.exception.request)
        with cap.session(root, "author", data, approval=approval): packet = author(root, case.actor, [item])
        self.assertEqual(approval, packet["guards"]["capacity"])
        key = packet["preview"]["preview_hash"]
        altered = copy.deepcopy(packet)
        altered["guards"]["capacity"]["statement"] = "A fabricated different response"
        with self.assertRaisesRegex(ContractError, "altered"):
            apply(root, altered, key)
        canonical_before = {p.relative_to(root).as_posix(): sha(p.read_bytes())
                            for p in (root/"docs/lks-sdd").rglob("*") if p.is_file()}
        with patch("v2_storage.JOURNAL_BYTES", 8):
            with self.assertRaisesRegex(ContractError, "recovery format"):
                apply(root, packet, key)
        self.assertEqual(canonical_before, {p.relative_to(root).as_posix(): sha(p.read_bytes())
                                          for p in (root/"docs/lks-sdd").rglob("*") if p.is_file()})
        # A real late quota, after canonical writes, retains the pending journal.
        from v3_storage import validate_runtime
        def late_capacity(target, guards):
            if cap.same_filesystem_path(target, root):
                cap.require("document_files", approval["request"]["limits"]["document_files"]+1,
                            10000, "late validator capacity test")
            return validate_runtime(target, guards)
        with patch("v3_storage.validate_runtime", side_effect=late_capacity):
            with self.assertRaises(cap.CapacityRequired): apply(root, packet, key)
        self.assertTrue((root/".lks-sdd/transaction.json").exists())
        self.assertIsNone(cap.consent())
        # A late resource request must point at the existing journal, not ask
        # the caller to repeat an author operation over partial effects.
        from v3_cli import main
        with cap.session(root, "author", data, approval=approval):
            with self.assertRaises(cap.CapacityRequired) as extra:
                cap.require("document_files", approval["request"]["limits"]["document_files"]+1,
                            10000, "late capacity test")
        input_path = self.root/"intent.json"; input_path.write_bytes(canonical(data))
        output = io.StringIO()
        with patch("v3_cli.execute", side_effect=extra.exception), contextlib.redirect_stdout(output):
            code = main(["author", str(root), "--input", str(input_path), "--json"])
        partial = json.loads(output.getvalue())
        self.assertEqual(3, code, partial)
        self.assertEqual("partial", partial["status"])
        self.assertNotIn("recovery_inspection", partial, partial.get("recovery_inspection"))
        self.assertEqual(key, partial["effects"]["preview_hash"])
        recovery_consent = self.root/"recover-ok.json"
        recovery_consent.write_bytes(canonical(self.approve(partial["capacity_request"])))
        child = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT/"scripts/lks_sdd.py"),
                                "v3", "recover", str(root), "--authorize", key,
                                "--capacity-approval", str(recovery_consent), "--json"],
                               capture_output=True, timeout=90)
        self.assertEqual(0, child.returncode, child.stdout.decode("utf-8") + child.stderr.decode("utf-8"))
        result = json.loads(child.stdout)
        self.assertEqual("completed", result["status"])
        with cap.recorded(root, approval):
            self.assertEqual(item["body"].strip(), load(root).require_valid().get(item["meta"]["uid"]).body.strip())
        with self.assertRaisesRegex(ContractError, "stale"):
            with cap.session(root, "author", data, approval=approval): pass
        recover(root, key, rollback=True, receipt=result["receipt"])
        self.assertNotIn(item["meta"]["uid"], load(root).require_valid().elements)
        self.assertIsNone(cap.consent())
        invalid = {"actor": "unregistered-actor", "items": [item]}
        with cap.session(root, "author", invalid):
            with self.assertRaises(cap.CapacityRequired) as needed:
                cap.require("source_bytes", 5*cap.MiB, 4*cap.MiB, "test resource request")
        with cap.session(root, "author", invalid, approval=self.approve(needed.exception.request)):
            with self.assertRaises(ContractError): author(root, invalid["actor"], [item])


if __name__ == "__main__": unittest.main()
