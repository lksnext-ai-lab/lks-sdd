"""Git reuse is bounded to a read-only preparation, never a physical guard."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import asyncio
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from v3_git import git, observation_evaluation


class GitObservationScopeTests(unittest.TestCase):
    def setUp(self):
        self.root=Path.cwd()
        self.routing=patch('v3_git._invocation',return_value=(['git'],None,None,None));self.routing.start();self.addCleanup(self.routing.stop)
        self.process=patch('v3_git.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=b'branch\n',stderr=b''));self.call=self.process.start();self.addCleanup(self.process.stop)

    def test_reuse_stops_at_scope_exit_before_the_next_physical_read(self):
        with observation_evaluation(self.root):
            self.assertEqual(b'branch\n',git(self.root,'symbolic-ref','--short','HEAD'))
            git(self.root,'symbolic-ref','--short','HEAD')
            self.assertEqual(1,self.call.call_count)
        self.call.return_value.stdout=b'changed\n'
        self.assertEqual(b'changed\n',git(self.root,'symbolic-ref','--short','HEAD'))
        self.assertEqual(2,self.call.call_count)

    def test_fetch_shared_refs_and_other_roots_are_not_reused(self):
        with observation_evaluation(self.root):
            for _ in range(2):
                git(self.root,'fetch','--','origin')
                git(self.root,'rev-parse','--verify','shared^{commit}')
                git(self.root.parent,'rev-parse','--verify','HEAD')
        self.assertEqual(6,self.call.call_count)

    def test_missing_optional_observation_is_not_cached(self):
        self.call.return_value.returncode=1
        with observation_evaluation(self.root):
            for _ in range(2): self.assertIsNone(git(self.root,'rev-parse','--verify','HEAD',optional=True))
        self.assertEqual(2,self.call.call_count)

    def test_bounded_inventory_reuse_ends_before_the_next_physical_read(self):
        args = ('ls-files','-z','--cached','--others','--exclude-standard')
        result = SimpleNamespace(returncode=0, stdout=b'app.py\0', stderr=b'')
        with patch('v3_git._bounded_ls_files',return_value=result) as capture:
            with observation_evaluation(self.root):
                self.assertEqual(b'app.py\0',git(self.root,*args))
                git(self.root,*args)
                self.assertEqual(1,capture.call_count)
            result.stdout=b'changed.py\0'
            self.assertEqual(b'changed.py\0',git(self.root,*args))
            self.assertEqual(2,capture.call_count)

    def test_exception_clears_scope(self):
        with self.assertRaises(ValueError):
            with observation_evaluation(self.root):
                git(self.root,'rev-parse','--verify','HEAD');raise ValueError('interrupted preparation')
        git(self.root,'rev-parse','--verify','HEAD')
        self.assertEqual(2,self.call.call_count)

    def test_thread_does_not_inherit_the_observation(self):
        with observation_evaluation(self.root):
            git(self.root,'rev-parse','--verify','HEAD')
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(git,self.root,'rev-parse','--verify','HEAD').result()
        self.assertEqual(2,self.call.call_count)

    def test_async_child_cannot_reuse_an_inherited_parent_context(self):
        async def child(): git(self.root,'rev-parse','--verify','HEAD')
        async def parent():
            with observation_evaluation(self.root):
                git(self.root,'rev-parse','--verify','HEAD')
                await asyncio.create_task(child())
        asyncio.run(parent())
        self.assertEqual(2,self.call.call_count)
