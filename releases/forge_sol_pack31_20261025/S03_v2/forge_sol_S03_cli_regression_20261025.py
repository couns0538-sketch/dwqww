#!/usr/bin/env python3
"""Exercise the real output-collision preflight without starting an engine."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args, remaining = parser.parse_known_args()
args.out.mkdir(parents=False, exist_ok=False)
tool = args.tool.resolve(strict=True)
records = []

def encoded(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'encoding': 'base64', 'data': base64.b64encode(data).decode('ascii')}

class OutputCollisionTests(unittest.TestCase):
    def check_collision(self, kind):
        existing = args.out / f'forge_sol_S03_existing_{kind}_20261025'
        marker = b'preserve existing input exactly\r\n'
        if kind == 'directory':
            existing.mkdir()
            content = existing / 'forge_sol_S03_marker_20261025.txt'
            content.write_bytes(marker)
        elif kind == 'file':
            existing.write_bytes(marker)
            content = existing
        else:
            existing.symlink_to('forge_sol_S03_missing_target_20261025')
            content = None
        argv = [sys.executable, '-B', str(tool), sys.executable,
                '--out', str(existing)]
        child = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False)
        preserved = (existing.is_symlink() if kind == 'symlink'
                     else content.read_bytes() == marker)
        if kind == 'directory':
            preserved = preserved and list(existing.iterdir()) == [content]
        record = {'case': kind, 'argv': argv, 'exit': child.returncode,
                  'stdout': encoded(child.stdout), 'stderr': encoded(child.stderr),
                  'input_preserved': preserved,
                  'child_waited': True, 'stream_capture_complete': True}
        records.append(record)
        (args.out / f'forge_sol_S03_{kind}_raw_20261025.json').write_text(
            json.dumps(record, indent=2) + '\n')
        combined = child.stdout + child.stderr
        self.assertEqual(child.returncode, 1, 'collision must exit 1')
        self.assertNotIn(b'Traceback', combined, 'collision must have no traceback')
        self.assertEqual(len(combined.splitlines()), 1, 'exactly one error line')
        self.assertIn(b'output directory already exists', combined)
        self.assertTrue(preserved, 'pre-existing input must remain unchanged')

    def test_existing_directory_is_one_line_failure(self):
        self.check_collision('directory')

    def test_existing_file_is_one_line_failure(self):
        self.check_collision('file')

    def test_dangling_output_symlink_is_one_line_failure(self):
        self.check_collision('symlink')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OutputCollisionTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    result = {'status': 'PASS' if outcome.wasSuccessful() else 'FAIL',
              'tool_sha256': hashlib.sha256(tool.read_bytes()).hexdigest(),
              'cases': records, 'scope': 'Actual CLI output preflight only; no engine process launched'}
    (args.out / 'forge_sol_S03_cli_result_20261025.json').write_text(
        json.dumps(result, indent=2) + '\n')
    sys.exit(0 if outcome.wasSuccessful() else 1)
