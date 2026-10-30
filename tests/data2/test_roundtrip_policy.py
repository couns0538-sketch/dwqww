"""The standalone million-row runner must enforce the external GPL boundary."""
import contextlib
import io
import pathlib
import runpy
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = pathlib.Path(__file__).resolve().parents[2] / 'tools' / 'data2'
sys.path.insert(0, str(TOOLS))


class RoundtripPolicy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.adapter = self.root / 'adapter'
        self.adapter.write_text('not executed')
        self.output = self.root / 'output'

    def run_script(self, ack=False):
        args = [str(TOOLS / 'run_1m_roundtrip.py'), '--input', str(self.root / 'input'),
                '--adapter', str(self.adapter), '--adapter-source', str(self.root / 'source'),
                '--out', str(self.output)] + (['--accept-gpl3'] if ack else [])
        with mock.patch.object(sys, 'argv', args), contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                runpy.run_path(args[0], run_name='__main__')
            except SystemExit as exc:
                return exc.code, err.getvalue()
        self.fail('Runner should have stopped at a mocked boundary')

    def test_without_ack_refuses_before_writes_or_execution(self):
        with mock.patch('subprocess.Popen') as popen:
            code, message = self.run_script()
        self.assertNotEqual(code, 0)
        self.assertIn('accept-gpl3', message)
        popen.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_repo_and_bare_and_worktree_refuse_even_with_ack(self):
        for kind in ('repo', 'bare', 'worktree'):
            with self.subTest(kind=kind):
                repo = self.root / kind
                repo.mkdir()
                if kind == 'worktree':
                    (repo / '.git').write_text('gitdir: /elsewhere')
                else:
                    meta = repo if kind == 'bare' else repo / '.git'
                    meta.mkdir(exist_ok=True)
                    (meta / 'HEAD').write_text('ref: refs/heads/test\n')
                    (meta / 'objects').mkdir()
                self.adapter = repo / 'adapter'
                self.adapter.write_text('not executed')
                with mock.patch('subprocess.Popen') as popen:
                    code, message = self.run_script(True)
                self.assertNotEqual(code, 0)
                self.assertIn('outside', message)
                popen.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_ack_external_adapter_reaches_execution(self):
        with mock.patch('subprocess.Popen', side_effect=RuntimeError('execution boundary')) as popen:
            with self.assertRaisesRegex(RuntimeError, 'execution boundary'):
                self.run_script(True)
        self.assertEqual(popen.call_args.args[0][0], str(self.adapter.resolve()))

    def test_symlink_dotdot_repo_target_refuses_before_writes(self):
        repo = self.root / 'repo'
        repo.mkdir()
        (repo / '.git').write_text('gitdir: /elsewhere')
        (repo / 'subdir').mkdir()
        (repo / 'adapter').write_text('not executed')
        link = self.root / 'link'
        link.symlink_to(repo / 'subdir', target_is_directory=True)
        self.adapter = link / '..' / 'adapter'
        code, message = self.run_script(True)
        self.assertNotEqual(code, 0)
        self.assertIn('outside', message)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
