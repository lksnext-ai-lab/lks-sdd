"""Real interrupted journal writes at each stage of result composition."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import test_work_operations as support
from v3_contract import load
from v3_storage import apply as apply_packet, recover
from v4_work_operations import run
from test_v4_cli_presentation import snapshot


class WorkOperationRecoveryTests(unittest.TestCase):
    setUpClass = classmethod(support.WorkOperationsTests.setUpClass.__func__)
    setUp = support.WorkOperationsTests.setUp
    basis = support.WorkOperationsTests.basis
    data = support.WorkOperationsTests.data
    start = support.WorkOperationsTests.start
    proof = support.WorkOperationsTests.proof
    records = support.WorkOperationsTests.records

    def test_native_recovery_of_real_partial_write_in_every_result_stage(self):
        for boundary in range(1, 5):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temp:
                original = self.root; self.root = Path(temp) / 'c'; shutil.copytree(self.case.root, self.root)
                try:
                    data = self.records(); calls = 0
                    def fault(root, packet, key, **kwargs):
                        nonlocal calls
                        calls += 1
                        return apply_packet(root, packet, key, **kwargs,
                                            **({'interrupt_after': 1} if calls == boundary else {}))
                    with patch('v3_storage.apply', side_effect=fault):
                        failed = run(self.root, 'work-record-results', data, apply=True)
                    self.assertEqual('partial', failed['status'], failed)
                    self.assertEqual(boundary - 1, len(failed['effects']))
                    self.assertEqual('recover-or-rollback', failed['recovery']['action'])
                    # Composition must not silently finish a pending material write.
                    self.assertEqual('partial', run(self.root, 'work-record-results', data, apply=True)['status'])
                    recover(self.root, failed['recovery']['preview_hash'])
                    completed = run(self.root, 'work-record-results', data, apply=True)
                    self.assertEqual('completed', completed['status'], completed)
                    self.assertEqual(4, len(completed['effects']))
                    model = load(self.root).require_valid()
                    self.assertEqual(4, len(model.by_kind('execution')))
                    self.assertEqual(1, len(model.by_kind('evidence')))
                    before = snapshot(self.root)
                    self.assertEqual('completed', run(self.root, 'work-record-results', data, apply=True)['status'])
                    self.assertEqual(before, snapshot(self.root))
                finally:
                    self.root = original

    def test_explicit_rollback_requires_new_intent_and_keeps_code(self):
        data = self.records(); code = (self.root / 'app.py').read_bytes()
        def fault(root, packet, key, **kwargs):
            return apply_packet(root, packet, key, interrupt_after=1, **kwargs)
        with patch('v3_storage.apply', side_effect=fault):
            value = run(self.root, 'work-record-results', data, apply=True)
        recover(self.root, value['recovery']['preview_hash'], rollback=True)
        before = snapshot(self.root); again = run(self.root, 'work-record-results', data, apply=True)
        self.assertNotEqual('completed', again['status'])
        self.assertEqual(before, snapshot(self.root)); self.assertEqual(code, (self.root / 'app.py').read_bytes())
        # Exact rollback can restore the original basis; explicitly distinguish
        # the new intent instead of silently recycling the rolled-back one.
        fresh = run(self.root, 'work-record-results', self.data('work-record-results',
            reason='Nuevo intento tras reversión explícita', evidence=[self.proof()]), apply=True)
        self.assertEqual('completed', fresh['status'], fresh)


if __name__ == '__main__': unittest.main()
