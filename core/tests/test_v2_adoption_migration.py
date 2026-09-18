import json
from pathlib import Path
import tempfile
import unittest

from v2_fixture import write
from v2_contract import ContractError, DOCS, load, read_bytes
from v2_migration import diagnose, plan, migrate, migration_status, continuation_status
from v2_storage import recover
from eval_support import initialize, materialize_ready_increment


class V2MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        initialize(self.root, "synthetic-migration")

    def test_unsupported_origin_is_diagnostic_not_conversion(self):
        path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.2"
        write(self.root, ".lks-sdd/project.json", json.dumps(manifest))
        self.assertEqual(diagnose(self.root)["status"], "blocked")
        with self.assertRaises(ContractError):
            plan(self.root)

    def test_migration_preserves_custom_prose_and_evidence_bytes(self):
        write(self.root, DOCS + "/01-context/custom.md", "# Conocimiento parcial\n\nNunca borrar pedidos históricos.\n")
        write(self.root, DOCS + "/evidence/EVID-999.json", b'{"historical": true}\r\n')
        before = read_bytes(self.root, ".lks-sdd/project.json")
        result, changes = plan(self.root)
        self.assertEqual(result["feature_classification"], "not-inferred")
        outcome = migrate(self.root, result["preview_hash"])
        self.assertEqual(outcome["status"], "applied")
        model = load(self.root)
        self.assertTrue(model.valid, model.errors)
        self.assertEqual(read_bytes(self.root, DOCS + "/evidence/EVID-999.json"), b'{"historical": true}\r\n')
        self.assertIn("Nunca borrar pedidos históricos.", "\n".join(model.documents.values()))
        archive = result["mapping"][".lks-sdd/project.json"]["archive"]
        self.assertEqual(read_bytes(self.root, archive), before)
        self.assertEqual(model.by_kind("feature"), [])
        self.assertEqual(migrate(self.root, result["preview_hash"])["status"], "already-v2")

    def test_migration_receipt_closes_every_source_and_records_clean_cutover(self):
        write(self.root, DOCS + "/01-context/custom.md", "# Contexto\n\nTexto conservado.\n")
        result, _ = plan(self.root)
        self.assertEqual(result["migration_state"], "migration-complete")
        self.assertTrue(result["audit"]["all_sources_accounted"])
        self.assertEqual(sum(result["conservation_counts"].values()), len(result["conservation"]))
        outcome = migrate(self.root, result["preview_hash"])
        self.assertEqual(outcome["migration_state"], "migration-complete")
        self.assertEqual(migration_status(self.root)["status"], "migration-complete")
        receipt = json.loads(read_bytes(self.root, result["receipt"]))
        self.assertEqual(receipt["migration_state"], "migration-complete")
        self.assertEqual(receipt["closed_source_snapshot"], receipt["audit"]["closed_source_snapshot"])
        self.assertEqual({item["source"] for item in receipt["conservation"]},
                         set(receipt["mapping"]))
        self.assertEqual(receipt["audit"]["source_count"], len(receipt["conservation"]))

    def test_v2_header_alone_does_not_hide_mixed_legacy_documents(self):
        write(self.root, DOCS + "/02-design/legacy.md", "# Legacy activo\n")
        manifest = json.loads(read_bytes(self.root, ".lks-sdd/project.json"))
        manifest["schema_version"] = "2.0"
        manifest["method_version"] = "2.0.0"
        write(self.root, ".lks-sdd/project.json", json.dumps(manifest))
        status = migration_status(self.root)
        self.assertEqual(status["status"], "blocked")
        self.assertEqual(status["state"], "mixed-contract")
        self.assertEqual(diagnose(self.root)["status"], "blocked")

    def test_migration_status_detects_tampered_archived_source(self):
        result, _ = plan(self.root)
        migrate(self.root, result["preview_hash"])
        receipt = json.loads(read_bytes(self.root, result["receipt"]))
        archived = next(item["archive"] for item in receipt["conservation"] if item["archive"])
        with (self.root / archived).open("ab") as stream:
            stream.write(b"\ncorruption")
        status = migration_status(self.root)
        self.assertEqual(status["status"], "blocked")
        self.assertTrue(any("Archived source hash mismatch" in error for error in status["errors"]))

    def test_migration_status_detects_tampered_mapping_and_audit(self):
        result, _ = plan(self.root)
        migrate(self.root, result["preview_hash"])
        receipt = json.loads(read_bytes(self.root, result["receipt"]))
        source = receipt["conservation"][0]["source"]
        receipt["mapping"][source]["destination"] = "docs/lks-sdd/02-specification/tampered.md"
        receipt["conservation_counts"]["transformed"] = (
            receipt["conservation_counts"].get("transformed", 0) + 1)
        write(self.root, result["receipt"], json.dumps(receipt))
        status = migration_status(self.root)
        self.assertEqual(status["status"], "blocked")
        self.assertTrue(any("mapping/conservation mismatch" in error for error in status["errors"]))
        self.assertTrue(any("disposition counts mismatch" in error for error in status["errors"]))

    def test_continuation_reports_only_migrated_task_semantics_as_pending(self):
        materialize_ready_increment(self.root)
        result, _ = plan(self.root)
        migrate(self.root, result["preview_hash"])
        continuation = continuation_status(self.root, ["TASK-001"])
        self.assertEqual(continuation["status"], "blocked")
        self.assertTrue(any("TASK-001" in blocker for blocker in continuation["blockers"]))

    def test_stale_preview_and_exact_rollback(self):
        before = read_bytes(self.root, ".lks-sdd/project.json")
        result, _ = plan(self.root)
        outcome = migrate(self.root, result["preview_hash"])
        recover(self.root, result["preview_hash"], rollback=True, receipt=outcome["receipt"])
        self.assertEqual(read_bytes(self.root, ".lks-sdd/project.json"), before)
        write(self.root, DOCS + "/01-context/late.md", "# Documento nuevo\n")
        with self.assertRaises(ContractError):
            migrate(self.root, result["preview_hash"])

    def test_interruption_recover_and_protect_later_edits(self):
        result, _ = plan(self.root)
        with self.assertRaises(InterruptedError):
            migrate(self.root, result["preview_hash"], interrupt_after=2)
        outcome = recover(self.root, result["preview_hash"])
        self.assertTrue(load(self.root).valid)
        path = self.root / DOCS / "01-context/product-brief.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nCambio posterior.\n", encoding="utf-8")
        with self.assertRaises(ContractError):
            recover(self.root, result["preview_hash"], rollback=True, receipt=outcome["receipt"])

    def test_canonical_task_ids_and_raw_source_are_preserved(self):
        materialize_ready_increment(self.root)
        result, _ = plan(self.root)
        old = read_bytes(self.root, DOCS + "/04-delivery/tasks/TASK-001.md")
        outcome = migrate(self.root, result["preview_hash"])
        model = load(self.root)
        self.assertIn("TASK-001", model.elements)
        self.assertTrue(model.elements["TASK-001"].meta["reconciliation_required"])
        self.assertEqual(read_bytes(self.root, result["mapping"][DOCS + "/04-delivery/tasks/TASK-001.md"]["archive"]), old)
        self.assertEqual(outcome["authorization"], "reconciliation-required")

    def test_pinned_transition_preserves_runtime_instructions_and_installation_ownership(self):
        from test_dual_distribution import core_fixture, installer
        from dual_distribution import project_files
        from runtime_doctor import check
        from v2_contract import canonical, sha
        old = project_files(core_fixture("1.1.1"), "synthetic-old", "synthetic")
        ownership = {}
        for name, raw in old.items():
            write(self.root, name, raw)
            if name in installer.BLOCK_FILES:
                _, block, _ = installer.block_parts(raw)
                ownership[name] = {"sha256": sha(block), "kind": "block", "created_file": False}
            else:
                ownership[name] = {"sha256": sha(raw), "kind": "file"}
        old_lock = json.loads(old[".lks-sdd/distribution-lock.json"])
        receipt = canonical({"schema_version": "1.0", "host": "copilot", "version": "1.1.1",
            "channel": "synthetic", "runtime_digest": old_lock["runtime_digest"], "files": ownership})
        write(self.root, ".lks-sdd/installation.json", receipt)
        original_agents = b"# Personalizacion preservada\n\n" + old["AGENTS.md"] + b"\nRegla propia.\n"
        write(self.root, "AGENTS.md", original_agents)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            core = core_fixture("2.0.0-rc.1")
            core["package-integrity.json"] = canonical({"files": [
                {"path": p, "sha256": sha(b), "size": len(b)} for p, b in core.items()]})
            for name, raw in core.items():
                write(target, name, raw)
            proposed, _ = plan(self.root, target_runtime=target)
            outcome = migrate(self.root, proposed["preview_hash"], target_runtime=target)
        self.assertEqual(check(self.root)["status"], "valid", check(self.root))
        self.assertEqual(migration_status(self.root)["status"], "migration-complete")
        self.assertTrue((self.root / old_lock["runtime"]).is_dir())
        for name, raw in old.items():
            if name.startswith(old_lock["runtime"] + "/"):
                self.assertEqual((self.root / name).read_bytes(), raw)
        updated = json.loads(read_bytes(self.root, ".lks-sdd/installation.json"))
        self.assertEqual(updated["preserved_historical_runtime"], old_lock["runtime"])
        self.assertFalse(any(p.startswith(old_lock["runtime"] + "/") for p in updated["files"]))
        # A later uninstall can reconcile ownership, without deleting historical runtime or personal text.
        removal = installer.plan(None, self.root, "copilot", remove=True)
        self.assertFalse(any(c["path"].startswith(old_lock["runtime"] + "/") for c in removal["changes"]))
        self.assertIn(b"Personalizacion preservada", read_bytes(self.root, "AGENTS.md"))
        recover(self.root, proposed["preview_hash"], rollback=True, receipt=outcome["receipt"])
        self.assertEqual(read_bytes(self.root, ".lks-sdd/installation.json"), receipt)
        self.assertEqual(read_bytes(self.root, "AGENTS.md"), original_agents)
        self.assertEqual(check(self.root)["status"], "valid", check(self.root))

    def test_pending_visual_request_blocks_migration_without_writes(self):
        write(self.root, ".lks-sdd/handoffs/visual/VH-synthetic/request.json", "{}")
        self.assertEqual(diagnose(self.root)["status"], "blocked")
        with self.assertRaises(ContractError):
            plan(self.root)

    def test_migration_archives_linked_external_attachment_with_navigable_tree(self):
        path = DOCS + "/01-context/custom.md"
        write(self.root, path, "# Custom\n\n[Operational rule](../../../design/rule.txt)\n")
        write(self.root, "design/rule.txt", "Never erase historical orders.")
        proposed, _ = plan(self.root)
        migrate(self.root, proposed["preview_hash"])
        archived = proposed["mapping"][path]["archive"]
        target = (self.root / archived).parent / "../../../design/rule.txt"
        self.assertEqual(target.resolve().read_text(), "Never erase historical orders.")

    def test_open_legacy_authority_and_execution_are_preserved_but_not_reauthorized(self):
        from eval_support import authorize_implementation, run_json, IMPLEMENT_SCRIPT
        materialize_ready_increment(self.root)
        authorize_implementation(self.root)
        args = [str(self.root), "--increment", "INC-001", "--task", "TASK-001"]
        _, proposed = run_json(IMPLEMENT_SCRIPT, *args, "--dry-run")
        _, prepared = run_json(IMPLEMENT_SCRIPT, *args, "--apply", "--authorize", "--preview-hash", proposed["preview_hash"])
        self.assertTrue(prepared["changed"])
        proposed, _ = plan(self.root)
        migrate(self.root, proposed["preview_hash"])
        model = load(self.root)
        self.assertTrue(model.by_kind("execution"))
        self.assertTrue(all(e.meta["state"] == "reconciliation-required" for e in model.by_kind("execution")))
        self.assertTrue(all(e.meta["state"] == "revoked" for e in model.by_kind("authorization")))
        self.assertTrue(model.elements["TASK-001"].meta["reconciliation_required"])
        self.assertEqual(model.elements["EXEC-001"].meta["legacy_index_record"]["authorization_id"], "AUTH-001")
        self.assertIn("BIND-001", model.elements)
        self.assertEqual(model.elements["BIND-001"].meta["legacy_index_record"]["profile_id"], "API-FASTAPI-STATELESS-OCI")
        self.assertEqual(model.elements["CKPT-001"].targets("execution"), {"EXEC-001"})
        self.assertTrue(any(e.meta.get("legacy_frontmatter") for e in model.by_kind("legacy")))


if __name__ == "__main__":
    unittest.main()
