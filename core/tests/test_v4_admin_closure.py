"""Focused administrative guards; complete journeys live in the stage runner."""
import shutil
import json
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from presentation_test_support import present
from test_v3_workflow import ProjectFixture, commit_packet
from v3_approval import task_authority
from v3_contract import ContractError, load
from v3_lifecycle import revoke
from v3_storage import apply, recover
from v3_workflow import plan_for, state, transition
from run_v4_administrative_case import reserve_full_journey


class JourneyReservationTests(unittest.TestCase):
    def test_failed_prelaunch_reservation_cannot_be_retried(self):
        for previous in ({"full_journeys_started": 1, "actual_worker_starts": 0},
                         {"full_journeys_started": 0, "actual_worker_starts": 1}):
            with self.subTest(previous=previous), tempfile.TemporaryDirectory() as directory:
                op = Path(directory); record = op / "authorization.json"
                record.write_text(json.dumps(previous), encoding="utf-8")
                (op / "journey-admission.json").write_text("{}", encoding="utf-8")
                before = record.read_bytes()
                with self.assertRaisesRegex(RuntimeError, "consumed"):
                    reserve_full_journey(op)
                self.assertEqual(before, record.read_bytes())

    def test_reservation_requires_admission_and_is_durable_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            op = Path(directory); record = op / "authorization.json"
            record.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Admission"):
                reserve_full_journey(op)
            self.assertEqual({}, json.loads(record.read_bytes()))
            admission = op / "journey-admission.json"
            digest = hashlib.sha256((ROOT / "tests/run_v4_administrative_case.py").read_bytes()).hexdigest()
            for invalid in ({}, {"status": "admitted", "execution_runner_sha256": "0" * 64}):
                admission.write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "Admission"):
                    reserve_full_journey(op)
                self.assertEqual({}, json.loads(record.read_bytes()))
            admission.write_text(json.dumps({"status": "admitted", "execution_runner_sha256": digest}), encoding="utf-8")
            reserve_full_journey(op)
            self.assertEqual(1, json.loads(record.read_bytes())["full_journeys_started"])
            with self.assertRaisesRegex(RuntimeError, "consumed"):
                reserve_full_journey(op)


class AdministrativeGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ProjectFixture("runTest")
        cls.fixture.setUp()
        cls.addClassCleanup(cls.fixture.doCleanups)
        cls.fixture.plan()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v4-admin-guard-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "consumer"
        shutil.copytree(self.fixture.root, self.root)
        self.actor, self.task = self.fixture.actor, self.fixture.task

    def advance(self, action):
        return present(transition, self.root, self.actor, self.task, action,
                       "Comprobación administrativa sintética autorizada")

    def documents(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in (self.root / "docs/lks-sdd").rglob("*") if p.is_file()}

    def test_stale_code_inventory_cannot_apply_cancellation(self):
        commit_packet(self.root, self.advance("start"))
        packet = self.advance("cancel")
        (self.root / "app.py").write_bytes(b"later independent code\n")
        before = self.documents()
        with self.assertRaises(ContractError): commit_packet(self.root, packet)
        self.assertEqual(before, self.documents())
        self.assertEqual("in-progress", state(load(self.root), load(self.root).get(self.task)))
        self.assertFalse((self.root / ".lks-sdd/transaction.json").exists())

    def test_revocation_invalidates_prepared_start(self):
        packet = self.advance("start")
        model = load(self.root); task = model.get(self.task)
        authority = task_authority(model, task, plan_for(model, task), "execution")["decisions"]
        commit_packet(self.root, present(revoke, self.root, self.actor, authority[0],
                                        "Retiro el permiso antes de aplicar el inicio preparado"))
        before = self.documents()
        with self.assertRaises(ContractError): commit_packet(self.root, packet)
        self.assertEqual(before, self.documents())
        self.assertNotEqual("in-progress", state(load(self.root), load(self.root).get(self.task)))

    def test_interrupted_cancellation_rolls_back_and_preserves_later_work(self):
        commit_packet(self.root, self.advance("start"))
        packet = self.advance("cancel"); key = packet["preview"]["preview_hash"]
        with self.assertRaises(InterruptedError): apply(self.root, packet, key, interrupt_after=1)
        self.assertTrue((self.root / ".lks-sdd/transaction.json").exists())
        later = self.root / "independent.txt"; later.write_bytes(b"preserve later work")
        recover(self.root, key, rollback=True)
        model = load(self.root).require_valid()
        self.assertEqual("in-progress", state(model, model.get(self.task)))
        self.assertEqual(b"preserve later work", later.read_bytes())
        self.assertFalse((self.root / ".lks-sdd/transaction.json").exists())


if __name__ == "__main__": unittest.main()
