#!/usr/bin/env python3
"""Real owned-process cleanup contracts; no chess engine or timing experiment."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument('--runner', type=Path, required=True)
parser.add_argument('--artifacts', type=Path, required=True)
arguments, remaining = parser.parse_known_args()
arguments.runner = arguments.runner.resolve()
arguments.artifacts = arguments.artifacts.resolve()
arguments.artifacts.mkdir(parents=True, exist_ok=False)
spec = importlib.util.spec_from_file_location('causal_runner_under_test', arguments.runner)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def active_members(pgid):
    """Independent test oracle: only live members of this fixture's group."""
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            stat = (path/'stat').read_text()
            fields = stat[stat.rindex(')') + 2:].split()
            if fields[0] != 'Z' and int(fields[2]) == pgid:
                found.append(int(path.name))
        except (OSError, ValueError, IndexError):
            pass
    return found


class CleanupContracts(unittest.TestCase):
    def fixture(self, *, orphan):
        directory = arguments.artifacts/self._testMethodName
        directory.mkdir()
        helper = directory/'fixture.py'
        helper.write_text('#!' + sys.executable + '\n' + '''
import os, signal
signal.signal(signal.SIGTERM, signal.SIG_IGN)
''' + ('''
read_fd, write_fd = os.pipe()
child = os.fork()
if child:
    os.close(write_fd)
    os.read(read_fd, 1)
    os.close(read_fd)
    os._exit(0)
os.close(read_fd)
os.write(write_fd, b'R')
os.close(write_fd)
''' if orphan else '') + '''
os.write(1, b'fixture-ready\\n')
while True:
    signal.pause()
''')
        helper.chmod(0o700)
        capture = runner.Capture(helper, directory/'capture', 1, time.monotonic()+5)
        self.addCleanup(self.emergency_fixture_cleanup, capture)
        capture.wait('fixture-ready')
        if orphan:
            self.assertEqual(capture.proc.wait(timeout=1), 0)
        self.assertTrue(active_members(capture.proc.pid))
        return capture

    @staticmethod
    def emergency_fixture_cleanup(capture):
        # Test cleanup is unconditional so even the expected RED cannot leak.
        try:
            os.killpg(capture.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            capture.proc.wait(timeout=1)
        except Exception:
            pass
        for thread in capture.readers:
            thread.join(timeout=1)
        for stream in (capture.proc.stdin, capture.proc.stdout, capture.proc.stderr, capture.stdin):
            if stream is not None and not stream.closed:
                stream.close()
        descriptor = getattr(capture, 'log_fd', None)
        if descriptor is not None:
            try:
                # Only close this capture's log, never a potentially reused FD.
                expected = (capture.out/'manager-events.jsonl').stat()
                actual = os.fstat(descriptor)
                if (actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino):
                    os.close(descriptor)
            except OSError:
                pass

    def assert_finalized(self, capture):
        self.assertFalse(active_members(capture.proc.pid), 'owned live descendant survived cleanup')
        self.assertIsNotNone(capture.proc.poll())
        self.assertTrue(all(not thread.is_alive() for thread in capture.readers))
        self.assertTrue(capture.finished)
        self.assertTrue(capture.stdin.closed)
        self.assertTrue(capture.proc.stdin.closed)

    def test_exited_leader_does_not_leave_live_descendant(self):
        capture = self.fixture(orphan=True)
        problem = None
        try:
            capture.close(success=True)
        except Exception as error:
            problem = repr(error)
        self.assertIsNone(problem, 'cleanup rejected a fully drainable owned descendant: '+str(problem))
        self.assert_finalized(capture)
        capture.close()  # Successful cleanup is idempotent.

    def test_early_cleanup_exception_allows_real_retry(self):
        capture = self.fixture(orphan=False)
        # Only the initial leader wait is fault-injected. The process, pipes,
        # signals, capture threads, second cleanup and idempotence are real.
        with mock.patch.object(capture.proc, 'wait', side_effect=RuntimeError('injected early cleanup exception')):
            with self.assertRaisesRegex(RuntimeError, 'injected early cleanup exception'):
                capture.close(success=True)
        self.assertFalse(capture.finished, 'failed cleanup was prematurely marked finished')
        capture.close()
        self.assert_finalized(capture)
        capture.close()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
