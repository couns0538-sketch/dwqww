#!/usr/bin/env python3
"""Bounded TT parity/performance diagnostic. No games, clocks, retries or Elo claim.

Example (only after competing jobs stop):
  python3 -B compare-search.py --out /workspace/.cloud-setup/tt-comparison-attempt1
--plan-only writes a preview and starts no executable. A real run requires a new
output directory and freezes the complete schedule before the first engine starts.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shlex
import signal
import statistics
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
BASELINE = Path('/workspace/.cloud-setup/forge-underpromotions-build/forge')
CANDIDATE = Path('/workspace/.cloud-setup/forge-tt-coherent-release/forge')
REPO = Path('/workspace/dwqww')
BLOCKS = 6
NODE_BUDGET = 200_000
WARMUP_BUDGET = 50_000
THREADS = (1, 2, 4)
CASES = (
    ('start', 'startpos', 7),
    ('kiwipete', 'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 6),
    ('middlegame', 'fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10', 6),
    ('endgame', 'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', 7),
    ('promotion_white', 'fen 8/k1P5/2K5/8/8/8/8/8 w - - 0 1', 1),
    ('promotion_black', 'fen 8/8/8/8/8/2k5/K1p5/8 b - - 0 1', 1),
)
PERF_CASES = CASES[:3]
VOLATILE = re.compile(r'\b(time|nps|hashfull)\s+\d+\b')
MOVE = r'[a-h][1-8][a-h][1-8][qrbn]?'
INFO = re.compile(r'^info depth (?P<depth>\d+) seldepth (?P<seldepth>\d+) '
                  r'score (?P<kind>cp|mate) (?P<score>-?\d+)(?: (?P<bound>lowerbound|upperbound))? '
                  r'nodes (?P<nodes>\d+) nps \d+ hashfull \d+ time \d+ pv(?: (?P<pv>.*))?$')
BESTMOVE = re.compile(r'^bestmove (' + MOVE + r')(?: ponder (' + MOVE + r'))?$')
BENCH = re.compile(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+$')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def read_text(path):
    try:
        return {'path': str(path), 'text': Path(path).read_text()}
    except OSError as error:
        return {'path': str(path), 'error': str(error)}


def resources():
    group = read_text('/proc/self/cgroup')
    paths = {Path('/sys/fs/cgroup')}
    for line in group.get('text', '').splitlines():
        if line.startswith('0::'):
            relative = line.split('::', 1)[1]
            if '..' not in Path(relative).parts:
                paths.add(Path('/sys/fs/cgroup') / relative.lstrip('/'))
    return {'monotonic_ns': time.monotonic_ns(), 'affinity': sorted(os.sched_getaffinity(0)),
            'loadavg': list(os.getloadavg()), 'self_cgroup': group,
            'cgroups': [read_text(base / name) for base in sorted(paths)
                        for name in ('cpu.max', 'cpu.stat', 'cpuset.cpus.effective')]}


def process_cpu(pid):
    before = time.monotonic_ns()
    raw = Path(f'/proc/{pid}/stat').read_text()
    # Fields after ')' begin at field3/state; utime/stime are fields14/15.
    fields = raw[raw.rfind(')') + 2:].split()
    return {'sample_begin_ns': before, 'sample_end_ns': time.monotonic_ns(),
            'user_ticks': int(fields[11]), 'system_ticks': int(fields[12]),
            'total_ticks': int(fields[11]) + int(fields[12]), 'raw_stat': raw.rstrip()}


def build_metadata(executable):
    root = executable.parent
    cache = root / 'CMakeCache.txt'
    data = {}
    for line in cache.read_text().splitlines():
        match = re.match(r'^([^/#][^:]*):[^=]+=(.*)$', line)
        if match:
            data[match[1]] = match[2]
    keys = ('CMAKE_BUILD_TYPE', 'CMAKE_CXX_COMPILER', 'CMAKE_CXX_FLAGS',
            'CMAKE_CXX_FLAGS_RELEASE', 'CMAKE_EXE_LINKER_FLAGS',
            'CMAKE_EXE_LINKER_FLAGS_RELEASE', 'FORGE_NATIVE', 'FORGE_ENABLE_SANITIZERS',
            'FORGE_EXPOSE_TUNABLES')
    files = [cache, root / 'CMakeFiles/forge_core.dir/flags.make',
             root / 'CMakeFiles/forge.dir/link.txt']
    files += sorted((root / 'CMakeFiles').glob('*/CMakeCXXCompiler.cmake'))
    return {'path': str(executable), 'sha256': sha(executable),
            'cache_values': {key: data.get(key) for key in keys},
            'build_files': {str(path): {'sha256': sha(path), 'text': path.read_text()}
                            for path in files if path.is_file()}}


def parse_search(lines):
    if not lines or not BESTMOVE.fullmatch(lines[-1]):
        raise ValueError('Search has no syntactically valid nonterminal bestmove')
    infos = []
    for line in lines[:-1]:
        match = INFO.fullmatch(line)
        if not match:
            raise ValueError(f'Unexpected/incomplete search output: {line}')
        item = match.groupdict()
        for key in ('depth', 'seldepth', 'score', 'nodes'):
            item[key] = int(item[key])
        pv = (item['pv'] or '').split()
        if not pv or any(not re.fullmatch(MOVE, move) for move in pv) or item['nodes'] <= 1:
            raise ValueError(f'Search has no real searched PV/child nodes: {line}')
        item['pv'] = pv
        infos.append(item)
    best = BESTMOVE.fullmatch(lines[-1])[1]
    if not infos or infos[-1]['pv'][0] != best:
        raise ValueError('Final searched PV does not agree with bestmove')
    return infos


def normalized_search(lines):
    parse_search(lines)
    return [' '.join(VOLATILE.sub(lambda m: m[1] + ' <normalized>', line).split())
            for line in lines]


def schedule():
    result = []
    for threads in THREADS:
        for block in range(BLOCKS):
            order = ('baseline', 'candidate', 'candidate', 'baseline') if block % 2 == 0 else (
                'candidate', 'baseline', 'baseline', 'candidate')
            positions = [PERF_CASES[(i + block) % len(PERF_CASES)][0]
                         for i in range(len(PERF_CASES))]
            for slot, engine in enumerate(order):
                result.append({'threads': threads, 'block': block, 'slot': slot,
                               'engine': engine, 'positions': positions})
    return result


class Engine:
    """One child, permanent pipe readers, and exactly one wait4 reaper."""
    def __init__(self, executable, directory, threads, cpus, deadline, timeout):
        self.directory = directory
        directory.mkdir()
        self.deadline, self.timeout = deadline, timeout
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.errors = []
        self.events = (directory / 'events.jsonl').open('w')
        self.stdin_raw = (directory / 'stdin.bin').open('wb')
        self.reaped = False
        self.closed = False
        self.returncode = None
        self.rusage = None
        self.search_count = 0
        self.process = None
        self.pid = None
        self.command = [str(executable)]
        self.actual_affinity = None
        self.readers = []
        try:
            self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, start_new_session=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            self.pid = self.process.pid
            for stream in ('stdout', 'stderr'):
                thread = threading.Thread(target=self.reader, args=(stream,), daemon=True)
                thread.start()
                self.readers.append(thread)
            os.sched_setaffinity(self.pid, cpus)
            self.actual_affinity = sorted(os.sched_getaffinity(self.pid))
            write(directory / 'launch.json', {'argv': self.command, 'cwd': os.getcwd(),
                  'threads': threads, 'pid': self.pid, 'affinity': self.actual_affinity,
                  'environment': 'Inherited, with PYTHONDONTWRITEBYTECODE=1; no credential values recorded'})
            self.send('uci')
            self.handshake = self.until(lambda line: line == 'uciok')
            for name in ('Hash', 'Threads', 'OwnBook', 'Ponder'):
                if not any(line.startswith('option name ' + name + ' type ') for _, line in self.handshake):
                    raise ValueError(f'Missing required UCI option {name}')
            for command in ('setoption name Hash value 32', f'setoption name Threads value {threads}',
                            'setoption name OwnBook value false', 'setoption name Ponder value false'):
                self.send(command)
            self.ready()
        except BaseException as error:
            if self.process is not None:
                self.close(force=True)
            else:
                self.stdin_raw.close()
                self.events.close()
                self.closed = True
                write(directory / 'exit.json', {'launch_error': f'{type(error).__name__}: {error}',
                                               'child_started': False})
            raise

    def event(self, stream, **data):
        with self.lock:
            self.events.write(json.dumps({'stream': stream, **data}) + '\n')
            self.events.flush()

    def reader(self, stream):
        buffered = bytearray()
        try:
            with (self.directory / (stream + '.bin')).open('wb') as raw:
                while True:
                    chunk = os.read(getattr(self.process, stream).fileno(), 4096)
                    if not chunk:
                        break
                    observed = time.monotonic_ns()
                    raw.write(chunk)
                    raw.flush()
                    buffered.extend(chunk)
                    if len(buffered) > 1_048_576:
                        raise ValueError(f'{stream} exceeded maximum pending line size')
                    while b'\n' in buffered:
                        line, _, remainder = buffered.partition(b'\n')
                        buffered = bytearray(remainder)
                        stamp = observed
                        text = line.rstrip(b'\r').decode('utf-8')
                        self.event(stream, monotonic_ns=stamp, line=text)
                        if stream == 'stdout':
                            self.q.put((stamp, text))
                if buffered:
                    raise ValueError(f'{stream} ended with a partial line: {buffered[:100]!r}')
        except BaseException as error:
            self.errors.append(f'{stream}: {error}')
        finally:
            if stream == 'stdout':
                self.q.put((time.monotonic_ns(), None))

    def send(self, command):
        data = (command + '\n').encode('ascii')
        self.stdin_raw.write(data)
        self.stdin_raw.flush()
        # Local artifact logging is outside the go-to-bestmove interval.
        stamp = time.monotonic_ns()
        self.process.stdin.write(data)
        self.process.stdin.flush()
        self.event('stdin', monotonic_ns=stamp, line=command)
        return stamp

    def until(self, predicate):
        limit = min(self.deadline, time.monotonic() + self.timeout)
        lines = []
        while True:
            remaining = limit - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Bounded UCI response deadline exceeded')
            try:
                stamp, line = self.q.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError('Bounded UCI response deadline exceeded') from error
            if line is None:
                raise RuntimeError(f'Engine stdout EOF; reader errors={self.errors}')
            lines.append((stamp, line))
            if predicate(line):
                return lines

    def ready(self):
        if not self.q.empty():
            raise ValueError('Unsolicited/stale stdout before readiness fence')
        self.send('isready')
        lines = self.until(lambda line: line == 'readyok')
        if [line for _, line in lines] != ['readyok'] or not self.q.empty():
            raise ValueError(f'Unexpected output at readiness fence: {lines}')

    def search(self, position, command, *, cold):
        if cold:
            self.send('ucinewgame')
        self.send('position ' + position)
        self.ready()
        cpu_before = process_cpu(self.pid)
        started = self.send(command)
        output = self.until(lambda line: line.startswith('bestmove '))
        finished = output[-1][0]
        cpu_after = process_cpu(self.pid)
        lines = [line for _, line in output]
        normalized = normalized_search(lines)
        parsed = parse_search(lines)
        if command.startswith('go depth '):
            depth = int(command.split()[-1])
            if [item['depth'] for item in parsed] != list(range(1, depth + 1)):
                raise ValueError(f'Fixed-depth search did not complete every requested iteration: {lines}')
        if position in (CASES[4][1], CASES[5][1]):
            expected = 'c7c8r' if position == CASES[4][1] else 'c2c1r'
            if BESTMOVE.fullmatch(lines[-1])[1] != expected or parsed[-1]['kind'] != 'cp' or parsed[-1]['score'] <= 100:
                raise ValueError(f'Underpromotion fixture did not choose the searched winning rook: {lines}')
        tick_delta = cpu_after['total_ticks'] - cpu_before['total_ticks']
        record = {'position': position, 'go': command, 'cold': cold, 'go_ns': started,
                  'bestmove_observed_ns': finished, 'wall_seconds': (finished - started) / 1e9,
                  'cpu_before': cpu_before, 'cpu_after': cpu_after,
                  'search_window_cpu_seconds': tick_delta / os.sysconf('SC_CLK_TCK'),
                  'output': lines, 'normalized_output': normalized,
                  'bestmove': lines[-1].split()[1],
                  'last_info': next(line for line in reversed(lines) if line.startswith('info depth ')),
                  'parsed_info': parsed, 'last_info_nodes_not_final_work': parsed[-1]['nodes']}
        if tick_delta < 0 or record['wall_seconds'] <= 0:
            raise ValueError('Invalid process accounting/timestamps')
        write(self.directory / f'search-{self.search_count:03}.json', record)
        self.search_count += 1
        self.ready()  # Reject trailing duplicate results before another search.
        return record

    def bench(self):
        self.ready()
        cpu_before = process_cpu(self.pid)
        started = self.send('bench 11')
        output = self.until(lambda line: bool(BENCH.fullmatch(line)))
        cpu_after = process_cpu(self.pid)
        if len(output) != 1:
            raise ValueError(f'Unexpected benchmark output: {output}')
        match = BENCH.fullmatch(output[-1][1])
        self.ready()
        return {'command': 'bench 11', 'internal_hash_mib': 16, 'internal_threads': 1,
                'nodes': int(match[1]), 'output': [line for _, line in output],
                'normalized_output': VOLATILE.sub(lambda m: m[1] + ' <normalized>', output[-1][1]),
                'wall_seconds': (output[-1][0] - started) / 1e9,
                'cpu_before': cpu_before, 'cpu_after': cpu_after}

    def close(self, force=False):
        if self.closed:
            return
        self.closed = True
        failure = None

        def kill_owned_group():
            try:
                os.killpg(self.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        def collect(status, usage):
            self.reaped = True
            self.returncode = os.waitstatus_to_exitcode(status)
            self.process.returncode = self.returncode
            self.rusage = {key: getattr(usage, key) for key in (
                'ru_utime', 'ru_stime', 'ru_maxrss', 'ru_minflt', 'ru_majflt',
                'ru_nvcsw', 'ru_nivcsw')}

        try:
            if force:
                kill_owned_group()
            else:
                try:
                    self.send('quit')
                except OSError as error:
                    # Even an already-dead child must be reaped exactly once.
                    failure = error
                    kill_owned_group()
            limit = min(self.deadline, time.monotonic() + 5)
            while not self.reaped:
                pid, status, usage = os.wait4(self.pid, os.WNOHANG)
                if pid:
                    collect(status, usage)
                    break
                if time.monotonic() >= limit:
                    kill_owned_group()
                    _, status, usage = os.wait4(self.pid, 0)
                    collect(status, usage)
                    failure = TimeoutError('Child required forced termination at shutdown')
                    break
                time.sleep(.01)
        except BaseException as error:
            failure = failure or error
            kill_owned_group()
            if not self.reaped:
                try:
                    _, status, usage = os.wait4(self.pid, 0)
                    collect(status, usage)
                except ChildProcessError as missing:
                    self.errors.append(f'Lost sole-reaper child accounting: {missing}')
        finally:
            for thread in self.readers:
                thread.join(timeout=2)
                if thread.is_alive():
                    self.errors.append('Pipe reader failed to stop after child shutdown')
            while True:
                try:
                    _, line = self.q.get_nowait()
                except queue.Empty:
                    break
                if line is not None:
                    self.errors.append(f'Unsolicited/trailing stdout at shutdown: {line}')
            self.stdin_raw.close()
            self.events.close()
            for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
                pipe.close()
            write(self.directory / 'exit.json', {'exit_code': self.returncode,
                  'rusage': self.rusage, 'whole_session_cpu_scope':
                  'wait4 user+system CPU for entire process including all helpers, handshake, hash clears and exit',
                  'reader_errors': self.errors, 'forced_cleanup_requested': force,
                  'cleanup_error': None if failure is None else f'{type(failure).__name__}: {failure}'})
        if not force:
            if failure:
                raise failure
            if self.returncode != 0 or self.rusage is None or self.errors or (self.directory / 'stderr.bin').stat().st_size:
                raise RuntimeError(f'Invalid engine exit/stderr/reader state; inspect {self.directory}')


def run_session(executable, directory, threads, cpus, deadline, timeout, operation):
    if time.monotonic() >= deadline:
        raise TimeoutError('Overall deadline reached before next session; no replacement/retry')
    engine = Engine(executable, directory, threads, cpus, deadline, timeout)
    try:
        result = operation(engine)
        engine.close()
    except BaseException:
        engine.close(force=True)
        raise
    result['whole_session_rusage'] = engine.rusage
    result['whole_session_cpu_seconds'] = engine.rusage['ru_utime'] + engine.rusage['ru_stime']
    write(directory / 'result.json', result)
    return result


def distributions(values):
    return {'samples': values, 'count': len(values), 'median': statistics.median(values),
            'geometric_mean': math.exp(statistics.mean(math.log(value) for value in values)),
            'minimum': min(values), 'maximum': max(values)}


def summarize(records):
    result = {}
    for threads in THREADS:
        ratios = {'requested_budget_per_wall_second_ratio': [],
                  'requested_budget_per_search_cpu_second_ratio': [],
                  'whole_session_cpu_ratio_including_setup': []}
        blocks = []
        for block in range(BLOCKS):
            selected = [r for r in records if r['threads'] == threads and r['block'] == block]
            if len(selected) != 4:
                continue
            totals = {}
            for engine in ('baseline', 'candidate'):
                runs = [r for r in selected if r['engine'] == engine]
                totals[engine] = {'wall': sum(s['wall_seconds'] for r in runs for s in r['searches']),
                                 'cpu': sum(s['search_window_cpu_seconds'] for r in runs for s in r['searches']),
                                 'session_cpu': sum(r['whole_session_cpu_seconds'] for r in runs)}
            block_result = {'block': block, 'totals': totals}
            for key, metric in [('requested_budget_per_wall_second_ratio', 'wall'),
                                ('requested_budget_per_search_cpu_second_ratio', 'cpu'),
                                ('whole_session_cpu_ratio_including_setup', 'session_cpu')]:
                value = totals['baseline'][metric] / totals['candidate'][metric] if totals['candidate'][metric] else None
                block_result[key] = value
                if value and value > 0:
                    ratios[key].append(value)
            blocks.append(block_result)
        result[str(threads)] = {'blocks': blocks,
            'ratios': {key: distributions(values) if values else None for key, values in ratios.items()},
            'interpretation': 'Ratio>1 favors candidate. Six block aggregates, not individual searches, are comparison units. SMP uses equal requested node budgets with variable trees/stopping overshoot; conditional throughput only.'}
    return result


def hash_errors(frozen):
    errors = []
    for path, expected in frozen.items():
        try:
            actual = sha(path)
        except OSError as error:
            errors.append({'path': path, 'expected': expected, 'error': str(error)})
        else:
            if actual != expected:
                errors.append({'path': path, 'expected': expected, 'actual': actual})
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    parser.add_argument('--candidate', type=Path, default=CANDIDATE)
    parser.add_argument('--out', type=Path, required=True, help='New output directory; never resumed')
    parser.add_argument('--cpus', help='Frozen comma-separated CPU affinity; default inherited permitted set')
    parser.add_argument('--response-timeout', type=float, default=30)
    parser.add_argument('--overall-timeout', type=float, default=480)
    parser.add_argument('--plan-only', action='store_true', help='Write preview only; start no executable')
    parser.add_argument('--parity-only', action='store_true', help='Only cold/warm one-thread exact output and bench11; no throughput phase')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'planning', 'elo_claim': None, 'parity_passed': False, 'performance_complete': False}
    frozen = {}
    records = []
    def terminate(signum, frame):
        raise KeyboardInterrupt(f'Received signal {signum}')
    signal.signal(signal.SIGTERM, terminate)
    started = time.monotonic()
    deadline = started + args.overall_timeout
    try:
        cpus = set(map(int, args.cpus.split(','))) if args.cpus else set(os.sched_getaffinity(0))
        if not cpus or not cpus <= set(os.sched_getaffinity(0)):
            raise ValueError('CPU mask must be nonempty and within permitted inherited affinity')
        if not 0 < args.response_timeout <= args.overall_timeout <= 900:
            raise ValueError('Require 0 < response timeout <= overall timeout <=900 seconds')
        plan = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'kind': 'TT exact-behavior parity and conditional requested-budget throughput; not games/Elo',
            'mode': 'parity_only' if args.parity_only else 'parity_then_performance',
            'driver_sha256': sha(Path(__file__)), 'argv': sys.argv, 'cwd': os.getcwd(),
            'engines': {'baseline': str(args.baseline.resolve()), 'candidate': str(args.candidate.resolve())},
            'settings': {'hash_mib': 32, 'ownbook': False, 'ponder': False, 'cpus': sorted(cpus),
                         'threads': list(THREADS), 'blocks_per_thread': BLOCKS,
                         'nodes_per_performance_search': NODE_BUDGET,
                         'warmup_nodes': WARMUP_BUDGET, 'performance_searches': 0 if args.parity_only else len(schedule()) * 3,
                         'response_timeout_seconds': args.response_timeout,
                         'overall_timeout_seconds': args.overall_timeout},
            'parity': {'threads': 1, 'cases': CASES, 'passes': ['cold', 'warm'],
                       'normalize_only': ['time', 'nps', 'hashfull'],
                       'compare': 'All ordered depth/seldepth/score/bound/nodes/PV/bestmove records'},
            'bench': {'command_via_stdin': 'bench 11', 'hash_mib': 16, 'threads': 1,
                      'expected_baseline_nodes': 419798, 'must_match': 'candidate node signature'},
            'warmups': [] if args.parity_only else [{'threads': n, 'engine': e, 'position': 'start', 'nodes': WARMUP_BUDGET}
                        for n in THREADS for e in ('baseline', 'candidate')],
            'schedule': [] if args.parity_only else schedule(), 'resource_before': resources(),
            'cpu_accounting': {'clock_ticks_per_second': os.sysconf('SC_CLK_TCK'),
                'search_window': '/proc/tgid/stat user+system tick deltas sampled before go and after bestmove; aggregate all process threads',
                'high_resolution': 'wait4 rusage for whole session includes setup, hash clears and exit; separate estimand',
                'endpoint': 'monotonic timestamp of go before write/flush to reader-observed bestmove; includes transport/observer scheduling',
                'node_limit': 'Last UCI info nodes is NOT final work accounting. Rates use requested budget units; helper overshoot and variable SMP trees prevent exact-node NPS or equal-quality claims.',
                'cgroup': 'Shared-cgroup counter deltas are diagnostic only, not engine-specific CPU'},
            'session_setup_commands': ['uci', 'setoption name Hash value 32', 'setoption name Threads value <frozen_threads>', 'setoption name OwnBook value false', 'setoption name Ponder value false', 'isready'],
            'search_commands': {'cold_prefix': ['ucinewgame', 'position <frozen_position>', 'isready'], 'warm_prefix': ['position <same_position>', 'isready'], 'fixed_depth': ['go depth ' + str(case[2]) for case in CASES], 'performance': 'go nodes 200000', 'shutdown': 'quit'},
            'stopping_rule': 'No retries, substitutions, trimming or adaptive counts. Parity/bench mismatch or any timeout/error aborts the attempt. All six blocks for each of1/2/4threads required for complete performance status.'}
        write(args.out / 'plan.json', plan)
        if args.plan_only:
            result['status'] = 'plan_only_no_executables_started'
            return 0
        engines = {'baseline': args.baseline.resolve(strict=True), 'candidate': args.candidate.resolve(strict=True)}
        metadata = {name: build_metadata(path) for name, path in engines.items()}
        cache = [metadata[name]['cache_values'] for name in ('baseline', 'candidate')]
        if cache[0] != cache[1] or cache[0]['CMAKE_BUILD_TYPE'] != 'Release':
            raise ValueError('Release compiler/flags/options differ; inspect build metadata')
        for name, info in metadata.items():
            values = info['cache_values']
            actual = ' '.join(item['text'] for path, item in info['build_files'].items()
                              if path.endswith(('flags.make', 'link.txt')))
            flags = shlex.split(' '.join(values.get(key) or '' for key in (
                'CMAKE_CXX_FLAGS', 'CMAKE_CXX_FLAGS_RELEASE', 'CMAKE_EXE_LINKER_FLAGS',
                'CMAKE_EXE_LINKER_FLAGS_RELEASE')))
            if (values['FORGE_ENABLE_SANITIZERS'] != 'OFF'
                    or not {'-fno-fast-math', '-ffp-contract=off'} <= set(flags)
                    or '-fsanitize' in actual
                    or any(flag in ('-ffast-math', '-Ofast') or flag.startswith('-fsanitize')
                           or (flag.startswith('-ffp-contract=') and flag != '-ffp-contract=off')
                           for flag in flags)):
                raise ValueError(f'Expected non-sanitized floating-point-preserving Release flags: {name}')
        frozen = {info['path']: info['sha256'] for info in metadata.values()}
        for info in metadata.values():
            frozen.update({path: item['sha256'] for path, item in info['build_files'].items()})
        frozen[str(Path(__file__).resolve())] = plan['driver_sha256']
        write(args.out / 'inputs.json', {'engines': metadata, 'frozen_sha256': frozen})
        if hash_errors(frozen):
            raise ValueError('Inputs changed during preflight; no engine started')
        write(args.out / 'status.json', dict(result, status='parity_running'))
        for label, position, depth in CASES:
            pair = {}
            for name in ('baseline', 'candidate'):
                pair[name] = run_session(engines[name], args.out / f'parity-{label}-{name}', 1, cpus,
                    deadline, args.response_timeout, lambda engine, p=position, d=depth: {
                        'cold': engine.search(p, f'go depth {d}', cold=True),
                        'warm': engine.search(p, f'go depth {d}', cold=False)})
            for mode in ('cold', 'warm'):
                if pair['baseline'][mode]['normalized_output'] != pair['candidate'][mode]['normalized_output']:
                    raise ValueError(f'Exact one-thread {mode} parity mismatch: {label}')
        benchmarks = {}
        for name in ('baseline', 'candidate'):
            benchmarks[name] = run_session(engines[name], args.out / f'bench-{name}', 1, cpus,
                deadline, args.response_timeout, lambda engine: {'bench': engine.bench()})
        nodes = [benchmarks[name]['bench']['nodes'] for name in ('baseline', 'candidate')]
        if nodes != [419798, 419798]:
            raise ValueError(f'Unexpected or mismatched bench11 signature: {nodes}')
        result['parity_passed'] = True
        if args.parity_only:
            result['status'] = 'parity_only_completed'
            return 0
        write(args.out / 'status.json', dict(result, status='performance_running'))
        by_name = {case[0]: case for case in PERF_CASES}
        for threads in THREADS:
            for name in ('baseline', 'candidate'):
                run_session(engines[name], args.out / f'warmup-t{threads}-{name}', threads, cpus,
                    deadline, args.response_timeout, lambda engine: {
                        'searches': [engine.search('startpos', f'go nodes {WARMUP_BUDGET}', cold=True)],
                        'excluded_from_performance_summary': True})
            for item in [x for x in schedule() if x['threads'] == threads]:
                before = resources()
                name = item['engine']
                directory = args.out / f"perf-t{threads}-b{item['block']:02}-s{item['slot']}-{name}"
                measured = run_session(engines[name], directory, threads, cpus, deadline,
                    args.response_timeout, lambda engine, positions=item['positions']: {
                        'searches': [dict(engine.search(by_name[label][1], f'go nodes {NODE_BUDGET}', cold=True),
                                          position_name=label, requested_nodes=NODE_BUDGET)
                                     for label in positions]})
                records.append(dict(item, **measured, resource_before=before, resource_after=resources()))
                write(args.out / 'performance-raw.json', records)
                write(args.out / 'status.json', dict(result, status='performance_running', completed_sessions=len(records)))
        result.update(status='completed', performance_complete=True,
                      performance=summarize(records), completed_sessions=len(records))
        return 0
    except BaseException as error:
        result.update(status='failed_or_interrupted', error=f'{type(error).__name__}: {error}',
                      partial_completed_sessions=len(records))
        return 1
    finally:
        result['elapsed_seconds'] = time.monotonic() - started
        result['resource_after'] = resources()
        result['input_hash_errors'] = hash_errors(frozen) if frozen else []
        result['input_hashes_unchanged'] = not result['input_hash_errors'] if frozen else None
        if frozen and not result['input_hashes_unchanged']:
            result.update(status='failed_or_interrupted', performance_complete=False)
            result.setdefault('error', 'Frozen input hash changed')
        result['interpretation'] = 'Correctness parity and conditional throughput only. Shared-VM noise, CPU tick quantization and SMP variable work remain limitations. No Elo, equal-clock or native Ryzen claim.'
        write(args.out / 'result.json', result)
        print(json.dumps({'status': result['status'], 'parity_passed': result['parity_passed'],
                          'performance_complete': result['performance_complete'], 'output': str(args.out)}), flush=True)
        if frozen and not result['input_hashes_unchanged']:
            return 1


if __name__ == '__main__':
    raise SystemExit(main())
