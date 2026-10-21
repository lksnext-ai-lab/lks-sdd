"""Focused adversarial/product checks for the experimental v5 vertical slice."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import sdd


FACTS = dict(implementation="Código de fixture modificado", verification="Prueba local superada",
             integration="not-run", publication="not-run", deployment="not-run", acceptance="pending")


def meta(kind, ident, **values):
    return {"format": "sdd/5-prototype", "kind": kind, "id": ident, **values}


def put(root, name, raw):
    path = sdd.path_at(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw if isinstance(raw, bytes) else raw.encode())


def fixture(root, task="T-001", units=None):
    if not (root / "product.py").exists():
        put(root, "product.py", "def visible(value):\n    return bool(value)\n")
        put(root, "test_product.py", "from product import visible\nassert visible('value')\nassert not visible('')\n")
        put(root, "project-policy.md", "Verificar comportamiento afectado; no despliegue implícito.\n")
        put(root, "README.md", "Proyecto de prueba\n")
        put(root, sdd.unit_path("acceso"), sdd.document(meta("unit", "acceso", depends_on=[]),
                                                       "# Acceso\nEl vacío no es un valor visible."))
    task_meta = meta("task", task, units=units or ["acceso"], policies=["project-policy.md"],
                     owner="fixture-owner", authority={"actor": "fixture-owner", "source": "test-only",
                                                       "scope": ["implement", "consolidate"]})
    put(root, sdd.task_path(task, "tarea"), sdd.document(task_meta,
        "# Corrección de visibilidad\nC1: valor presente visible; valor vacío oculto."))
    plan_meta = meta("plan", task, state="preparado", next="Implementar y ejecutar C1",
                     bases={sdd.unit_path("acceso"): sdd.digest(sdd.read(root, sdd.unit_path("acceso")))},
                     checks={"C1": {"criteria": ["C1"], "risk": "Valor vacío mostrado",
                                    "inputs": ["product.py", "test_product.py"],
                                    "argv": [sys.executable, "-B", "test_product.py"],
                                    "environment": "fixture-local"}})
    put(root, sdd.task_path(task, "plan"), sdd.document(plan_meta,
        "# Plan\nModificar producto; ejecutar C1; consolidar resultado.\nNo requiere entrega externa."))
    return task_meta, plan_meta


def update(root, task="T-001", extra="Los valores presentes son visibles."):
    m, b, _ = sdd.current(root, sdd.unit_path("acceso"))
    return {"acceso": sdd.document(m, b + "\n" + extra)}


def legacy_fixture(root):
    name = "docs/lks-sdd/task.md"
    raw = ('---\nschema_version: "3.1"\n---\n\n<!-- lks-sdd: ' +
           json.dumps({"uid": "legacy-1", "id": "TASK-1", "kind": "task", "state": "ready"}) +
           ' -->\n# Tarea\nConservar permisos y C1.\n<!-- /lks-sdd -->\n').encode()
    put(root, name, raw)
    path = ".sdd-work/recovery/source.zip"
    target = sdd.path_at(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as z:
        z.writestr(name, raw)
    recovery = {"kind": "zip", "path": path, "sha256": sdd.digest(target.read_bytes()),
                "expires": "2026-11-20", "owner": "fixture-only"}
    output = {sdd.task_path("T-migrated", "tarea"):
              sdd.document(meta("task", "T-migrated", units=[], owner="pending"), "# Tarea\nConservar permisos y C1.")}
    output[sdd.task_path("T-migrated", "plan")] = sdd.document(
        meta("plan", "T-migrated", state="preparado", delivery=FACTS), "# Plan\nComprobar C1; entrega pendiente.")
    return name, output, recovery


class VerticalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sdd-v5-test-")
        self.root = Path(self.tmp.name)
        fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, task="T-001"):
        return sdd.current(self.root, sdd.task_path(task, "plan"))

    def edit_plan(self, fn):
        m, b, _ = self.plan()
        fn(m)
        put(self.root, sdd.task_path("T-001", "plan"), sdd.document(m, b))

    def test_complete_flow_has_two_task_documents_and_separate_delivery_facts(self):
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")
        revised = update(self.root)
        self.assertEqual(sdd.close(self.root, "T-001", revised, FACTS)["status"], "applied")
        self.assertEqual(sdd.close(self.root, "T-001", revised, FACTS)["status"], "unchanged")
        self.assertEqual(sorted(p.name for p in (self.root / "docs/sdd/tareas/T-001").iterdir()),
                         ["plan.md", "tarea.md"])
        self.assertEqual(self.plan()[0]["delivery"]["deployment"], "not-run")
        self.assertEqual(self.plan()[0]["delivery"]["acceptance"], "pending")
        self.assertFalse((self.root / ".sdd-work/journal.json").exists())

    def test_reuses_passed_result_and_document_only_change(self):
        sdd.check_task(self.root, "T-001", "C1")
        before = self.plan()[2]
        put(self.root, "README.md", "Documentación actualizada\n")
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "reused")
        self.assertEqual(before, self.plan()[2])

    def test_changed_code_invalidates_and_failure_blocks_close(self):
        sdd.check_task(self.root, "T-001", "C1")
        put(self.root, "product.py", "def visible(value):\n    return True\n")
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "failed")
        self.assertTrue(self.plan()[0]["temporaries"])
        with self.assertRaises(ValueError):
            sdd.close(self.root, "T-001", update(self.root), FACTS)

    def test_policy_and_environment_changes_invalidate(self):
        sdd.check_task(self.root, "T-001", "C1")
        put(self.root, "project-policy.md", "Nueva condición de verificación\n")
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")
        self.edit_plan(lambda m: m["checks"]["C1"].update(environment="different-environment"))
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")

    def test_added_and_deleted_glob_inputs_invalidate(self):
        self.edit_plan(lambda m: m["checks"]["C1"]["inputs"].append("config/*.json"))
        sdd.check_task(self.root, "T-001", "C1")
        put(self.root, "config/new.json", "{}")
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")
        (self.root / "config/new.json").unlink()
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")

    def test_expired_results_not_reused(self):
        self.edit_plan(lambda m: m["checks"]["C1"].update(max_age_seconds=0))
        sdd.check_task(self.root, "T-001", "C1")
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")

    def test_scope_change_does_not_reuse_acceptance(self):
        sdd.check_task(self.root, "T-001", "C1")
        name = sdd.task_path("T-001", "tarea")
        m, b, _ = sdd.current(self.root, name)
        put(self.root, name, sdd.document(m, b + "\nC2: nueva condición."))
        self.assertEqual(sdd.check_task(self.root, "T-001", "C1")["status"], "passed")

    def test_context_depends_on_current_scope_not_history(self):
        baseline = sdd.context(self.root, "T-001")
        for count in (10, 100):
            for i in range(count):
                put(self.root, f"docs/sdd/tareas/old-{i}/plan.md", "irrelevant history" * 100)
            self.assertEqual(sdd.context(self.root, "T-001"), baseline)

    def test_transitive_dependencies_and_cycles_are_read_once(self):
        name = sdd.unit_path("acceso")
        m, b, _ = sdd.current(self.root, name)
        m["depends_on"] = ["permisos"]
        put(self.root, name, sdd.document(m, b))
        put(self.root, sdd.unit_path("permisos"),
            sdd.document(meta("unit", "permisos", depends_on=["acceso"]), "No ampliar permisos."))
        self.assertEqual(sdd.context(self.root, "T-001")["files_read"], 5)

    def test_missing_dependency_is_visible(self):
        name = sdd.unit_path("acceso")
        m, b, _ = sdd.current(self.root, name)
        m["depends_on"] = ["missing"]
        put(self.root, name, sdd.document(m, b))
        with self.assertRaises(ValueError):
            sdd.context(self.root, "T-001")

    def test_interrupted_close_recovers_without_repeating_test(self):
        sdd.check_task(self.root, "T-001", "C1")
        timestamp = self.plan()[0]["results"]["C1"]["finished"]
        with self.assertRaises(InterruptedError):
            sdd.close(self.root, "T-001", update(self.root), FACTS, interrupt_after=1)
        self.assertEqual(sdd.resume(self.root)["status"], "applied")
        self.assertEqual(self.plan()[0]["results"]["C1"]["finished"], timestamp)
        self.assertEqual(self.plan()[0]["state"], "cerrado")
        self.assertEqual(sdd.resume(self.root)["status"], "unchanged")

    def test_recovery_preserves_later_foreign_edit(self):
        sdd.check_task(self.root, "T-001", "C1")
        with self.assertRaises(InterruptedError):
            sdd.close(self.root, "T-001", update(self.root), FACTS, interrupt_after=1)
        put(self.root, sdd.unit_path("acceso"), "edición ajena")
        with self.assertRaises(sdd.Conflict):
            sdd.resume(self.root)
        self.assertEqual(sdd.read(self.root, sdd.unit_path("acceso")), "edición ajena".encode())

    def test_recovery_rejects_new_test_inputs(self):
        sdd.check_task(self.root, "T-001", "C1")
        with self.assertRaises(InterruptedError):
            sdd.close(self.root, "T-001", update(self.root), FACTS, interrupt_after=1)
        put(self.root, "product.py", "changed after interruption")
        with self.assertRaises(sdd.Conflict):
            sdd.resume(self.root)
        self.assertNotEqual(self.plan()[0]["state"], "cerrado")

    def test_second_local_writer_is_rejected(self):
        with sdd.locked(self.root):
            with self.assertRaises(sdd.Conflict):
                sdd.apply(self.root, {}, {})

    def test_stale_plan_preserved_before_any_write(self):
        name = sdd.task_path("T-001", "plan")
        raw = sdd.read(self.root, name)
        put(self.root, name, raw + b"\nforeign edit\n")
        unit = sdd.unit_path("acceso")
        original = sdd.read(self.root, unit)
        with self.assertRaises(sdd.Conflict):
            sdd.apply(self.root, {unit: original + b"\nchanged\n", name: raw},
                      {unit: sdd.digest(original), name: sdd.digest(raw)})
        self.assertEqual(sdd.read(self.root, unit), original)

    def test_two_tasks_reconcile_shared_unit_without_lost_changes(self):
        fixture(self.root, "T-002")
        sdd.check_task(self.root, "T-001", "C1")
        sdd.check_task(self.root, "T-002", "C1")
        stale = update(self.root, extra="Cambio segundo.")
        sdd.close(self.root, "T-001", update(self.root, extra="Cambio primero."), FACTS)
        with self.assertRaises(sdd.Conflict):
            sdd.close(self.root, "T-002", stale, FACTS)
        name = sdd.task_path("T-002", "plan")
        m, b, _ = sdd.current(self.root, name)
        m["bases"][sdd.unit_path("acceso")] = sdd.digest(sdd.read(self.root, sdd.unit_path("acceso")))
        put(self.root, name, sdd.document(m, b))
        sdd.close(self.root, "T-002", update(self.root, extra="Cambio segundo."), FACTS)
        raw = sdd.read(self.root, sdd.unit_path("acceso")).decode()
        self.assertIn("Cambio primero.", raw)
        self.assertIn("Cambio segundo.", raw)

    def test_cleanup_only_owned_unchanged_temporaries(self):
        put(self.root, ".sdd-work/tmp/owned.log", "owned")
        put(self.root, "user.log", "keep")
        self.edit_plan(lambda m: m.update(temporaries={".sdd-work/tmp/owned.log": sdd.digest(b"owned")}))
        sdd.check_task(self.root, "T-001", "C1")
        sdd.close(self.root, "T-001", update(self.root), FACTS)
        self.assertFalse((self.root / ".sdd-work/tmp/owned.log").exists())
        self.assertEqual((self.root / "user.log").read_text(), "keep")

    def test_changed_temporary_is_not_removed(self):
        put(self.root, ".sdd-work/tmp/owned.log", "new foreign content")
        self.edit_plan(lambda m: m.update(temporaries={".sdd-work/tmp/owned.log": sdd.digest(b"old")}))
        sdd.check_task(self.root, "T-001", "C1")
        with self.assertRaises(sdd.Conflict):
            sdd.close(self.root, "T-001", update(self.root), FACTS)
        self.assertTrue((self.root / ".sdd-work/tmp/owned.log").exists())

    def test_unowned_cleanup_is_rejected(self):
        put(self.root, "user.log", "keep")
        self.edit_plan(lambda m: m.update(temporaries={"user.log": sdd.digest(b"keep")}))
        sdd.check_task(self.root, "T-001", "C1")
        with self.assertRaises(ValueError):
            sdd.close(self.root, "T-001", update(self.root), FACTS)

    def test_missing_authority_does_not_execute(self):
        name = sdd.task_path("T-001", "tarea")
        m, b, _ = sdd.current(self.root, name)
        m.pop("authority")
        put(self.root, name, sdd.document(m, b))
        with self.assertRaises(ValueError):
            sdd.check_task(self.root, "T-001", "C1")

    def test_binary_evidence_does_not_decode_utf8(self):
        put(self.root, "evidence.zip", b"PK\x03\x04\xff\xfe\x00")
        result = sdd.artifact(self.root, "evidence.zip")
        self.assertEqual(result["media_type"], "application/zip")
        self.assertEqual(result["bytes"], 7)

    def test_traversal_and_absolute_path_rejected(self):
        for name in ("../foreign", "C:/foreign", "/foreign", "docs/../../foreign", "docs\\foreign"):
            with self.assertRaises(ValueError):
                sdd.path_at(self.root, name)

    def test_pending_transaction_blocks_new_write(self):
        sdd.check_task(self.root, "T-001", "C1")
        with self.assertRaises(InterruptedError):
            sdd.close(self.root, "T-001", update(self.root), FACTS, interrupt_after=1)
        with self.assertRaises(sdd.Conflict):
            sdd.apply(self.root, {}, {})

    def test_cli_check_and_context_work_without_wrapper(self):
        cli = Path(sdd.__file__)
        for command in (["check", "T-001", "C1"], ["context", "T-001"]):
            run = subprocess.run([sys.executable, "-B", "-X", "utf8", str(cli), str(self.root), *command],
                                 capture_output=True, check=True)
            self.assertIsInstance(json.loads(run.stdout), dict)

    def preview(self):
        name, targets, recovery = legacy_fixture(self.root)
        return sdd.migration_preview(self.root, [name], targets,
                                     resolution={"legacy-1": "T-migrated: preserve pending status and C1"},
                                     recovery_reference=recovery)

    def test_migration_removes_only_explicit_sources_and_retains_recovery(self):
        preview = self.preview()
        put(self.root, "docs/other.md", "ajeno")
        sdd.migrate(self.root, preview, preview["preview"])
        self.assertFalse((self.root / "docs/lks-sdd/task.md").exists())
        self.assertTrue((self.root / "docs/sdd/tareas/T-migrated/tarea.md").exists())
        self.assertEqual((self.root / "docs/other.md").read_text(), "ajeno")
        self.assertTrue((self.root / preview["recovery"]["path"]).exists())

    def test_migration_interrupted_and_resumed(self):
        preview = self.preview()
        with self.assertRaises(InterruptedError):
            sdd.migrate(self.root, preview, preview["preview"], interrupt_after=1)
        sdd.resume(self.root)
        self.assertFalse((self.root / "docs/lks-sdd/task.md").exists())

    def test_migration_unresolved_meaning_preserves_sources(self):
        name, targets, recovery = legacy_fixture(self.root)
        with self.assertRaises(ValueError):
            sdd.migration_preview(self.root, [name], targets, resolution={}, recovery_reference=recovery)
        self.assertTrue((self.root / name).exists())

    def test_migration_stale_source_or_modified_preview_rejected(self):
        preview = self.preview()
        put(self.root, "docs/lks-sdd/task.md", "modified")
        with self.assertRaises(sdd.Conflict):
            sdd.migrate(self.root, preview, preview["preview"])
        preview = self.preview()
        preview["changes"]["docs/lks-sdd/task.md"] = b"tampered"
        with self.assertRaises(ValueError):
            sdd.migrate(self.root, preview, preview["preview"])

    def test_missing_recovery_is_not_a_successful_migration(self):
        preview = self.preview()
        (self.root / preview["recovery"]["path"]).unlink()
        with self.assertRaises(FileNotFoundError):
            sdd.migrate(self.root, preview, preview["preview"])
        self.assertTrue((self.root / "docs/lks-sdd/task.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
