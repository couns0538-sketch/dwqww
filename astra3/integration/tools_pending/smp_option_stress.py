#!/usr/bin/env python3
"""A1: 250 Threads=2 go/stop cycles plus six live option stop/join probes.

Reuses Forge's UCI deadlines, SMP legal-move/ponder checks and raw-stream driver.
No match or performance claim. Engine execution is explicit; --help runs none.
IDEA_SOURCE: user A1 TSan contract and this repository's existing UCI/SMP tests.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'astra3/integration/tests_pending'))
import smp_uci_regression as smp
from option_contract_tests import RawEngine, Suite, parse_options, require, sha256, write_json

PROFILES = (
    ('OFF', 'OFF', False, False, False),
    ('three-independent', 'OFF', True, True, True),
    ('N1-with-independent', 'N1', True, True, True),
    ('N1-only', 'N1', False, False, True),
)
SANITIZER = re.compile(rb'ThreadSanitizer|AddressSanitizer|LeakSanitizer|runtime error:|Sanitizer CHECK failed')


class CapturedRun(smp.Run):
    def __init__(self, executable, seed, directory):
        # Only Run's five initialization fields are adapted. All synchronization,
        # legal/ponder validation, go/answer accounting and grace checks are reused.
        self.e = RawEngine(executable, directory)
        self.rng = random.Random(seed)
        self.legal_cache = {}
        self.stats = {'go': 0, 'bestmove': 0, 'max_stop_latency_s': 0.0,
                      'max_ponderhit_latency_s': 0.0, 'isready_during_search': 0}
        self.passed = []


def positive(value):
    n = float(value)
    if not math.isfinite(n) or n <= 0:
        raise argparse.ArgumentTypeError('must be positive and finite')
    return n


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('engine', type=Path)
    p.add_argument('--out-dir', type=Path, required=True, help='new evidence directory')
    p.add_argument('--iterations', type=int, default=250)
    p.add_argument('--seed', type=int, default=20261029, help='workload scheduling seed, not a gate seed')
    p.add_argument('--timeout', type=positive, default=120.0, help='deadline per UCI response')
    p.add_argument('--sanitizer', choices=('none', 'tsan'), default='none')
    args = p.parse_args(argv)
    p.error('iterations must be at least 250') if args.iterations < 250 else None
    exe = args.engine.resolve(strict=True)
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    before = sha256(exe)
    sources = [Path(__file__), ROOT / 'tools/smp_uci_regression.py', ROOT / 'tools/uci_regression.py',
               ROOT / 'astra3/integration/tests_pending/option_contract_tests.py']
    receipt = {'status': 'RUNNING', 'engine': str(exe), 'binary_sha256_before': before,
               'command': sys.argv, 'iterations_requested': args.iterations, 'seed': args.seed,
               'threads': 2, 'hash_mb': 16, 'ownbook': False, 'timeout_seconds': args.timeout,
               'profiles': PROFILES, 'sanitizer_requested': args.sanitizer,
               'sanitizer_environment': {n: os.environ.get(n) for n in ('TSAN_OPTIONS', 'ASAN_OPTIONS', 'UBSAN_OPTIONS')},
               'source_sha256': {str(x.relative_to(ROOT)): sha256(x) for x in sources},
               'explicit_stop_cycles_completed': 0, 'live_option_joins_completed': 0, 'errors': []}
    write_json(out / 'invocation.json', receipt)
    run = None
    started = time.monotonic()
    try:
        if args.sanitizer == 'tsan':
            require('halt_on_error=1' in os.environ.get('TSAN_OPTIONS', '').split(':'),
                    'TSan run requires TSAN_OPTIONS=halt_on_error=1 (other colon-separated settings allowed)')
            with (out / 'readelf.stdout').open('xb') as so, (out / 'readelf.stderr').open('xb') as se:
                probe = subprocess.run(['readelf', '-Ws', str(exe)], stdout=so, stderr=se, timeout=30)
            require(probe.returncode == 0, 'readelf could not inspect TSan instrumentation')
            require(re.search(rb'\b__tsan_init\b', (out / 'readelf.stdout').read_bytes()) is not None,
                    'binary has no __tsan_init symbol; refusing an uninstrumented TSan claim')
        smp.TIMEOUT = args.timeout
        run = CapturedRun(exe, args.seed, out / 'engine')
        e = run.e
        e.send('uci')
        advertised = parse_options(e.until(lambda line: line == 'uciok', args.timeout))
        for name in ('SmpV2', 'TmSoftHardClamp', 'SingularV2', 'BundlePreset'):
            require(name in advertised, 'required integrated option absent: ' + name)
        validator = SimpleNamespace(options=advertised)
        for name, value in [('Threads', '2'), ('Hash', '16'), ('OwnBook', 'false'), ('Ponder', 'true')]:
            e.send(f'setoption name {name} value {value}')
        run.sync('fixed controls')
        for pos in smp.POSITIONS:
            require(bool(run.legal(pos)), 'legal-move fixture unexpectedly terminal: ' + pos)
        for i in range(args.iterations):
            label, preset, smpv2, tm, singular = PROFILES[i % len(PROFILES)]
            settings = [('BundlePreset', preset), ('SmpV2', str(smpv2).lower()),
                        ('TmSoftHardClamp', str(tm).lower()), ('SingularV2', '1' if singular else '0')]
            for name, value in settings:
                e.send(f'setoption name {name} value {value}')
            run.sync('iteration settings')
            expected = {name: value for name, value in settings[1:] if value not in ('false', '0')}
            if preset == 'N1':
                expected['CorrHistPlus'] = '4'
            pos = run.rng.choice(smp.POSITIONS)
            delay = run.rng.choice((0.0, 0.001, 0.01))
            # The first four profiles and every tenth cycle reach depth 7; this
            # exercises deeper search paths as well as rapid shutdowns.
            depth = 7 if i < 4 or i % 10 == 0 else 3
            command = 'go infinite' if i % 2 == 0 else 'go ponder wtime 100 btime 100 winc 10000 binc 10000'
            transcript_start = len(e.transcript)
            run.go(pos, command)
            lines = e.until(lambda line: line.startswith('bestmove ') or
                            re.match(r'info depth ' + str(depth) + r'\b', line) is not None, args.timeout)
            require(not lines[-1].startswith('bestmove '), 'answer before stop/ponderhit')
            run.wait_without_bestmove(delay, 'pre-stop delay')
            run.sync('isready during search')
            run.stats['isready_during_search'] += 1
            e.send('stop')
            best, ponder = run.answer(pos, 'stop iteration ' + str(i), time.monotonic(), 'max_stop_latency_s')
            wire = [s[2:] for s in e.transcript[transcript_start:] if s.startswith('< ')]
            active = Suite.active(validator, wire)
            require(active == expected, f'profile {label} not active: {active!r} != {expected!r}')
            receipt['explicit_stop_cycles_completed'] += 1
            with (out / 'iterations.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps({'iteration': i, 'profile': label, 'settings': settings, 'position': pos,
                                    'go': command, 'wait_depth': depth, 'delay_seconds': delay,
                                    'bestmove': best, 'ponder': ponder, 'active': active}) + '\n')
        # In addition to the 250 explicit stops, exercise UCI's required stop/join
        # before all three new mutable option assignments, in both directions.
        for name in ('SmpV2', 'TmSoftHardClamp', 'SingularV2'):
            for value in (('0', '1') if name == 'SingularV2' else ('false', 'true')):
                run.go('position startpos', 'go infinite')
                e.until(lambda s: s.startswith('info depth 2 ') or s.startswith('bestmove '), args.timeout)
                e.send(f'setoption name {name} value {value}')
                run.answer('position startpos', 'live assignment ' + name + '=' + value)
                receipt['live_option_joins_completed'] += 1
        require(run.stats['go'] == run.stats['bestmove'] == args.iterations + 6, 'go/bestmove count mismatch')
        require(sum(s.startswith('< bestmove ') for s in e.transcript) == args.iterations + 6,
                'raw bestmove count differs from completed searches')
        bad = [s for s in e.transcript if s.startswith('< ') and
               re.search(r'unknown option|invalid value|\brefused\b|\bERROR\b', s)]
        require(not bad, 'unexpected engine diagnostic: ' + repr(bad[:5]))
    except Exception as error:
        receipt['errors'].append(type(error).__name__ + ': ' + str(error))
    finally:
        if run is not None:
            try:
                run.e.close()
            except Exception as error:
                receipt['errors'].append('cleanup ' + type(error).__name__ + ': ' + str(error))
            receipt['stats'] = run.stats
            stderr = (out / 'engine/stderr.bin').read_bytes()
            stdout = (out / 'engine/stdout.bin').read_bytes()
            receipt['sanitizer_diagnostic_lines'] = [line.decode('utf-8', 'replace') for line in
                (stderr + b'\n' + stdout).splitlines() if SANITIZER.search(line)]
            if receipt['sanitizer_diagnostic_lines']:
                receipt['errors'].append('sanitizer diagnostic(s) captured; see original streams')
        receipt['binary_sha256_after'] = sha256(exe)
        if receipt['binary_sha256_after'] != before:
            receipt['errors'].append('engine binary changed during workload')
        receipt['seconds'] = time.monotonic() - started
        receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
        write_json(out / 'results.json', receipt)
        with (out / 'SHA256SUMS.txt').open('x') as f:
            for path in sorted(out.rglob('*')):
                if path.is_file() and path.name != 'SHA256SUMS.txt':
                    f.write(sha256(path) + '  ' + str(path.relative_to(out)) + '\n')
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
