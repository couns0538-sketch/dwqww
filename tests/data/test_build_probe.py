#!/usr/bin/env python3
"""Build receipt/error-path tests; the full native build is verified separately.
IDEA_SOURCE: user requirement for reproducible offline Forge data tooling.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/data/build_probe.py'


class BuildProbeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='forge-build-probe-test-'))
        print('retained build fixture ' + str(self.root), file=sys.stderr)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              text=True, capture_output=True, check=False)

    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'build tool has not been implemented')
        spec = importlib.util.spec_from_file_location('build_probe', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_existing_output_is_untouched_and_refused(self):
        output = self.root / 'existing'
        output.mkdir()
        (output / 'sentinel').write_bytes(b'never overwrite')
        run = self.run_tool('--output', output)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('output directory already exists', run.stderr)
        self.assertEqual(list(output.iterdir()), [output / 'sentinel'])
        self.assertEqual((output / 'sentinel').read_bytes(), b'never overwrite')

    def test_missing_compiler_leaves_failed_receipt(self):
        output = self.root / 'missing-compiler'
        run = self.run_tool('--output', output, '--cxx', self.root / 'absent-g++')
        self.assertNotEqual(run.returncode, 0)
        receipt = output / 'build_receipt.json'
        self.assertTrue(receipt.is_file(), 'failed build must retain a receipt')
        data = json.loads(receipt.read_text())
        self.assertEqual(data['status'], 'FAIL')
        self.assertIn('compiler', data['error'])
        self.assertIn('source_sha256', data)
        self.assertNotIn('probe_sha256', data)

    def test_invalid_jobs_does_not_create_output(self):
        output = self.root / 'invalid-jobs'
        run = self.run_tool('--output', output, '--jobs', '0')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('jobs must be', run.stderr)
        self.assertFalse(output.exists())

    def test_flags_cannot_be_smuggled_into_architecture(self):
        output = self.root / 'invalid-flags'
        run = self.run_tool('--output', output, '--march', 'native -ffast-math')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('architecture names', run.stderr)
        self.assertFalse(output.exists())

    def test_fma_instruction_counter_ignores_symbol_and_comment_names(self):
        module = self.module()
        text = ('0000000 <vfmadd_symbol>:\n'
                ' 0: c4 e2 71 99 c2  vfmadd132ss %xmm2,%xmm1,%xmm0\n'
                ' 5: c4 e2 75 9a c2  vfmsub132ps %ymm2,%ymm1,%ymm0\n'
                ' a: c4 e2 75 9c c2  vfnmadd132ps %ymm2,%ymm1,%ymm0\n'
                ' f: c4 e2 75 9e c2  vfnmsub132ps %ymm2,%ymm1,%ymm0\n'
                '14: c5 f8 58 c1     vaddps %xmm1,%xmm0,%xmm0 # vfmadd132ps\n')
        self.assertEqual(module.count_fma(text), 4)

    def test_environment_flags_cannot_override_strict_fp(self):
        module = self.module()
        clean = module.clean_environment({'PATH': '/bin', 'CXXFLAGS': '-ffast-math',
                                         'CFLAGS': '-Ofast', 'LDFLAGS': '-flto',
                                         'CXX': 'wrong-compiler', 'CPPFLAGS': '-DFORGE_NNUE_INT16=1'})
        self.assertEqual(clean, {'PATH': '/bin'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
