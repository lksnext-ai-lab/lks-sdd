"""Activity transport, real signals and durable interruption boundaries."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import v4_activity as activity
from v3_cli import main


class ActivityTests(unittest.TestCase):
    def test_unread_native_activity_pipe_does_not_block_exit(self):
        script = """import sys,time,json
sys.path.insert(0,'scripts')
import v4_activity as activity
activity.INTERVAL=.001 # fault injection: fill the pipe without a ten-minute wait
with activity.session('work-prepare',activity=True):time.sleep(.5)
print(json.dumps({'status':'finished'}))
"""
        child = subprocess.Popen([sys.executable,'-B','-X','utf8','-c',script],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        self.assertEqual(0, child.wait(timeout=5))  # deliberately do not drain stderr
        stdout,stderr=child.communicate(timeout=2)
        self.assertEqual('finished',json.loads(stdout)['status'])
        self.assertLessEqual(len(stderr),16384)

    def test_disabled_and_brief_do_not_wait_or_write_sources(self):
        stream = io.StringIO(); start = time.monotonic()
        with activity.session('work-prepare', stream=stream): activity.phase('prepare')
        self.assertEqual('', stream.getvalue())
        self.assertLess(time.monotonic() - start, .1)
        with activity.session('work-prepare', activity=True, stream=stream): pass
        self.assertLess(time.monotonic() - start, .2)

    def test_real_cadence_without_tty_and_bounded_volume(self):
        class Stream(io.StringIO):
            def write(self, value):
                stamps.append(time.monotonic()); return super().write(value)
        stamps = []; stream = Stream(); start = time.monotonic()
        with activity.session('work-prepare', activity=True, stream=stream): time.sleep(3.25)
        self.assertGreaterEqual(len(stamps), 3)
        self.assertLessEqual(stamps[0] - start, 1)
        self.assertTrue(all(1 <= b-a <= 2 for a,b in zip(stamps, stamps[1:])))
        self.assertTrue(all(len(line.encode()) <= 1024 for line in stream.getvalue().splitlines(True)))
        controller = activity.Controller(io.StringIO(), activity=True)
        for _ in range(2000): controller.emit()
        self.assertLessEqual(controller.bytes, 16384)
        self.assertFalse(controller.emit())
        self.assertTrue(all('percent' not in line and 'eta' not in line for line in stream.getvalue().splitlines()))

    def test_closed_channel_does_not_fail_operation(self):
        stream = io.StringIO(); stream.close()
        with activity.session('work-prepare', activity=True, stream=stream): activity.checkpoint()
        self.assertFalse(any(t.name == 'lks-sdd-activity' for t in __import__('threading').enumerate()))

    def test_real_sigint_cpu_checkpoint_and_handler_restoration(self):
        previous = signal.getsignal(signal.SIGINT)
        with activity.session('work-prepare') as controller:
            start = time.monotonic(); signal.raise_signal(signal.SIGINT)
            with self.assertRaises(activity.OperationInterrupted) as raised:
                while True: activity.checkpoint()
            self.assertLess(time.monotonic() - start, 2)
            self.assertLess(raised.exception.interruption['checkpoint_seconds'], 5)
            self.assertFalse(raised.exception.interruption['business_cancel'])
        self.assertIs(previous, signal.getsignal(signal.SIGINT))
        activity.checkpoint()  # no stale cancellation in a later invocation

    def test_native_write_defers_until_receipt_boundary(self):
        with activity.session('work-continue') as controller:
            activity.phase('apply')
            with activity.defer():
                signal.raise_signal(signal.SIGINT)
                activity.checkpoint()
                effect = {'receipt': 'durable'}
            self.assertEqual('durable', effect['receipt'])
            with self.assertRaises(activity.OperationInterrupted): activity.checkpoint()
            activity.checkpoint()  # inspection/final result can complete

    def test_stdout_json_compatible_and_operational_with_activity(self):
        for view in ('compatible', 'operational'):
            outputs = []
            for enabled in (False, True):
                out = io.StringIO(); err = io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), patch('v3_cli.execute', return_value={'status':'ready','literal':'Obligación completa'}):
                    code = main(['work-prepare', str(ROOT), '--json', '--view', view, *(['--activity'] if enabled else [])])
                self.assertEqual(0, code); outputs.append(json.loads(out.getvalue()))
                if enabled: self.assertTrue(err.getvalue())
                else: self.assertEqual('', err.getvalue())
            self.assertEqual(*outputs)

    def test_public_cli_signal_result_is_single_json_and_not_success(self):
        script = """import sys,signal
sys.path.insert(0,'scripts')
from unittest.mock import patch
import v3_cli
from v4_activity import checkpoint
def stop(*a,**k):
 signal.raise_signal(signal.SIGINT); checkpoint()
with patch('v3_cli.execute',side_effect=stop):
 sys.exit(v3_cli.main(['work-prepare','.', '--json','--activity']))
"""
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script], cwd=ROOT, capture_output=True, timeout=15)
        self.assertEqual(130, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual('interrupted', value['status'])
        self.assertFalse(value['interruption']['business_cancel'])

    def test_capture_interruption_is_not_swallowed_as_success(self):
        import diagnostic_capture
        out = io.StringIO()
        class Capture:
            def store(self, *a, **k):
                signal.raise_signal(signal.SIGINT); activity.checkpoint()
        with contextlib.redirect_stdout(out), activity.session('work-prepare'):
            with self.assertRaises(activity.OperationInterrupted): diagnostic_capture.emit({'status':'ready'}, {}, Capture())
        self.assertEqual('', out.getvalue())

    def test_stop_after_capture_commit_retains_entry_and_single_failure(self):
        import diagnostic_capture
        out = io.StringIO(); committed = []
        class Capture:
            run_id = 'synthetic-run'
            def store(self, *a, **k):
                committed.append('entry'); signal.raise_signal(signal.SIGINT)
                return '{"status":"completed"}\n'
        result = {'format':'lks-sdd-operation-result/1','status':'completed', 'effects':[{'receipt':'real-receipt'}], 'writes':['one']}
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(out), patch('v3_cli.execute', return_value=result), patch('diagnostic_capture.Capture', return_value=Capture()):
            code = main(['work-continue', str(ROOT), '--capture-dir', temp, '--json'])
        value = json.loads(out.getvalue())
        self.assertEqual(3, code); self.assertEqual('partial', value['status'])
        self.assertEqual(result['effects'], value['effects']); self.assertEqual(['entry'], committed)
        self.assertEqual('inspection-required', value['diagnostic_capture']['status'])

    def test_activity_local_cpu_and_wall_overhead(self):
        def sample(enabled):
            stream = io.StringIO(); wall = time.perf_counter(); cpu = time.process_time()
            with activity.session('work-prepare', activity=enabled, stream=stream):
                checksum = 0
                for number in range(100000):
                    activity.checkpoint(); checksum = (checksum + number) % 1000003
                self.assertEqual(935003, checksum)
            return time.perf_counter()-wall, time.process_time()-cpu, len(stream.getvalue().encode())
        off = sample(False); on = sample(True)
        self.assertLessEqual(on[0] - off[0], max(.1, .05 * off[0]))
        self.assertLessEqual(on[1] - off[1], max(.1, .05 * off[1]))
        self.assertLessEqual(on[2], 16384)
        if os.environ.get('LKS_ACTIVITY_EVIDENCE'):
            Path(os.environ['LKS_ACTIVITY_EVIDENCE']).write_text(json.dumps({'off':off,'on':on,
                'wall_delta_seconds':on[0]-off[0],'cpu_delta_seconds':on[1]-off[1],
                'scope':'local signal component; not whole-task or billed-token savings'}), encoding='utf8')


import test_work_operations as support
from v4_work_operations import run
from v3_storage import apply as apply_packet, recover
from v3_contract import load
from test_v4_cli_presentation import snapshot


class ActivityJournalTests(unittest.TestCase):
    setUpClass = classmethod(support.WorkOperationsTests.setUpClass.__func__)
    setUp = support.WorkOperationsTests.setUp
    basis = support.WorkOperationsTests.basis
    data = support.WorkOperationsTests.data
    start = support.WorkOperationsTests.start
    proof = support.WorkOperationsTests.proof
    records = support.WorkOperationsTests.records

    def test_cold_pinned_public_launcher_activity_preserves_preview(self):
        data = self.data(); source = self.out/'input.json'; source.write_text(json.dumps(data), encoding='utf8')
        lock = json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        command = [sys.executable, '-B', '-X', 'utf8', str(self.root/lock['runtime']/'scripts/lks_sdd.py'),
                   'v3','work-continue',str(self.root),'--input',str(source),'--activity','--json','--view','operational']
        before = snapshot(self.root)
        completed = subprocess.run(command, capture_output=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stdout.decode(errors='replace')[:2000])
        self.assertEqual('ready', json.loads(completed.stdout)['status'])
        signals = [json.loads(line) for line in completed.stderr.splitlines()]
        self.assertTrue(signals); self.assertEqual({'activity'}, set(signals[0]))
        self.assertEqual(before, snapshot(self.root))

    def test_real_signal_between_result_stages_resumes_without_duplication(self):
        data = self.records(); calls = 0
        with activity.session('work-record-results'):
            def interrupted(*a, **k):
                nonlocal calls
                calls += 1
                if calls == 2: signal.raise_signal(signal.SIGINT)
                return apply_packet(*a, **k)
            with patch('v3_storage.apply', side_effect=interrupted):
                value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('partial', value['status'], value)
        self.assertEqual(2, len(value['effects'])); self.assertTrue(value['interruption']['requested'])
        value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('completed', value['status'], value); self.assertEqual(4, len(value['effects']))
        model = load(self.root).require_valid()
        self.assertEqual(4, len(model.by_kind('execution'))); self.assertEqual(1, len(model.by_kind('evidence')))

    def test_interruption_before_first_effect_is_read_only(self):
        import v4_work_operations as operations
        data = self.data(); before = snapshot(self.root); original = operations._prepare
        with activity.session('work-continue') as controller:
            def interrupted(*a):
                controller.request(); return original(*a)
            with patch.object(operations, '_prepare', side_effect=interrupted):
                value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('blocked', value['status'], value)
        self.assertTrue(value['interruption']['requested']); self.assertEqual([], value['effects'])
        self.assertEqual(before, snapshot(self.root))

    def test_interruption_after_durable_effect_exact_retry_and_later_edit(self):
        data = self.data(); code = (self.root/'app.py').read_bytes()
        with activity.session('work-continue') as controller:
            def interrupted(*a, **k):
                controller.request(); return apply_packet(*a, **k)
            with patch('v3_storage.apply', side_effect=interrupted):
                value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('partial', value['status'], value)
        self.assertEqual(1, len(value['effects'])); self.assertTrue(value['interruption']['requested'])
        self.assertFalse((self.root/'.lks-sdd/transaction.json').exists())
        before = snapshot(self.root)
        self.assertEqual('completed', run(self.root, 'work-continue', data, apply=True)['status'])
        self.assertEqual(before, snapshot(self.root)); self.assertEqual(1, len(load(self.root).by_kind('execution')))
        (self.root/'app.py').write_bytes(code + b'# later independent work\n')
        before = snapshot(self.root)
        stopped = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('partial', stopped['status']); self.assertEqual(1, len(stopped['effects']))
        self.assertEqual(before, snapshot(self.root))

    def test_interrupted_real_pending_journal_recovery_preserves_later_work(self):
        # Exercise the new stop/recovery boundary on a real Windows long route;
        # the separate host sandbox incident is not involved.
        from path_utils import filesystem_root
        deep = self.out / ('ruta larga espacios ñ ' * 4).strip() / ('siguiente tramo ' * 5).strip() / ('consumidor profundo ' * 5).strip()
        self.assertTrue(deep.resolve().is_relative_to(self.out.resolve()))
        shutil.copytree(filesystem_root(self.root), filesystem_root(deep)); self.root = filesystem_root(deep)
        self.addCleanup(shutil.rmtree, self.root)
        self.assertGreater(len(str(self.root)), 260)
        data = self.data()
        def interrupted(*a, **k): return apply_packet(*a, **k, interrupt_after=1)
        with activity.session('work-continue'), patch('v3_storage.apply', side_effect=interrupted):
            value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('partial', value['status'], value)
        self.assertEqual('recover-or-rollback', value['recovery']['action'])
        later = self.root/'.lks-sdd/unrelated-note.txt'; later.write_text('later work', encoding='utf8')
        recover(self.root, value['recovery']['preview_hash'])
        self.assertEqual('later work', later.read_text())
        self.assertEqual('completed', run(self.root, 'work-continue', data, apply=True)['status'])
        before = snapshot(self.root)
        self.assertEqual('completed', run(self.root, 'work-continue', data, apply=True)['status'])
        self.assertEqual(before, snapshot(self.root))


if __name__ == '__main__': unittest.main()
