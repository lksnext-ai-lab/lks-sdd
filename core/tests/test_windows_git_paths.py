"""Real Git observations through Windows aliases, without changing the checkout."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from path_utils import filesystem_root, short_existing_path
from v3_contract import ContractError
from v3_git import code_inventory, git, observe


@unittest.skipUnless(os.name == 'nt', 'Windows Git long paths')
class WindowsGitPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wp-git-unit-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.environ = patch.dict(os.environ, {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
        self.environ.start(); self.addCleanup(self.environ.stop)
        self.short = self.base / 'short'; self.short.mkdir()
        self.run_git('init', '-b', 'codex/test', str(self.short), cwd=self.base)
        (self.short / 'app.py').write_bytes(b'synthetic = True\n')
        self.run_git('-C', str(self.short), 'add', 'app.py')
        self.run_git('-C', str(self.short), '-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid',
                     '-c', 'commit.gpgsign=false', 'commit', '-m', 'Synthetic fixture')
        (self.short / '.gitignore').write_text('ignored.txt\n', encoding='utf-8')
        (self.short / 'ignored.txt').write_text('excluded', encoding='utf-8')
        (self.short / '.git/info/exclude').write_text('info-ignored.txt\n', encoding='utf-8')
        (self.short / 'info-ignored.txt').write_text('excluded', encoding='utf-8')
        (self.short / 'nested').mkdir(); (self.short / 'nested/inside.txt').write_text('inside', encoding='utf-8')
        target = self.base / ('segment-' + 'a'*70) / ('segment-' + 'b'*70) / ('segment-' + 'c'*70) / 'consumidor ñ con espacios'
        self.assertTrue(target.resolve().is_relative_to(self.base.resolve()))
        self.long = filesystem_root(target, force_extended=True)
        cleanup = filesystem_root(self.base / ('segment-' + 'a'*70), force_extended=True)
        def remove_owned():
            from path_utils import is_within_filesystem_path
            owned = filesystem_root(self.base, force_extended=True)
            def writable(function, path, error):
                self.assertTrue(is_within_filesystem_path(Path(path), owned))
                if not isinstance(error, PermissionError): raise error
                path = filesystem_root(Path(path), force_extended=True)
                path.chmod(stat.S_IWRITE | stat.S_IREAD); function(path)
            shutil.rmtree(owned, onexc=writable)
        self.addCleanup(remove_owned)
        self.long.parent.mkdir(parents=True); shutil.copytree(self.short, self.long)

    def run_git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.base, capture_output=True, check=True, timeout=30).stdout

    def snapshot(self):
        return {p.relative_to(self.long).as_posix(): p.read_bytes() for p in self.long.rglob('*') if p.is_file()}

    def test_long_inventory_prefix_ignores_and_identity_match_short(self):
        before = self.snapshot()
        expected = observe(self.short); actual = observe(self.long)
        for key in ('branch', 'head', 'unborn', 'refs'): self.assertEqual(expected[key], actual[key])
        self.assertEqual(code_inventory(self.short), code_inventory(self.long))
        self.assertEqual(code_inventory(self.short/'nested'), code_inventory(self.long/'nested'))
        self.assertNotIn('ignored.txt', code_inventory(self.long))
        self.assertNotIn('info-ignored.txt', code_inventory(self.long))
        self.assertEqual({'inside.txt'}, set(code_inventory(self.long/'nested')))
        self.assertEqual(before, self.snapshot())

    def test_external_gitfile_metadata_is_the_same_checkout(self):
        external = self.base / 'metadata'
        self.assertTrue(external.resolve().is_relative_to(self.base.resolve()))
        (self.long/'.git').rename(external)
        (self.long/'.git').write_text('gitdir: ' + str(external) + '\n', encoding='utf-8')
        self.assertEqual(observe(self.short)['head'], observe(self.long)['head'])
        self.assertEqual(code_inventory(self.short), code_inventory(self.long))

    def test_unborn_detached_and_changed_head_are_fresh(self):
        first = observe(self.long)
        git(self.long, 'update-ref', 'refs/heads/other', first['head'])
        git(self.long, 'symbolic-ref', 'HEAD', 'refs/heads/other')
        self.assertEqual('other', observe(self.long)['branch'])
        git(self.long, 'update-ref', '--no-deref', 'HEAD', first['head'])
        self.assertIsNone(observe(self.long)['branch'])
        self.assertEqual(first['head'], observe(self.long)['head'])
        git(self.long, 'symbolic-ref', 'HEAD', 'refs/heads/unborn')
        self.assertTrue(observe(self.long)['unborn'])

    def test_refs_show_and_missing_optional_match_short(self):
        expected = observe(self.short, refs=['refs/heads/codex/test', 'refs/heads/missing'])
        actual = observe(self.long, refs=['refs/heads/codex/test', 'refs/heads/missing'])
        self.assertEqual(expected['refs'], actual['refs'])
        self.assertEqual(git(self.short, 'show', 'HEAD:app.py'), git(self.long, 'show', 'HEAD:app.py'))
        self.assertIsNone(git(self.long, 'rev-parse', '--verify', 'refs/heads/missing', optional=True))

    def test_unconditional_relative_include_keeps_exclusions(self):
        for root in (self.short, self.long):
            (root/'.git/extra.cfg').write_text('[core]\n\texcludesFile = extra-ignore.txt\n', encoding='utf-8')
            (root/'extra-ignore.txt').write_text('extra-ignored.txt\n', encoding='utf-8')
            (root/'extra-ignored.txt').write_text('excluded', encoding='utf-8')
            with (root/'.git/config').open('a', encoding='utf-8') as stream: stream.write('\n[include]\n\tpath = extra.cfg\n')
        self.assertEqual(code_inventory(self.short), code_inventory(self.long))
        self.assertNotIn('extra-ignored.txt', code_inventory(self.long))

    def test_gitdir_conditional_is_not_silently_omitted(self):
        included = self.base/'conditional.cfg'; included.write_text('[probe]\n\tvalue = must-not-disappear\n', encoding='utf-8')
        with (self.long/'.git/config').open('a', encoding='utf-8') as stream:
            stream.write('\n[includeIf "gitdir:**/consumer/.git"]\n\tpath = ' + included.as_posix() + '\n')
        with self.assertRaisesRegex(ContractError, 'gitdir-conditional'): observe(self.long)

    def test_unavailable_alias_is_explicit_and_not_cached(self):
        with patch('path_utils.short_existing_path', side_effect=OSError('8.3 disabled')):
            with self.assertRaisesRegex(ContractError, 'short alias'): observe(self.long)
        self.assertEqual(observe(self.short)['head'], observe(self.long)['head'])

    def test_alias_must_identify_the_same_directory(self):
        with patch('path_utils.same_filesystem_path', return_value=False):
            with self.assertRaisesRegex(OSError, 'same Git directory'): short_existing_path(self.long)

    def test_invalid_gitfile_does_not_choose_another_repository(self):
        external = self.base/'metadata'; (self.long/'.git').rename(external)
        (self.long/'.git').write_text('untrusted-pointer', encoding='utf-8')
        with self.assertRaisesRegex(ContractError, 'Invalid Git directory'): observe(self.long)

    def test_short_invocation_keeps_original_arguments_and_limits(self):
        import v3_git
        command, cwd, prefix, checkout = v3_git._invocation(self.short, ('show', 'HEAD:app.py'))
        self.assertEqual(['git', '-C', str(self.short), 'show', 'HEAD:app.py'], command)
        self.assertIsNone(cwd); self.assertIsNone(prefix); self.assertIsNone(checkout)
        with patch('v3_git.subprocess.run', side_effect=subprocess.TimeoutExpired('git', 60)):
            with self.assertRaisesRegex(ContractError, '60 s'): git(self.short, 'rev-parse', 'HEAD')



    def test_unverified_ownership_never_executes_git(self):
        with patch('path_utils.owned_by_current_user',return_value=False), patch('v3_git.subprocess.run') as launch:
            with self.assertRaisesRegex(ContractError,'ownership'): observe(self.long)
            launch.assert_not_called()

    def test_relative_fetch_url_is_not_resolved_against_another_directory(self):
        with (self.long/'.git/config').open('a',encoding='utf-8') as stream:
            stream.write('\n[remote "local"]\n\turl = ../other-repo\n')
        with self.assertRaisesRegex(ContractError,'absolute configured remote URL'):
            git(self.long,'fetch','--','local')


    def test_gitfile_preserves_leading_space_in_directory_identity(self):
        (self.long/'.git').rename(self.long/' metadata')
        shutil.copytree(self.short/'.git',self.long/'metadata')
        (self.long/'metadata/HEAD').write_bytes(b'ref: refs/heads/decoy\n')
        (self.long/'.git').write_bytes(b'gitdir:  metadata\n')
        expected=observe(self.short);actual=observe(self.long)
        self.assertEqual(expected['branch'],actual['branch'])
        self.assertEqual(expected['head'],actual['head'])

    def test_routing_environment_never_changes_repository_or_index(self):
        for name,value in [('GIT_INDEX_FILE','.git/index'),('GIT_DIR','other'),('GIT_CONFIG_GLOBAL','relative-config')]:
            with self.subTest(name=name),patch.dict(os.environ,{name:value}),patch('v3_git.subprocess.run') as launch:
                with self.assertRaisesRegex(ContractError,'environment'): observe(self.long)
                launch.assert_not_called()

    def test_bare_configuration_is_not_promoted_to_worktree(self):
        config=self.long/'.git/config'
        config.write_text(config.read_text(encoding='utf-8').replace('bare = false','bare = true'),encoding='utf-8')
        with self.assertRaisesRegex(ContractError,'bare repository'): observe(self.long)

    def test_declared_worktree_must_identify_original_checkout(self):
        config=self.long/'.git/config';raw=config.read_text(encoding='utf-8')
        config.write_text(raw+'\n[core]\n\tworktree = '+self.short.as_posix()+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ContractError,'core.worktree'): observe(self.long)
        logical=str(self.long)[4:].replace('\\','/')
        config.write_text(raw+'\n[core]\n\tworktree = '+logical+'\n',encoding='utf-8')
        self.assertEqual(observe(self.short)['head'],observe(self.long)['head'])

    def test_git_configuration_error_remains_diagnostic(self):
        with (self.long/'.git/config').open('a',encoding='utf-8') as stream:stream.write('\n[invalid\n')
        with self.assertRaisesRegex(ContractError,'bad config line'): observe(self.long)

if __name__ == '__main__': unittest.main()
