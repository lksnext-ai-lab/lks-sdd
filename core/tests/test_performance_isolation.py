"""Real native-process observations, without performance assertions."""
import subprocess
import sys
import time
import unittest

from performance_isolation import Audit, ConcurrentRunner, Watch, processes


@unittest.skipUnless(sys.platform=='win32','Native Windows process audit')
class IsolationTests(unittest.TestCase):
    def test_active_foreign_runner_is_rejected_and_completed_identity_is_not_active(self):
        audit=Audit()
        # Existing machine activity is the test fixture, not benchmark clearance.
        audit.known.update(processes())
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)','measure_approval_conflict.py'])
        try:
            with self.assertRaises(ConcurrentRunner) as caught: audit.check()
            self.assertIn(str(child.pid),str(caught.exception))
        finally: child.terminate();child.wait()
        self.assertNotIn(child.pid,processes())
        audit.check()

    def test_native_watch_detects_foreign_process_and_accepts_owned_descendant(self):
        audit=Audit(); audit.known.update(processes())
        code="import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(1)','approval_command_worker.py']);time.sleep(1.5);p.wait()"
        owned=subprocess.Popen([sys.executable,'-c',code,'measure_approval_owned_probe.py'])
        watch=Watch(audit,owned.pid,interval=.01);watch.start()
        foreign=None
        try:
            time.sleep(.15)
            foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(.3)','measure_approval_conflict.py'])
            foreign.wait();owned.wait()
        finally:
            if foreign is not None and foreign.poll() is None: foreign.terminate();foreign.wait()
            if owned.poll() is None: owned.terminate();owned.wait()
            report=watch.close()
        self.assertFalse(report['errors'],report)
        self.assertIn(foreign.pid,{e['pid'] for e in report['unowned_new_identities']})
        self.assertGreaterEqual(len(report['owned_python_identities']),2)
        self.assertFalse(set(report['owned_python_identities']) & {e['pid'] for e in report['unowned_new_identities']})

    def test_unrecognized_coordinators_and_opaque_python_are_also_rejected(self):
        for label in ('run-s3-release-close-sequence.py','run-s3-release-native.py','opaque'):
            with self.subTest(label=label):
                audit=Audit();audit.known.update(processes())
                child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)',label])
                try:
                    with self.assertRaises(ConcurrentRunner) as caught:audit.check()
                    self.assertIn('any-unowned-python',str(caught.exception))
                    self.assertIn(str(child.pid),str(caught.exception))
                finally:child.terminate();child.wait()
                audit.check()
