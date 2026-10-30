"""Native evidence preservation regressions; set FORGE_LOCK_ORACLE to a built oracle."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

BINARY = os.environ.get('FORGE_LOCK_ORACLE')
FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n'

@unittest.skipUnless(BINARY, 'set FORGE_LOCK_ORACLE to run native output-preservation tests')
class OracleFiles(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='lock-oracle-io-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.fens = self.root/'input.fen'
        self.fens.write_text(FEN)
        self.cp = self.root/'output.txt'

    def run_oracle(self, *args):
        return subprocess.run([BINARY, str(self.fens), *map(str,args)], capture_output=True, timeout=10)

    def test_existing_output_preserved(self):
        self.cp.write_bytes(b'original evidence\n')
        result = self.run_oracle(self.cp)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.cp.read_bytes(), b'original evidence\n')

    def test_input_alias_preserved(self):
        result = self.run_oracle(self.fens)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.fens.read_text(), FEN)

    def test_symlink_input_alias_preserved(self):
        self.cp.symlink_to(self.fens)
        result = self.run_oracle(self.cp)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.fens.read_text(), FEN)

    def test_hardlink_input_alias_preserved(self):
        self.cp.hardlink_to(self.fens)
        result = self.run_oracle(self.cp)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.fens.read_text(), FEN)

    def test_duplicate_optional_output_rejected_before_creating_files(self):
        result = self.run_oracle(self.cp, '--hce', self.cp)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.cp.exists())
        self.assertEqual(self.fens.read_text(), FEN)

    def test_existing_optional_output_preserved_before_creating_files(self):
        hce = self.root/'hce.txt'
        hce.write_bytes(b'original HCE\n')
        result = self.run_oracle(self.cp, '--hce', hce)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.cp.exists())
        self.assertEqual(hce.read_bytes(), b'original HCE\n')

    def test_success_creates_new_outputs(self):
        hce = self.root/'hce.txt'
        result = self.run_oracle(self.cp, '--hce', hce)
        self.assertEqual(result.returncode, 0, result.stderr)
        int(self.cp.read_text().strip())
        int(hce.read_text().strip())
        self.assertEqual(self.fens.read_text(), FEN)

if __name__ == '__main__':
    unittest.main()
