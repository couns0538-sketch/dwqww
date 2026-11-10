#!/usr/bin/env python3
"""Inject exceptions through actual UCI worker/bench; assert protocol recovery."""
import argparse
import hashlib
import json
import os
import pathlib
import queue
import subprocess
import threading
import time


def check(binary, name, mode, command, fen=None, release=None, expected=None):
    env = dict(os.environ, FORGE_TEST_EXCEPTION=mode)
    p = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    q = queue.Queue()
    log = []
    def read():
        for line in p.stdout:
            line = line.rstrip()
            log.append('< ' + line)
            q.put(line)
        q.put(None)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    def send(line):
        log.append('> ' + line)
        p.stdin.write(line + '\n')
        p.stdin.flush()
    def wait(prefix):
        seen = []
        while True:
            line = q.get(timeout=15)
            if line is None:
                raise RuntimeError(f'engine exited {p.poll()} waiting for {prefix}')
            seen.append(line)
            if line.startswith(prefix):
                return seen
    try:
        send('setoption name OwnBook value false')
        send('setoption name Threads value 3')
        send('isready')
        wait('readyok')
        send('position fen ' + fen if fen else 'position startpos')
        send(command)
        wait('info string search error')
        if release:
            send('isready')
            interim = wait('readyok')
            assert not any(line.startswith('bestmove ') for line in interim), interim
            # Check that no premature fallback appears while the search remains
            # infinite/pondering, including after the controller's ready reply.
            try:
                premature = q.get(timeout=0.1)
            except queue.Empty:
                premature = ''
            assert not premature or not premature.startswith('bestmove '), premature
            send(release)
        best = wait('bestmove ')[-1]
        expected = expected or ('0000' if fen else 'a2a3')
        assert best == 'bestmove ' + expected, best
        assert sum('test injection:' in line for line in log) == 1, log
        assert sum(line.startswith('< info string search error') for line in log) == 1, log
        send('isready')
        tail = wait('readyok')
        if command.startswith('bench'):
            assert not any('info string bench depth' in line for line in tail), tail
            send('bench 1')
            wait('info string bench depth 1 nodes ')
        send('position startpos')
        send('go depth 2')
        again = wait('bestmove ')
        assert any(line.startswith('info depth 2 ') for line in again), again
        assert not any('search error' in line for line in again), again
        send('isready')
        wait('readyok')
        send('quit')
        p.wait(timeout=15)
        assert p.returncode == 0, p.returncode
        return {'case': name, 'passed': True, 'exit_code': p.returncode, 'log': log}
    except Exception as error:
        if p.poll() is None:
            p.kill()
        p.wait(timeout=15)
        reader.join(timeout=2)
        return {'case': name, 'passed': False, 'error': repr(error), 'exit_code': p.returncode, 'log': log}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=pathlib.Path)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve()
    cases = [
        ('search facade', 'search', 'go depth 3', None, None),
        ('non-standard exception', 'unknown', 'go depth 3', None, None),
        ('main worker allocation', 'main', 'go depth 3', None, None),
        ('helper worker allocation', 'helper', 'go depth 3', None, None),
        ('terminal fallback', 'search', 'go depth 3', '7k/6Q1/6K1/8/8/8/8/8 b - - 0 1', None),
        ('infinite wait', 'search', 'go infinite', None, 'stop'),
        ('ponderhit wait', 'search', 'go ponder', None, 'ponderhit'),
        ('ponder stop wait', 'search', 'go ponder', None, 'stop'),
        ('restricted fallback', 'search', 'go depth 3 searchmoves e2e4', None, None, 'e2e4'),
        ('empty restricted fallback', 'search', 'go depth 3 searchmoves', None, None, '0000'),
        ('illegal-only restricted fallback', 'search', 'go depth 3 searchmoves a1a8', None, None, '0000'),
        ('board-order restricted fallback', 'search', 'go depth 3 searchmoves g1f3 e2e4', None, None, 'e2e4'),
        ('bench facade', 'bench', 'bench 2', None, None),
        ('bench non-standard exception', 'bench_unknown', 'bench 2', None, None),
        ('bench internal allocation', 'bench_alloc', 'bench 2', None, None),
    ]
    results = []
    for case in cases:
        result = check(binary, *case)
        results.append(result)
        print(('PASS ' if result['passed'] else 'FAIL ') + result['case'], flush=True)
    data = {'binary': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'passed': all(result['passed'] for result in results), 'cases': results}
    args.output.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    return 0 if data['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
