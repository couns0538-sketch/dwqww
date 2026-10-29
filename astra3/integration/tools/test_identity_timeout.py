#!/usr/bin/env python3
"""Pure-Python timeout evidence regression; subprocess.run is always mocked.

IDEA_SOURCE: same-repository identity helper and the requirement to preserve
original timeout bytes without inventing a child exit status.
"""
import argparse
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


class IdentityTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix=self._testMethodName + '-',
                                             dir=args.evidence_dir))
        self.exe = self.directory / 'never-executed.fixture'
        self.exe.write_bytes(b'not an executable; subprocess.run must be mocked\n')
        self.output = self.directory / 'output'

    def invoke(self, override=None, stdout=b'partial\x00stdout\xff\n', stderr=b'partial\x00stderr\xfe\n'):
        environment = {} if override is None else {'FORGE_BENCH_TIMEOUT_SECONDS': override}

        def timeout(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=stdout, stderr=stderr)

        with mock.patch.object(sys, 'argv', [str(args.helper), str(self.exe), str(self.output)]), \
             mock.patch.object(os, 'environ', environment), \
             mock.patch('subprocess.run', side_effect=timeout) as called:
            try:
                runpy.run_path(str(args.helper), run_name='__main__')
            except Exception as exc:
                return exc, called
        self.fail('helper unexpectedly completed despite injected timeout')

    def test_default_timeout(self):
        exception, called = self.invoke()
        self.assertIsInstance(exception, subprocess.TimeoutExpired)
        called.assert_called_once()
        self.assertEqual(called.call_args.kwargs['timeout'], 300)

    def test_override_consumed(self):
        exception, called = self.invoke('17')
        self.assertIsInstance(exception, subprocess.TimeoutExpired)
        self.assertEqual(called.call_args.kwargs['timeout'], 17)
        self.assertEqual(exception.timeout, 17)

    def test_invalid_and_nonpositive_rejected(self):
        for value in ('not-a-number', '0', '-1', '1.5', ''):
            with self.subTest(value=value):
                self.output = self.directory / ('invalid-' + str(len(list(self.directory.iterdir()))))
                exception, called = self.invoke(value)
                self.assertIsInstance(exception, ValueError)
                called.assert_not_called()

    def test_original_partial_bytes_and_unknown_exit(self):
        stdout, stderr = b'partial\x00stdout\xff\r\n', b'partial\x00stderr\xfe\n'
        exception, called = self.invoke('23', stdout, stderr)
        self.assertIsInstance(exception, subprocess.TimeoutExpired)
        called.assert_called_once()
        self.assertEqual((self.output / 'OFF_d11.stdout').read_bytes(), stdout)
        self.assertEqual((self.output / 'OFF_d11.stderr').read_bytes(), stderr)
        self.assertEqual((self.output / 'OFF_d11.stdin').read_bytes(), called.call_args.kwargs['input'])
        receipt = json.loads((self.output / 'timeout.json').read_text())
        self.assertEqual(receipt, {'mode': 'OFF', 'depth': 11, 'timeout_seconds': 23,
                                  'status': 'INCOMPLETE_TIMEOUT', 'actual_returncode': None})
        self.assertFalse((self.output / 'results.json').exists(), 'no completed result may be fabricated')

    def test_absent_partial_streams_are_empty(self):
        exception, called = self.invoke(stdout=None, stderr=None)
        self.assertIsInstance(exception, subprocess.TimeoutExpired)
        called.assert_called_once()
        self.assertEqual((self.output / 'OFF_d11.stdout').read_bytes(), b'')
        self.assertEqual((self.output / 'OFF_d11.stderr').read_bytes(), b'')
        receipt = json.loads((self.output / 'timeout.json').read_text())
        self.assertIsNone(receipt['actual_returncode'])


if __name__ == '__main__':
    unittest.main()
