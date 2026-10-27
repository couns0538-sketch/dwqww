"""ADVICE: collect fixed-work search counters, never strength or dead-code proof (S08 v2).

v2 (S08fix; v1 = Sol's forge_sol_S08_collect_profiles_substitute_20261026.py @ 17aa0cae, unchanged):
- bench pins are arguments (--bench11-nodes / --bench20-nodes), default the AL1 lock (312866 / 12389307);
  v1 hard-coded Sol's development base (308972 / 11901452) and refused AL1 builds;
- S08-4: the firing tables drop events whose feature is disabled by a default-zero tuning constant
  (capture_futility_prunes: tune::CaptureFutilityBase = 0) from the rare-event rows and list them in their own
  section; the table states the corpus limit (substitute corpus, not the specified 2,000 WAC/STS set).

Standard library only. Native execution is explicit through --engine; importing
or checking corpus metadata never launches a process. A timeout aborts a broken
operation; it never supplies a wall-time search limit. Corpus coverage defaults
to 2,000 unique WAC/STS positions. Explicit handoff-authorized BENCH/OPENING
substitutes are separately labelled and never acquire WAC/STS identity. The supplied WAC300 alone requires
--allow-incomplete and is labelled LIMITED_INCOMPLETE.
"""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import queue
import selectors
import signal
import threading
import stat
import subprocess
import sys
import time

DATE = '20261026'
DEFAULT_BENCH11_NODES = 312866    # AL1 lock pins (forge-engine-verify)
DEFAULT_BENCH20_NODES = 12389307
# S08-4: events whose feature the locked defaults switch off; a zero count is not a dead-feature finding.
DISABLED_BY_DEFAULT = {
    'capture_futility_prunes': 'tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune '
                               'requires CaptureFutilityBase > 0, the opportunity counter runs before that guard',
}
CORPUS_LIMIT = ('Corpus limit: the specified 2,000 WAC/STS set is not available (no STS file exists on the PC); '
                'this run uses Sol\'s sealed substitute corpus: 300 WAC + 7 bench + 1,693 synthetic opening '
                'positions, 2,000 distinct. It is not a WAC/STS corpus.')
SUBSTITUTION_AUTHORITY_SHA256 = '11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2'
WAC_SHA256 = '9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46'
U64_MAX = 2**64-1
# Exact schema-1 registry frozen from the original S08 profile descriptions.
COUNTERS = dict((name, denominator) for denominator, names in (
    ('nodes', 'nodes main_nodes qs_nodes eval_requests tt_probes picker_visits'),
    ('eval_requests', 'hce_computations nnue_forward'),
    ('nnue_forward', 'nnue_refresh'),
    ('tt_probes', 'tt_hits tt_misses'),
    ('picker_visits', 'picker_main_tt picker_generate_captures picker_good_captures picker_killer1 picker_killer2 picker_counter_move picker_generate_quiets picker_quiet_moves picker_bad_captures picker_qs_tt picker_qs_generate picker_qs_captures picker_evasion_tt picker_evasion_generate picker_evasions'),
    ('main_nodes', 'razor_checks probcut_checks iir_checks lmp_checks futility_checks capture_futility_checks history_checks quiet_see_checks noisy_see_checks singular_checks'),
    ('razor_checks', 'razor_searches'), ('razor_searches', 'razor_cutoffs'),
    ('probcut_checks', 'probcut_searches'), ('probcut_searches', 'probcut_cutoffs'),
    ('iir_checks', 'iir_reductions'), ('lmp_checks', 'lmp_activations'),
    ('futility_checks', 'futility_prunes'), ('capture_futility_checks', 'capture_futility_prunes'),
    ('history_checks', 'history_prunes'), ('quiet_see_checks', 'quiet_see_prunes'),
    ('noisy_see_checks', 'noisy_see_prunes'), ('qs_nodes', 'qs_futility_checks qs_see_checks'),
    ('qs_futility_checks', 'qs_futility_prunes'), ('qs_see_checks', 'qs_see_prunes'),
    ('singular_checks', 'singular_searches'),
    ('singular_searches', 'singular_extensions singular_double_extensions singular_cutoffs'),
) for name in names.split())
if len(COUNTERS) != 55:
    raise RuntimeError('schema 1 requires exactly 55 counters')

HEADER = re.compile(r'info string prof schema 1 scope search_only setup_excluded 1 overflow ([01])$')
COUNTER_LINE = re.compile(r'info string prof ([a-z0-9_]+) count (\d+) denominator ([a-z0-9_]+) opportunities (\d+) pct (unknown|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)$')
BENCH = re.compile(r'info string bench depth (\d+) nodes (\d+)(?: .*)?$')
MOVE = re.compile(r'bestmove (?:[a-h][1-8][a-h][1-8][nbrq]?|0000)(?: ponder [a-h][1-8][a-h][1-8][nbrq]?)?$')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def parse_packet(lines, *, registry=COUNTERS, terminal='bestmove'):
    """Validate one complete schema-1 packet and its actual denominator counts.

    Counts need not be smaller than opportunities: some events can occur more
    than once per opportunity. Unknown percentages are required for zero
    opportunities or overflow. Printed percentages are checked at the source's
    default six-significant-digit precision; reported rates use integer counts.
    """
    lines = [line.rstrip('\r\n') for line in lines]
    terminals = [i for i, line in enumerate(lines)
                 if (MOVE.fullmatch(line) if terminal == 'bestmove' else BENCH.fullmatch(line))]
    if len(terminals) != 1:
        raise ValueError('expected exactly one valid ' + terminal + ' terminal')
    end = terminals[0]
    # The controller sends exactly one explicit isready fence after a terminal.
    # Any other trailing bytes represented by lines are delayed/unexpected logs.
    if lines[end+1:] not in ([], ['readyok']):
        raise ValueError('unexpected stdout after terminal; only one explicit readyok fence is allowed')
    headers = [(i, HEADER.fullmatch(line)) for i, line in enumerate(lines) if 'info string prof schema ' in line]
    if len(headers) != 1 or headers[0][1] is None or headers[0][0] >= end:
        raise ValueError('missing, duplicate, invalid or late profile schema header')
    begin, header = headers[0]
    overflow = header.group(1) == '1'
    counters = {}
    printed = {}
    for i, line in enumerate(lines):
        if not line.startswith('info string prof ') or i == begin:
            continue
        match = COUNTER_LINE.fullmatch(line)
        if match is None or not begin < i < end:
            raise ValueError('malformed profile counter or profile output after terminal')
        name, count, denominator, opportunities, pct = match.groups()
        count, opportunities = int(count), int(opportunities)
        if name not in registry or name in counters or denominator != registry[name]:
            raise ValueError('unknown/duplicate event or incorrect denominator: ' + name)
        if count > U64_MAX or opportunities > U64_MAX:
            raise ValueError('counter is outside uint64 range')
        unknown = opportunities == 0 or overflow
        if (pct == 'unknown') != unknown:
            raise ValueError('percentage must be unknown exactly for overflow or zero opportunities')
        rate = None if unknown else 100 * count / opportunities
        if not unknown and not math.isclose(float(pct), rate, rel_tol=5e-6, abs_tol=1e-12):
            raise ValueError('printed percentage disagrees with numerator/opportunities')
        counters[name] = {'count': count, 'denominator': denominator,
                          'opportunities': opportunities, 'pct': rate}
        printed[name] = pct
    if set(counters) != set(registry):
        raise ValueError('packet missing required counters: ' + ','.join(sorted(set(registry)-set(counters))))
    for event, row in counters.items():
        if row['opportunities'] != counters[row['denominator']]['count']:
            raise ValueError('opportunities disagree with actual denominator counter: ' + event)
    if not overflow and {'nodes','main_nodes','qs_nodes'} <= set(counters):
        if counters['main_nodes']['count']+counters['qs_nodes']['count'] != counters['nodes']['count']:
            raise ValueError('main_nodes + qs_nodes disagree with nodes')
    if not overflow and {'tt_probes','tt_hits','tt_misses'} <= set(counters):
        if counters['tt_hits']['count']+counters['tt_misses']['count'] != counters['tt_probes']['count']:
            raise ValueError('TT hits + misses disagree with probes')
    stages = [name for name in registry if name.startswith('picker_') and name != 'picker_visits']
    if not overflow and len(stages) == 15 and 'picker_visits' in counters:
        if sum(counters[name]['count'] for name in stages) != counters['picker_visits']['count']:
            raise ValueError('picker stage counts disagree with picker visits')
    return {'schema': 1, 'scope': 'search_only', 'setup_excluded': True,
            'overflow': overflow, 'counters': counters, 'printed_pct': printed}


def verify_profile_work(packet, *, expected_nodes=None, node_limit=None):
    """Check bench node pins or a fixed-node budget against the final snapshot.

    Iteration info is intentionally not used: an interrupted iteration can add
    nodes after the last completed-iteration info line. Threads is fixed at one.
    """
    observed = packet['counters']['nodes']['count']
    if expected_nodes is not None and observed != expected_nodes:
        raise ValueError('profile nodes disagree with canonical bench nodes')
    if node_limit is not None and observed > node_limit:
        raise ValueError('profile nodes exceeded fixed single-thread node budget')


def firing_table(packets):
    """Aggregate integer events/opportunities, preserving undefined frequencies."""
    if not packets:
        return []
    registry = {name: row['denominator'] for name, row in packets[0]['counters'].items()}
    totals = {name: [0, 0] for name in registry}
    overflow = any(packet['overflow'] for packet in packets)
    for packet in packets:
        if {n: r['denominator'] for n, r in packet['counters'].items()} != registry:
            raise ValueError('cannot aggregate different counter schemas')
        for name, row in packet['counters'].items():
            totals[name][0] += row['count']
            totals[name][1] += row['opportunities']
    rows = []
    for name, (count, opportunities) in totals.items():
        pct = None if overflow or opportunities == 0 else 100 * count / opportunities
        disabled = DISABLED_BY_DEFAULT.get(name)
        rows.append({'event': name, 'count': count, 'denominator': registry[name],
                     'opportunities': opportunities, 'pct': pct, 'overflow': overflow,
                     'rare_below_0_1_pct': None if pct is None or disabled else pct < .1,
                     'disabled_by_default': disabled,
                     'interpretation': 'ADVICE; frequency is not strength or dead-code proof'})
    return rows


def _epd(line, kind):
    fields = line.split()
    if len(fields) < 5:
        raise ValueError('EPD needs four board fields and benchmark operations')
    ranks = fields[0].split('/')
    if (len(ranks) != 8 or any(not re.fullmatch('[prnbqkPRNBQK1-8]+', rank)
            or sum(int(c) if c.isdigit() else 1 for c in rank) != 8 for rank in ranks)
            or fields[0].count('K') != 1 or fields[0].count('k') != 1
            or fields[1] not in ('w', 'b')
            or not re.fullmatch(r'(?:-|K?Q?k?q?)', fields[2])
            or not re.fullmatch(r'(?:-|[a-h][36])', fields[3])):
        raise ValueError('invalid EPD board-field syntax')
    identity = re.search(r'\bid\s+"([^"\r\n]+)"\s*;', line)
    if identity is None or (kind in ('WAC', 'STS') and re.search(r'\bbm\s+[^;]+;', line) is None):
        raise ValueError('benchmark EPD requires id and bm operations')
    pid = identity.group(1)
    if (kind == 'WAC' and not re.fullmatch(r'WAC\.\d+', pid)) or (kind == 'STS' and not pid.startswith('STS')):
        raise ValueError('benchmark id disagrees with declared WAC/STS class')
    return {'id': pid, 'fen4': ' '.join(fields[:4]), 'fen': ' '.join(fields[:4])+' 0 1', 'kind': kind}


def corpus_metadata(suites, *, required=2000, allow_incomplete=False, manifest=None):
    """Accept canonical WAC or explicitly supplied hash/provenance declarations.

    External provenance is caller-declared, not independently authenticated.
    External EPDs receive syntax checks, not a claim of legal bm/SAN validation.
    Filenames never establish benchmark identity. BENCH/OPENING require explicit
    pinned handoff authorization; training corpora remain rejected. Duplicate FEN4 boards count once, including across corpus files.
    """
    if isinstance(required, bool) or not isinstance(required, int) or required < 1:
        raise ValueError('required positions must be a positive integer')
    authorization = (manifest or {}).get('authorization', {})
    substitutes_authorized = (isinstance(authorization, dict)
          and authorization.get('kind') == 'handoff_S08_opening_substitution'
          and authorization.get('sha256') == SUBSTITUTION_AUTHORITY_SHA256)
    allowed_kinds = ('WAC', 'STS', 'BENCH', 'OPENING') if substitutes_authorized else ('WAC', 'STS')
    declared = (manifest or {}).get('corpora', [])
    if not isinstance(declared, list):
        raise ValueError('manifest corpora must be a list')
    entries = {}
    for entry in declared:
        key = str(Path(entry['path']).resolve())
        if key in entries:
            raise ValueError('duplicate manifest path')
        entries[key] = entry
    sources, positions, seen = [], [], set()
    for raw in suites:
        path = Path(raw).resolve(strict=True)
        digest = sha256(path)
        canonical = digest == WAC_SHA256
        if canonical:
            kind, source = 'WAC', 'frozen canonical WAC.001-300; SHA256-pinned supplied benchmark'
        else:
            entry = entries.get(str(path), {})
            kind, source = entry.get('kind'), entry.get('source')
            if (kind not in allowed_kinds or not isinstance(source, str) or not source.strip()
                    or entry.get('sha256') != digest):
                raise ValueError('noncanonical corpus requires matching SHA256 and declared WAC/STS benchmark provenance: '+str(path))
        rows = []
        ids = set()
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            try:
                row = _epd(line, kind)
            except ValueError as exc:
                raise ValueError(str(path)+':'+str(number)+': '+str(exc)) from exc
            if row['id'] in ids:
                raise ValueError('duplicate benchmark id within corpus: '+row['id'])
            ids.add(row['id'])
            rows.append(row)
            if row['fen4'] not in seen:
                seen.add(row['fen4'])
                positions.append({**row, 'source_sha256': digest})
        if canonical and (len(rows) != 300 or ids != {'WAC.%03d'%i for i in range(1,301)}):
            raise ValueError('canonical WAC identity mismatch')
        sources.append({'path': str(path), 'sha256': digest, 'bytes': path.stat().st_size,
                        'kind': kind, 'source': source, 'rows': len(rows),
                        'unique_fen4': len({r['fen4'] for r in rows}),
                        'provenance': 'canonical_hash' if canonical else 'caller_declared_hash_and_source',
                        'validation': 'canonical bytes previously independently legality-checked' if canonical else 'EPD field syntax only; bm legality unverified'})
    gap = max(0, required-len(positions))
    wac_sts_count = sum(row['kind'] in ('WAC', 'STS') for row in positions)
    has_substitutes = any(row['kind'] in ('BENCH', 'OPENING') for row in positions)
    if not positions:
        raise ValueError('no genuine declared WAC/STS positions supplied')
    result = {'sources': sources, 'positions': positions, 'unique_positions': len(positions),
              'required_positions': required, 'coverage_gap': gap,
              'coverage_status': 'LIMITED_INCOMPLETE' if gap else ('COMPLETE_AUTHORIZED_SUBSTITUTE' if has_substitutes else 'COMPLETE'),
              'wac_sts_only_positions': wac_sts_count,
              'wac_sts_only_coverage_gap': max(0, required-wac_sts_count),
              'substitute_authorization': authorization if has_substitutes else None,
              'deduplication': 'exact normalized FEN first four fields; no padding',
              'opening_or_training_boards_counted': has_substitutes,
              'training_boards_counted': False}
    if gap and not allow_incomplete:
        raise ValueError('genuine WAC/STS coverage missing '+str(gap)+' positions; explicit --allow-incomplete required for a limited screen')
    return result


def exclusive_directory(path):
    """Refuse existing output and every existing symlink ancestor."""
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ValueError('output path cannot contain parent traversal')
    for parent in [*reversed(path.parents), path]:
        try:
            mode = parent.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError('output path has a symlink ancestor: '+str(parent))
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path


def validate_limits(depth, nodes):
    if (depth is None) == (nodes is None):
        raise ValueError('supply exactly one fixed --depth or --nodes limit')
    value = depth if depth is not None else nodes
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError('depth/nodes limit must be a positive integer')
    return 'go '+('depth ' if depth is not None else 'nodes ')+str(value)


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


class _Process:
    """Pipe controller preserving raw bytes and a receipt, including failures."""
    def __init__(self, command, out, label, timeout, max_capture_bytes):
        self.command, self.out, self.label = list(command), out, label
        self.timeout, self.max_bytes = timeout, max_capture_bytes
        self.total, self.complete, self.closed = 0, True, False
        self.lines, self.pending = collections.deque(), b''
        self.handles = {s: (out/(label+'.'+s)).open('xb') for s in ('stdin','stdout','stderr')}
        self.receipt = {'command': self.command, 'cwd': os.getcwd(), 'operational_timeout_seconds': timeout,
                        'returncode': None, 'stdout_complete': True, 'stderr_complete': True}
        try:
            self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, start_new_session=True)
        except BaseException as exc:
            self.receipt['launch_error'] = type(exc).__name__+': '+str(exc)
            self.close(False)
            raise
        self.receipt['pid'] = self.proc.pid
        if os.name == 'nt':
            # v2: no select() on Windows pipes; reader threads feed one queue.
            self.selector, self.queue, self.live = None, queue.Queue(), {'stdout', 'stderr'}
            for name in ('stdout', 'stderr'):
                threading.Thread(target=self._reader, args=(name,), daemon=True).start()
        else:
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.proc.stdout, selectors.EVENT_READ, 'stdout')
            self.selector.register(self.proc.stderr, selectors.EVENT_READ, 'stderr')

    def _reader(self, name):
        stream = getattr(self.proc, name)
        while True:
            try:
                data = os.read(stream.fileno(), 65536)
            except OSError:
                data = b''
            self.queue.put((name, data))
            if not data:
                return

    def _open_streams(self):
        return bool(self.live) if self.selector is None else bool(self.selector.get_map())

    def send(self, command):
        data = (command+'\n').encode('utf-8')
        self.handles['stdin'].write(data)
        self.handles['stdin'].flush()
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def _pump(self, wait=.05):
        if self.selector is None:
            events = []
            try:
                events.append(self.queue.get(timeout=wait))
                while True:
                    events.append(self.queue.get_nowait())
            except queue.Empty:
                pass
        else:
            events = [(key.data, os.read(key.fileobj.fileno(), 65536), key.fileobj)
                      for key, _ in self.selector.select(wait)]
        for event in events:
            name, data = event[0], event[1]
            if not data:
                if self.selector is None:
                    self.live.discard(name)
                else:
                    self.selector.unregister(event[2])
                if name == 'stdout' and self.pending:
                    self.lines.append(self.pending.decode('utf-8'))
                    self.pending = b''
                continue
            remaining = self.max_bytes-self.total
            self.total += len(data)
            if self.total > self.max_bytes:
                if remaining > 0:
                    self.handles[name].write(data[:remaining])
                    self.handles[name].flush()
                self.complete = False
                raise ValueError('raw output exceeded explicit capture limit; partial evidence retained')
            self.handles[name].write(data)
            self.handles[name].flush()
            if name == 'stdout':
                self.pending += data
                if len(self.pending) > 65536 and b'\n' not in self.pending:
                    raise ValueError('stdout line exceeds 65536 bytes')
                while b'\n' in self.pending:
                    line, self.pending = self.pending.split(b'\n', 1)
                    self.lines.append(line.rstrip(b'\r').decode('utf-8'))

    def until(self, predicate):
        deadline = time.monotonic()+self.timeout
        consumed = []
        while True:
            while self.lines:
                line = self.lines.popleft()
                consumed.append(line)
                if predicate(line):
                    return consumed
            if not self._open_streams() and self.proc.poll() is not None:
                raise RuntimeError('process exited before expected protocol terminal')
            if time.monotonic() >= deadline:
                raise TimeoutError('operational protocol timeout; search was not time-limited')
            self._pump()

    def close(self, successful):
        if self.closed:
            return
        self.closed = True
        error = None
        try:
            if hasattr(self, 'proc'):
                if successful:
                    try:
                        self.send('quit')
                        deadline = time.monotonic()+self.timeout
                        while self._open_streams() or self.proc.poll() is None:
                            if time.monotonic() >= deadline:
                                raise TimeoutError('process or descendants did not close after quit')
                            self._pump()
                        self.proc.wait()
                        if self.proc.returncode != 0:
                            raise RuntimeError('process returned nonzero exit status '+str(self.proc.returncode))
                        # until() consumes the one requested terminal/fence.
                        # Buffered or newly drained lines are unrequested tail,
                        # including empty lines or duplicate readyok replies.
                        if self.lines:
                            self.receipt['unexpected_stdout_lines'] = len(self.lines)
                            self.receipt['unexpected_stdout_preview'] = [
                                line[:160] for _, line in zip(range(8), self.lines)]
                            raise ValueError('unexpected stdout after final protocol terminal/fence')
                        if (self.out/(self.label+'.stderr')).stat().st_size:
                            raise ValueError('unexpected stderr from protocol process')
                    except BaseException as exc:
                        error, successful = exc, False
                if not successful:
                    if os.name == 'nt':
                        # v2: no process-group kill on Windows; end the child's input and wait for it.
                        try:
                            self.proc.stdin.close()
                        except OSError:
                            pass
                        self.proc.wait(timeout=30)
                    else:
                        try:
                            os.killpg(self.proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        self.proc.wait(timeout=2)
                    # Preserve buffered raw output on ordinary failures. A
                    # capture-limit failure retains its flagged partial prefix.
                    if self.complete:
                        deadline = time.monotonic()+1
                        while self._open_streams() and time.monotonic() < deadline:
                            try:
                                self._pump()
                            except BaseException:
                                self.complete = False
                                break
        except BaseException as exc:
            if error is None:
                error = exc
            successful = False
        finally:
            if hasattr(self, 'proc'):
                self.receipt['returncode'] = self.proc.returncode
                if getattr(self, 'selector', None) is not None:
                    try:
                        self.selector.close()
                    except BaseException as exc:
                        if error is None:
                            error = exc
                for stream in (self.proc.stdin,self.proc.stdout,self.proc.stderr):
                    try:
                        stream.close()
                    except BaseException as exc:
                        if error is None:
                            error = exc
            for stream in self.handles.values():
                try:
                    stream.close()
                except BaseException as exc:
                    if error is None:
                        error = exc
            self.lines.clear()
            self.pending = b''
            self.receipt.update(stdout_complete=self.complete, stderr_complete=self.complete,
                                reader_queues_cleared=True,
                                close_protocol_valid=bool(successful and error is None))
            if error is not None:
                self.receipt['close_error'] = type(error).__name__+': '+str(error)
            self.receipt['captures'] = {s: {'path':self.label+'.'+s,'sha256':sha256(self.out/(self.label+'.'+s)),
                                          'bytes':(self.out/(self.label+'.'+s)).stat().st_size}
                                        for s in self.handles}
            _write_json(self.out/(self.label+'.receipt.json'), self.receipt)
        if error:
            raise error


def _table_text(groups):
    text = ['# ADVICE: observed search-event frequencies', '',
            'Search only; board/FEN setup excluded. Zero opportunities are undefined.',
            'A frequency below 0.1% is advisory; it proves neither dead code nor strength.',
            CORPUS_LIMIT, '']
    for label, rows in groups:
        kept = [row for row in rows if row['event'] not in DISABLED_BY_DEFAULT]
        text += ['## '+label, '', '| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |',
                 '|---|---:|---|---:|---:|---|']
        for row in kept:
            pct = 'unknown' if row['pct'] is None else format(row['pct'], '.8g')
            rare = 'undefined' if row['rare_below_0_1_pct'] is None else str(row['rare_below_0_1_pct']).lower()
            text.append('| {event} | {count} | {denominator} | {opportunities} | {pct} | {rare} |'.format(**{**row,'pct':pct,'rare':rare}))
        dropped = [row for row in rows if row['event'] in DISABLED_BY_DEFAULT]
        if dropped:
            text += ['', 'Not a dead-feature row (disabled by default, so a zero count is expected):']
            text += ['- {event}: count {count} of {opportunities} {denominator}; '.format(**row) +
                     DISABLED_BY_DEFAULT[row['event']] for row in dropped]
        text.append('')
    return '\n'.join(text)+'\n'


def collect(command, suites, output, *, depth=None, nodes=None, required=2000,
            allow_incomplete=False, manifest=None, timeout=120, max_capture_bytes=32 << 20,
            bench11_nodes=DEFAULT_BENCH11_NODES, bench20_nodes=DEFAULT_BENCH20_NODES):
    """Run bare pin, explicit profiled bench20, then fixed-work fresh positions.

    All failures retain the exclusive directory, raw streams, process status,
    hashes and completed packet records. PASS means protocol collection passed;
    coverage has its own explicit COMPLETE/LIMITED_INCOMPLETE status.
    """
    go = validate_limits(depth, nodes)
    if not command or not math.isfinite(timeout) or timeout <= 0 or max_capture_bytes < 1:
        raise ValueError('need command, positive operational timeout and capture bound')
    out = exclusive_directory(output)
    result = {'status':'FAIL', 'advice_only':True, 'strength_claim':False,
              'dead_code_claim':False, 'search_limit':go, 'positions_completed':0,
              'required_positions':required, 'engine_id':None, 'command':list(command),
              'collector_sha256':sha256(__file__), 'python_version':sys.version,
              'counter_schema':1, 'counter_count':len(COUNTERS), 'source_hashes':{},
              'bench11_expected_nodes':bench11_nodes, 'bench20_expected_nodes':bench20_nodes,
              'corpus_limit':CORPUS_LIMIT, 'disabled_by_default':DISABLED_BY_DEFAULT}
    process = None
    bench_packets, position_packets = [], []
    registry_source = Path(__file__).with_name('Lprime')/'src'/'profile.cpp'
    if registry_source.is_file():
        result['source_hashes']['counter_descriptions'] = {'path':str(registry_source),'sha256':sha256(registry_source)}
    for i, arg in enumerate(command):
        try:
            candidate = Path(arg)
            if candidate.is_file():
                result['source_hashes']['command_file_'+str(i)] = {'path':str(candidate.resolve()),'sha256':sha256(candidate)}
        except (OSError, ValueError):
            pass
    try:
        corpus = corpus_metadata(suites,required=required,allow_incomplete=allow_incomplete,manifest=manifest)
        result['corpus'] = {k:v for k,v in corpus.items() if k!='positions'}
        _write_json(out/'corpus.json',corpus)
        _write_json(out/'plan.json',result)
        process = _Process(command,out,'bare_bench11',timeout,max_capture_bytes)
        process.send('bench 11')
        lines = process.until(lambda line: bool(BENCH.fullmatch(line)))
        match = BENCH.fullmatch(lines[-1])
        if (int(match.group(1)),int(match.group(2))) != (11,bench11_nodes):
            raise ValueError('first bare bench11 canonical pin mismatch: '+lines[-1])
        if any(line.startswith('info string prof ') for line in lines):
            raise ValueError('bare bench unexpectedly emitted profile output')
        process.close(True)
        process = None
        process = _Process(command,out,'profile',timeout,max_capture_bytes)
        process.send('uci')
        lines = process.until(lambda line: line=='uciok')
        options = {}
        for line in lines:
            if line.startswith('id name '):
                result['engine_id'] = line[8:]
            match = re.match(r'option name (.+?) type (\S+)(?: (.*))?$',line)
            if match:
                if match.group(1) in options:
                    raise ValueError('duplicate advertised option')
                options[match.group(1)] = (match.group(2),match.group(3) or '')
        for name, kind in (('Threads','spin'),('Hash','spin'),('OwnBook','check'),('Profile','check'),('Clear Hash','button')):
            if name not in options or options[name][0] != kind:
                raise ValueError('required advertised option missing or wrong type: '+name)
        if not re.search(r'\bdefault false\b',options['Profile'][1]):
            raise ValueError('Profile must advertise default false')
        for name,value in (('Threads','1'),('Hash','16'),('OwnBook','false'),('Profile','true')):
            process.send('setoption name '+name+' value '+value)
        process.send('isready')
        process.until(lambda line:line=='readyok')
        with (out/'packets.jsonl').open('x') as packets:
            process.send('bench_prof 20')
            lines = process.until(lambda line:bool(BENCH.fullmatch(line)))
            match = BENCH.fullmatch(lines[-1])
            if (int(match.group(1)),int(match.group(2))) != (20,bench20_nodes):
                raise ValueError('profiled bench20 canonical pin mismatch: '+lines[-1])
            process.send('isready')
            lines += process.until(lambda line:line=='readyok')
            packet = parse_packet(lines,terminal='bench')
            verify_profile_work(packet,expected_nodes=bench20_nodes)
            bench_packets.append(packet)
            packets.write(json.dumps({'scope':'bench20','packet':packet},allow_nan=False)+'\n')
            packets.flush()
            for row in corpus['positions']:
                process.send('ucinewgame')
                process.send('setoption name Clear Hash')
                process.send('isready')
                process.until(lambda line:line=='readyok')
                process.send('position fen '+row['fen'])
                process.send(go)
                lines = process.until(lambda line:line.startswith('bestmove '))
                process.send('isready')
                lines += process.until(lambda line:line=='readyok')
                packet = parse_packet(lines)
                verify_profile_work(packet,node_limit=nodes)
                position_packets.append(packet)
                result['positions_completed'] += 1
                packets.write(json.dumps({'scope':'corpus','position':row,'packet':packet},allow_nan=False)+'\n')
                packets.flush()
        process.close(True)
        process = None
        if any(p['overflow'] for p in bench_packets+position_packets):
            raise ValueError('counter overflow invalidates frequency collection')
        result['status'] = 'PASS'
    except Exception as exc:
        result['failure'] = {'type':type(exc).__name__, 'message':str(exc)}
    finally:
        if process is not None:
            try:
                process.close(False)
            except Exception as exc:
                result['cleanup_failure'] = type(exc).__name__+': '+str(exc)
        result['bench20_firing_table'] = firing_table(bench_packets)
        result['corpus_firing_table'] = firing_table(position_packets)
        result['max_observed_counter'] = max((r['count'] for p in bench_packets+position_packets for r in p['counters'].values()),default=0)
        result['overflow'] = any(p['overflow'] for p in bench_packets+position_packets)
        (out/'firing_table.md').write_text(_table_text([('Bench depth 20',result['bench20_firing_table']),('Corpus fixed work',result['corpus_firing_table'])]))
        _write_json(out/'report.json',result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',required=True,type=Path)
    parser.add_argument('--suite',required=True,action='append',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    limits = parser.add_mutually_exclusive_group(required=True)
    limits.add_argument('--depth',type=int)
    limits.add_argument('--nodes',type=int)
    parser.add_argument('--required',type=int,default=2000)
    parser.add_argument('--allow-incomplete',action='store_true')
    parser.add_argument('--corpus-manifest',type=Path)
    parser.add_argument('--timeout',type=float,default=120,help='operational abort only; never a search limit')
    parser.add_argument('--max-capture-bytes',type=int,default=32 << 20)
    parser.add_argument('--bench11-nodes',type=int,default=DEFAULT_BENCH11_NODES,help='first bare bench 11 pin (AL1)')
    parser.add_argument('--bench20-nodes',type=int,default=DEFAULT_BENCH20_NODES,help='profiled bench 20 pin (AL1)')
    args = parser.parse_args(argv)
    manifest = json.loads(args.corpus_manifest.read_text()) if args.corpus_manifest else None
    try:
        result = collect([str(args.engine.resolve(strict=True))],args.suite,args.output,depth=args.depth,nodes=args.nodes,
                         required=args.required,allow_incomplete=args.allow_incomplete,manifest=manifest,
                         timeout=args.timeout,max_capture_bytes=args.max_capture_bytes,
                         bench11_nodes=args.bench11_nodes,bench20_nodes=args.bench20_nodes)
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')
    print(json.dumps({'status':result['status'],'positions_completed':result['positions_completed'],
                      'coverage':result.get('corpus',{}).get('coverage_status'),'output':str(args.output)},allow_nan=False))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
