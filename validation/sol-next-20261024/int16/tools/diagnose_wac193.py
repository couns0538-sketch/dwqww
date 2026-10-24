#!/usr/bin/env python3
"""Bounded normal-UCI diagnostic; three cases, not a WAC screen or NPS test."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import threading
import time

import chess

BASE = Path('/workspace/forge-sol-next-20261024/int16-agent')
EXE = Path('/workspace/forge-sol-next-20261024/build-int16-release/forge')
OUT = BASE / 'diagnostic-wac193'
CPU = 0


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    try:
        return Path(path).read_text()
    except OSError as error:
        return {'read_error': str(error)}


def usage():
    value = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {name: getattr(value, name) for name in ('ru_utime', 'ru_stime', 'ru_maxrss',
            'ru_minflt', 'ru_majflt', 'ru_inblock', 'ru_oublock', 'ru_nvcsw', 'ru_nivcsw')}


def proc(pid):
    task = Path(f'/proc/{pid}/task')
    return {'pid': pid, 'stat': read(f'/proc/{pid}/stat'), 'schedstat': read(f'/proc/{pid}/schedstat'),
            'tasks': {item.name: read(item / 'schedstat') for item in sorted(task.iterdir())} if task.exists() else {}}


def snapshot(pid):
    return {'utc_before': utc(), 'monotonic_before': time.monotonic(), 'observer': proc(os.getpid()),
            'child': proc(pid), 'cgroup_cpu_max': read('/sys/fs/cgroup/cpu.max'),
            'cgroup_cpu_stat': read('/sys/fs/cgroup/cpu.stat'),
            'cgroup_cpu_pressure': read('/sys/fs/cgroup/cpu.pressure'),
            'cgroup_memory_current': read('/sys/fs/cgroup/memory.current'),
            'cgroup_memory_events': read('/sys/fs/cgroup/memory.events'),
            'proc_cpu_pressure': read('/proc/pressure/cpu'),
            'utc_after': utc(), 'monotonic_after': time.monotonic()}


def main():
    OUT.mkdir()
    os.sched_setaffinity(0, {CPU})
    runner = BASE / 'tools/wac300_uci.py'
    runner_hash = hashlib.sha256(runner.read_bytes()).hexdigest()
    assert runner_hash == 'e90a8e6eef04f9e875bfa4877b0a02f43cfe5ea05d1e7ae45f272f235d3e9b79'
    engine_hash = hashlib.sha256(EXE.read_bytes()).hexdigest()
    assert engine_hash == '61f3753f8f66ec5b9ee2d43d0f3156b3bc1fedf32fc7da46582354a04c49e509'
    spec = importlib.util.spec_from_file_location('original_wac_runner', runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entry = json.loads((BASE / 'wac-int16/FAILURE_DIAGNOSIS.json').read_text())['failed_entry']
    manifest = {'scope': 'Bounded diagnostic only; original failed WAC trial remains FAILED and unpooled',
                'started_utc': utc(), 'observer_pid': os.getpid(), 'cpu': CPU,
                'affinity': sorted(os.sched_getaffinity(0)), 'nice': os.getpriority(os.PRIO_PROCESS, 0),
                'exe': str(EXE), 'engine_sha256': engine_hash, 'runner_sha256': runner_hash,
                'diagnostic_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'position': entry, 'order': ['OFF1', 'ON', 'OFF2'], 'movetime_ms': 1000,
                'watchdog_seconds': 5, 'stop_rule': 'Stop immediately after any new case fault; no repetitions'}
    (OUT / 'frozen.json').write_text(json.dumps(manifest, indent=2) + '\n')
    cases = []
    for name, active in [('OFF1', False), ('ON', True), ('OFF2', False)]:
        before_usage = usage()
        engine = module.Engine(EXE, CPU, OUT, name)
        row = {'name': name, 'int16': active, 'child_pid': engine.process.pid,
               'usage_before': before_usage, 'started_utc': utc()}
        samples = []
        stop = threading.Event()
        monitor = None
        try:
            engine.send('uci')
            greeting = engine.until(lambda line: line == 'uciok', 10)
            assert 'option name NnueInt16 type check default false' in greeting
            for setting in ('Threads value 1', 'Hash value 16', 'OwnBook value false', 'Move Overhead value 10'):
                engine.send('setoption name ' + setting)
            engine.send('setoption name NnueInt16 value ' + ('true' if active else 'false'))
            engine.send('isready')
            ready = engine.until(lambda line: line == 'readyok', 10)
            if active:
                assert 'info string NnueInt16 active' in ready
                assert 'info string NnueInt16 unavailable; using float' not in ready
            engine.send('ucinewgame')
            engine.send('isready')
            engine.until(lambda line: line == 'readyok', 10)
            engine.send('position fen ' + entry['fen'])
            engine.send('isready')
            reply = engine.until(lambda line: line == 'readyok', 10)
            assert not any(line.startswith(('info string invalid FEN:', 'info string invalid position')) for line in reply)
            row['before_search'] = snapshot(engine.process.pid)

            def sample():
                while not stop.is_set():
                    samples.append(snapshot(engine.process.pid))
                    stop.wait(0.1)

            monitor = threading.Thread(target=sample, daemon=True)
            monitor.start()
            go = time.monotonic()
            engine.send('go movetime 1000')
            lines = engine.until(lambda line: line.startswith('bestmove '), 5)
            row['observer_wall_seconds_after_go'] = time.monotonic() - go
            row['after_search'] = snapshot(engine.process.pid)
            row['bestmove'] = next(line for line in reversed(lines) if line.startswith('bestmove '))
            move = chess.Move.from_uci(row['bestmove'].split()[1])
            row['legal'] = move in chess.Board(entry['fen']).legal_moves
            row['answer_match_not_a_screen'] = move.uci() in entry['bm_uci']
            row['last_info'] = next((line for line in reversed(lines) if line.startswith('info depth ')), None)
            row['status'] = 'PASS' if row['legal'] else 'FAIL'
        except Exception as error:
            row['status'] = 'FAIL'
            row['error'] = str(error)
            row['after_fault'] = snapshot(engine.process.pid)
        finally:
            stop.set()
            if monitor is not None:
                monitor.join(timeout=2)
                row['monitor_joined'] = not monitor.is_alive()
                if monitor.is_alive():
                    row['status'] = 'FAIL'
            row['actual_engine_exit'] = engine.close()
            row['usage_after'] = usage()
            row['child_cpu_user_seconds'] = row['usage_after']['ru_utime'] - before_usage['ru_utime']
            row['child_cpu_system_seconds'] = row['usage_after']['ru_stime'] - before_usage['ru_stime']
            row['closed_utc'] = utc()
            if row['actual_engine_exit'] != 0:
                row['status'] = 'FAIL'
            (OUT / name / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
            (OUT / name / 'RESULT.json').write_text(json.dumps(row, indent=2) + '\n')
            cases.append(row)
            print(json.dumps(row), flush=True)
        if row['status'] != 'PASS':
            break
    result = {'status': 'PASS' if len(cases) == 3 and all(row['status'] == 'PASS' for row in cases) else 'FAIL',
              'closed_utc': utc(), 'cases': cases, 'original_wac_status': 'FAILED_UNCHANGED_UNPOOLED',
              'root_cause': 'Not established by this diagnostic; passing cases mean failure was not reproduced here'}
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
