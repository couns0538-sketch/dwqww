"""Subprocess contract checks for the external driver; no chess-engine workload."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import queue
import types

DRIVER = Path(__file__).with_name('run-full-engine-tt.py')
FAKE = r'''#!/usr/bin/env python3
import os, sys
mode = sys.argv[1]
position = 'startpos'
active = False
def out(text):
    print(text, flush=True)
def best():
    global active
    if '7k/6Q1/6K1' in position or '7k/5Q2/6K1' in position:
        move = '0000'
    elif mode == 'illegal': move = 'a1a8'
    elif position.startswith('startpos'): move = 'e2e4'
    elif 'r3k2r/p1ppqpb1' in position: move = 'e2a6'
    elif '8/2p5/3p4' in position: move = 'b4f4'
    else: move = 'a1b1'
    out('bestmove ' + move)
    active = False
for raw in sys.stdin:
    cmd = raw.strip()
    if cmd == 'uci':
        out('id name fake fixture')
        for name, kind in [('Threads','spin'),('Hash','spin'),('OwnBook','check'),('Ponder','check'),('Clear Hash','button')]:
            out('option name ' + name + ' type ' + kind)
        out('uciok')
    elif cmd == 'isready': out('readyok')
    elif cmd.startswith('position '):
        if active: sys.exit(91)
        position = cmd[9:]
    elif cmd.startswith('go '):
        active = True
        if mode == 'race':
            os.write(2, b'WARNING: ThreadSanitizer: data race (pid=123)\n  Write of size 8\n')
            sys.exit(66)
        if mode == 'mapping':
            os.write(2, b'FATAL: ThreadSanitizer: unexpected memory mapping\n')
            sys.exit(66)
        if mode == 'hang': continue
        score = 'mate 0' if '7k/6Q1/6K1' in position else 'cp 0'
        out('info depth 2 score ' + score + ' nodes 1000 nps 1000 hashfull 10 time 1 pv e2e4')
        if '1000000000' not in cmd: best()
    elif cmd == 'stop':
        if active and mode != 'hang': best()
    elif cmd.startswith('setoption ') or cmd == 'ucinewgame':
        if active: sys.exit(92)
    elif cmd == 'quit': sys.exit(0)
'''


class DriverContract(unittest.TestCase):
    def test_reader_capture_exception_is_retained_as_failure_evidence(self):
        spec = importlib.util.spec_from_file_location('full_engine_tt_driver', DRIVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = module.Engine.__new__(module.Engine)
            engine.evidence = module.Evidence(root)
            engine.index = 0
            engine.result = {'reader_errors': []}
            engine.lines = queue.Queue()
            pipe = (root / 'closed-pipe').open('wb')
            pipe.close()
            engine.process = types.SimpleNamespace(stderr=pipe)
            engine.read('stderr')
            engine.evidence.file.close()
            self.assertEqual(len(engine.result['reader_errors']), 1)
            self.assertIn('stderr', engine.result['reader_errors'][0])

    def run_driver(self, mode, *extra):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        engine = root / 'fixture engine.py'
        engine.write_text(FAKE)
        engine.chmod(0o755)
        output = root / 'evidence with spaces'
        cmd = [sys.executable, '-B', str(DRIVER), '--engine', str(engine),
               '--engine-arg', mode, '--output', str(output), '--cycles', '1',
               '--restarts', '1', '--nodes', '2000', '--handshake-timeout', '2',
               '--search-timeout', '.3', '--stop-timeout', '2', '--quit-timeout', '2', *extra]
        run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        summary = json.loads((output / 'summary.json').read_text())
        return run, summary, output, engine

    def test_serial_lifecycle_retains_exact_streams_and_hashes(self):
        run, summary, output, engine = self.run_driver('normal')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(summary['status'], 'passed')
        self.assertTrue(summary['completed_all_scenarios'])
        self.assertEqual(summary['engine_sha256_before'], hashlib.sha256(engine.read_bytes()).hexdigest())
        session = summary['sessions'][0]
        self.assertEqual(session['exit_code'], 0)
        self.assertGreaterEqual(len(session['searches']), 9)
        self.assertTrue(any(s['stopped'] for s in session['searches']))
        raw = (output / 'process-00' / 'stdin.bin').read_bytes()
        self.assertIn(b'setoption name Threads value 4\n', raw)
        self.assertIn(b'setoption name Hash value 1\n', raw)
        self.assertIn(b'setoption name Clear Hash\n', raw)
        self.assertIn(b'ucinewgame\n', raw)
        self.assertTrue(raw.endswith(b'quit\n'))
        stdout = (output / 'process-00' / 'stdout.bin').read_bytes()
        self.assertIn(b'bestmove a1b1\n', stdout)
        self.assertTrue(stdout.endswith(b'readyok\n'))
        events = [json.loads(x) for x in (output / 'events.jsonl').read_text().splitlines()]
        self.assertTrue(all('monotonic_ns' in e and 'wall_ns' in e for e in events))

    def test_expected_tsan_race_is_partial_evidence_not_a_pass(self):
        run, summary, output, _ = self.run_driver('race', '--allow-tsan-exit66')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(summary['status'], 'expected_tsan_race')
        self.assertFalse(summary['completed_all_scenarios'])
        self.assertEqual(summary['sessions'][0]['exit_code'], 66)
        self.assertIn(b'ThreadSanitizer: data race', (output / 'process-00' / 'stderr.bin').read_bytes())

    def test_tsan_startup_failure_is_not_accepted_as_a_race(self):
        run, summary, _, _ = self.run_driver('mapping', '--allow-tsan-exit66')
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(summary['status'], 'failed')
        self.assertEqual(summary['sessions'][0]['sanitizer_classification'], 'tsan_runtime_failure')

    def test_timeout_is_failure_even_with_clean_exit(self):
        run, summary, _, _ = self.run_driver('hang')
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(summary['status'], 'failed')
        self.assertIn('deadline', summary['error'])

    def test_illegal_bestmove_rejected(self):
        run, summary, _, _ = self.run_driver('illegal')
        if not summary['legal_validation']['available']:
            self.skipTest('python-chess unavailable; only syntax validation possible')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('illegal bestmove', summary['error'])


if __name__ == '__main__':
    unittest.main()
