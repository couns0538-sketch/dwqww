#!/usr/bin/env python3
"""Synthetic finalizer regressions; every subprocess.run call is mocked.
IDEA_SOURCE: same-repository finalizer review and evidence-integrity requirements.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--helper', type=Path, required=True)
parser.add_argument('--evidence-dir', type=Path, required=True)
args, remaining = parser.parse_known_args()
args.evidence_dir.mkdir(parents=True, exist_ok=False)
sys.argv = [sys.argv[0], *remaining]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
SOURCE = '926c55f33227bc4a030d7ce5b1140528aeba75af'


class FinalizerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix=self._testMethodName + '-', dir=args.evidence_dir))
        self.engine = self.root / 'never-executed.fixture'
        self.engine.write_bytes(b'synthetic non-executable engine fixture\n')
        flags = self.root / 'CMakeFiles/forge_core.dir/flags.make'
        flags.parent.mkdir(parents=True)
        flags.write_text('synthetic -fsanitize=thread\n')
        self.directory = self.root / 'tsan'
        (self.directory / 'pins').mkdir(parents=True)
        digest = hashlib.sha256(self.engine.read_bytes()).hexdigest()
        self.build = {'status': 'BUILT', 'source_commit': SOURCE, 'binary_sha256': digest}
        self.write_build()
        records = []
        for depth, nodes in [(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]:
            stem = self.directory / 'pins' / f'OFF_d{depth}'
            stem.with_suffix('.stdout').write_bytes(f'uciok\nreadyok\ninfo string bench depth {depth} nodes {nodes} time 1 nps 1\n'.encode())
            stem.with_suffix('.stderr').write_bytes(b'')
            records.append({'mode':'OFF','depth':depth,'returncode':0,'pass':True})
        (self.directory / 'pins/results.json').write_text(json.dumps({'sha256':digest,'records':records}))
        (self.directory / 'pins/perft.stdout').write_bytes(b'nodes 4865609\n')
        (self.directory / 'pins_driver.stdout').write_text(json.dumps({'perft5':True,'returncode':0})+'\n')

    def write_build(self):
        (self.directory / 'build_receipt.json').write_text(json.dumps(self.build))

    def invoke(self, objdump_failure=False):
        raw_out, raw_err = b'partial disassembly\x00\xff\n', b'objdump failed\x00\xfe\n'

        def command(argv, **kwargs):
            if argv[0] == 'objdump':
                code = 17 if objdump_failure else 0
                if code and kwargs.get('check'):
                    raise subprocess.CalledProcessError(code, argv, raw_out, raw_err)
                return subprocess.CompletedProcess(argv, code, raw_out if code else b'nop\n', raw_err if code else b'')
            self.assertEqual(argv, [str(self.engine.resolve())])
            return subprocess.CompletedProcess(argv, 0, b'nodes 193690690\n', b'')

        with mock.patch.object(sys, 'argv', [str(args.helper), str(self.engine), str(self.directory)]), \
             mock.patch.object(os, 'environ', {'TSAN_OPTIONS':'halt_on_error=1'}), \
             mock.patch('subprocess.run', side_effect=command) as calls:
            error = None
            try:
                runpy.run_path(str(args.helper), run_name='__main__')
            except Exception as exc:
                error = exc
        receipt = json.loads((self.directory/'final_identity/qualification.json').read_text())
        return error, receipt, calls, raw_out, raw_err

    def test_valid_control(self):
        error, receipt, calls, _, _ = self.invoke()
        self.assertIsNone(error)
        self.assertEqual(receipt['status'], 'PASS')
        self.assertEqual(calls.call_count, 2)

    def test_invalid_pin_never_passes_under_optimized_python(self):
        path = self.directory/'pins/OFF_d11.stdout'
        path.write_bytes(path.read_bytes().replace(b'nodes 312866', b'nodes 1'))
        error, receipt, calls, _, _ = self.invoke()
        self.assertIsNotNone(error)
        self.assertEqual(receipt['status'], 'FAIL_OR_INCOMPLETE')
        calls.assert_not_called()

    def test_wrong_build_digest(self):
        self.build['binary_sha256'] = '0'*64
        self.write_build()
        error, receipt, calls, _, _ = self.invoke()
        self.assertIsNotNone(error)
        self.assertEqual(receipt['status'], 'FAIL_OR_INCOMPLETE')
        calls.assert_not_called()

    def test_wrong_build_source(self):
        self.build['source_commit'] = '0'*40
        self.write_build()
        error, receipt, calls, _, _ = self.invoke()
        self.assertIsNotNone(error)
        self.assertEqual(receipt['status'], 'FAIL_OR_INCOMPLETE')
        calls.assert_not_called()

    def test_objdump_failure_preserves_original_streams(self):
        error, receipt, calls, raw_out, raw_err = self.invoke(objdump_failure=True)
        self.assertIsNotNone(error)
        self.assertEqual(receipt['status'], 'FAIL_OR_INCOMPLETE')
        calls.assert_called_once()
        directory = self.directory/'final_identity'
        self.assertEqual((directory/'objdump.stdout').read_bytes(), raw_out)
        self.assertEqual((directory/'objdump.stderr').read_bytes(), raw_err)
        self.assertEqual((directory/'objdump_exit.txt').read_text(), '17\n')


if __name__ == '__main__':
    unittest.main()
