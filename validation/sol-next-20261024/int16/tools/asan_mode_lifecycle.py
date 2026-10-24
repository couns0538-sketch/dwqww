#!/usr/bin/env python3
"""Bounded T2 normal-UCI mid-search backend transitions; no performance test."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

import chess

BASE = Path('/workspace/forge-sol-next-20261024/int16-agent')
GATE = Path('/workspace/forge-sol-next-20261024/int16-asan-off-qa/precondition-d11/RESULT.json')
OUT = BASE / 'asan-midsearch-mode'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir()
    os.sched_setaffinity(0, {1})
    gate = json.loads(GATE.read_text())
    exe = Path(gate['argv'][0])
    assert gate['status'] == 'PASS' and gate['rows'] == [[11, 308972]] and gate['engine_sha256'] == sha(exe)
    for key, value in gate['environment'].items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    controller = BASE / 'tools/wac300_uci.py'
    assert sha(controller) == 'e90a8e6eef04f9e875bfa4877b0a02f43cfe5ea05d1e7ae45f272f235d3e9b79'
    spec = importlib.util.spec_from_file_location('frozen_engine_io', controller)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = {'purpose': 'One bounded normal-UCI T2 lifecycle; no timings interpreted as performance',
                'cpu': 1, 'affinity': sorted(os.sched_getaffinity(0)), 'threads': 2,
                'exe': str(exe), 'exe_sha256': sha(exe), 'd11_gate': str(GATE), 'd11_gate_sha256': sha(GATE),
                'environment': gate['environment'], 'controller_sha256': sha(controller),
                'lifecycle_source_sha256': sha(Path(__file__)),
                'protocol': 'OFF infinite -> setoption true -> ON finite; ON infinite -> setoption false -> OFF finite',
                'step_watchdog_seconds': 15, 'whole_watchdog_seconds': 120,
                'finite_depth': 6, 'stop_rule': 'Stop first failure; no retries'}
    (OUT / 'frozen.json').write_text(json.dumps(manifest, indent=2) + '\n')
    deadline = time.monotonic() + 120
    engine = module.Engine(exe, 1, OUT, 'process')
    result = {'status': 'FAIL', 'transitions': [], 'finite_searches': []}

    def until(predicate):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('whole lifecycle deadline')
        return engine.until(predicate, min(15, remaining))

    def bestmoves(lines, board):
        found = [line.split()[1] for line in lines if line.startswith('bestmove ')]
        assert len(found) == 1, ('expected exactly one bestmove', found)
        assert chess.Move.from_uci(found[0]) in board.legal_moves, ('illegal bestmove', found[0])
        return found[0]

    try:
        engine.send('uci')
        greeting = until(lambda line: line == 'uciok')
        assert 'option name NnueInt16 type check default false' in greeting
        for setting in ('Threads value 2', 'Hash value 16', 'OwnBook value false', 'NnueInt16 value false'):
            engine.send('setoption name ' + setting)
        engine.send('isready')
        until(lambda line: line == 'readyok')
        for target, fen in [(True, chess.STARTING_FEN),
                            (False, 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1')]:
            board = chess.Board(fen)
            engine.send('position fen ' + fen)
            engine.send('isready')
            position_reply = until(lambda line: line == 'readyok')
            assert not any(line.startswith('info string invalid FEN:') for line in position_reply)
            engine.send('go infinite')
            started = until(lambda line: line.startswith('info depth '))
            assert not any(line.startswith('bestmove ') for line in started)
            engine.send('setoption name NnueInt16 value ' + ('true' if target else 'false'))
            engine.send('isready')
            changed = until(lambda line: line == 'readyok')
            interrupted = bestmoves(changed, board)
            assert not any('NnueInt16 unavailable' in line for line in changed)
            if target:
                ack = [i for i, line in enumerate(changed) if line == 'info string NnueInt16 active']
                assert len(ack) == 1
                assert next(i for i, line in enumerate(changed) if line.startswith('bestmove ')) < ack[0]
            else:
                assert 'info string NnueInt16 active' not in changed
            result['transitions'].append({'target_int16': target, 'infinite_search_observed': True,
                                          'interrupted_bestmove': interrupted, 'ready_after_join': True})
            engine.send('go depth 6')
            finite = until(lambda line: line.startswith('bestmove '))
            result['finite_searches'].append({'int16': target, 'bestmove': bestmoves(finite, board),
                                              'legal': True, 'depth': 6})
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = str(error)
    finally:
        result['actual_engine_exit'] = engine.close()
        result['stderr_bytes'] = (OUT / 'process/stderr.raw').stat().st_size
        result['exe_unchanged'] = sha(exe) == gate['engine_sha256']
        if result['actual_engine_exit'] != 0 or result['stderr_bytes'] != 0 or not result['exe_unchanged']:
            result['status'] = 'FAIL'
        (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
