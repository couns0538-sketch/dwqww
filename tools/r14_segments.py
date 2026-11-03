"""Bounded adjacent-chain observations; inferred segments are not authentic game IDs."""
from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import time

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r14_scan import Row, iter_rows, load_pins
from r14_qualification.qualify import Native, DEFAULT_CANDIDATE, hashes, resource_guard
from run_policy import safe_path

ROOT = Path('D:/a14')
SOURCE = Path('D:/grok-pc-data/selfplay_out')
RANGE_STRUCT = struct.Struct('<IIQB')
PAIR_STRUCT = struct.Struct('<IBI')
CODES = {
    0: ('REACHABLE', 'legal_witness'),
    1: ('UNREACHABLE', 'nonpositive_ply_gap'),
    2: ('UNREACHABLE', 'result_mismatch'),
    3: ('UNREACHABLE', 'exhaustive_no_path'),
    4: ('UNKNOWN', 'gap_exceeds_k'),
    5: ('UNKNOWN', 'node_limit'),
    6: ('UNKNOWN', 'invalid_input'),
    7: ('UNKNOWN', 'missing_parsed_row'),
    8: ('UNKNOWN', 'transport_error'),
    250: ('UNKNOWN', 'scope_start'),
    251: ('UNKNOWN', 'scope_gap'),
}
NATIVE_CODES = {value: key for key, value in CODES.items() if key < 7}
UCI = re.compile(r'[a-h][1-8][a-h][1-8][nbrq]?\Z')


@dataclass(frozen=True)
class SourceRecord:
    source_id: int
    line: int
    row: Row | None
    contiguous: bool
    selected: bool = True


@dataclass(frozen=True)
class SourceSpec:
    source_id: int
    shard: int
    path: Path
    md5: str
    mode: str = 'all'
    limit: int | None = None
    target_limit: int | None = None


@dataclass(frozen=True)
class PairEvidence:
    left: SourceRecord | None
    right: SourceRecord
    code: int
    nodes: int = 0
    witness: tuple[str, ...] = ()
    adjacent: bool = True

    @property
    def status(self):
        return CODES[self.code][0]

    @property
    def reason(self):
        return CODES[self.code][1]


class TransportFailure(RuntimeError):
    pass


def select_source(spec, receipt, guard=lambda: None, progress=lambda value: None):
    """Select chain scope while consuming and hashing every physical source byte."""
    if spec.mode not in ('all', 'prefix', 'edges'):
        raise ValueError('unknown source selection')
    if spec.mode != 'all' and (type(spec.limit) is not int or spec.limit < 1):
        raise ValueError('positive window/prefix limit required')
    if spec.target_limit is not None and (type(spec.target_limit) is not int or spec.target_limit < 1):
        raise ValueError('positive target prefix required')
    tail = deque(maxlen=spec.limit if spec.mode == 'edges' else 0)
    previous = 0
    scanned, valid, target_rows, target_valid = 0, 0, 0, 0
    ranges = []

    def selected(line, row):
        nonlocal previous, scanned, valid, target_rows, target_valid
        contiguous = previous != 0 and line == previous + 1
        if not contiguous:
            ranges.append([line, line])
        else:
            ranges[-1][1] = line
        is_target = spec.target_limit is None or line <= spec.target_limit
        scanned += 1
        valid += row is not None
        target_rows += is_target
        target_valid += is_target and row is not None
        previous = line
        return SourceRecord(spec.source_id, line, row, contiguous, is_target)

    for line, row in iter_rows(spec.path, spec.md5, receipt):
        if line >= 2**32:
            raise ValueError('source row exceeds range format')
        if line % 4096 == 0:
            guard()
            progress(dict(stage='source_read', source_id=spec.source_id, rows=line,
                          scanned_rows=scanned, key_fill_rate=valid / scanned if scanned else None))
        if spec.mode == 'all' or line <= spec.limit:
            yield selected(line, row)
        elif spec.mode == 'edges':
            tail.append((line, row))
    for line, row in tail:
        if line % 4096 == 0:
            guard()
        yield selected(line, row)
    receipt.update(source_id=spec.source_id, shard=spec.shard, selection=spec.mode,
                   chain_scanned_ranges=ranges, chain_scanned_rows=scanned, chain_valid_key_rows=valid,
                   chain_windows=[dict(first_line=first, last_line=last, open_left=first != 1,
                                       open_right=last != receipt['rows']) for first, last in ranges],
                   chain_key_fill_rate=valid / scanned if scanned else None,
                   target_rows=target_rows, target_valid_key_rows=target_valid,
                   target_key_fill_rate=target_valid / target_rows if target_rows else None,
                   context_rows=scanned - target_rows, target_limit=spec.target_limit,
                   first_scanned_line=ranges[0][0] if ranges else None,
                   last_scanned_line=previous if scanned else None,
                   open_left=bool(ranges and ranges[0][0] != 1),
                   open_right=bool(scanned and previous != receipt['rows']))


def selected_records(specs, receipts, guard=lambda: None, progress=lambda value: None):
    previous_spec = previous_receipt = None
    for spec in specs:
        guard()
        receipt = {}
        receipts.append(receipt)
        join = bool(previous_spec is not None and previous_spec.shard + 1 == spec.shard and
                    previous_receipt.get('complete') is True and
                    previous_receipt.get('last_scanned_line') == previous_receipt.get('rows'))
        first = True
        for record in select_source(spec, receipt, guard, progress):
            if first:
                record = SourceRecord(record.source_id, record.line, record.row,
                                      join and record.line == 1, record.selected)
                first = False
            yield record
        previous_spec, previous_receipt = spec, receipt
        progress(dict(stage='source_complete', source_id=spec.source_id, receipt=receipt))


def validate_reply(left, right, reply, ident, limit, k):
    if not isinstance(reply, dict) or reply.get('id') != ident:
        raise TransportFailure('native response identifier mismatch')
    code = NATIVE_CODES.get((reply.get('status'), reply.get('reason')))
    nodes, witness = reply.get('nodes'), reply.get('witness')
    if code is None or type(nodes) is not int or not 0 <= nodes <= limit:
        raise TransportFailure('invalid native status or node count')
    if not isinstance(witness, list) or any(not isinstance(move, str) or not UCI.fullmatch(move) for move in witness):
        raise TransportFailure('invalid native witness syntax')
    delta = right.row.ply - left.row.ply
    equal_result = left.row.result == right.row.result
    if code == 0 and (not equal_result or not 1 <= delta <= k or len(witness) != delta):
        raise TransportFailure('native positive violates clocks/result/depth')
    if code == 0:
        board, target = chess.Board(left.row.fen), chess.Board(right.row.fen)
        if not board.is_valid() or not target.is_valid():
            raise TransportFailure('native witness endpoint fails independent board validity')
        for token in witness:
            move = chess.Move.from_uci(token)
            if move not in board.legal_moves:
                raise TransportFailure('native witness contains an independently illegal move')
            board.push(move)
        if board.fen(en_passant='fen') != target.fen(en_passant='fen'):
            raise TransportFailure('native witness does not reach the full six-field target')
    if code != 0 and witness:
        raise TransportFailure('nonpositive native result has a witness')
    if code == 1 and delta > 0 or code == 2 and equal_result:
        raise TransportFailure('native boundary reason contradicts input')
    if code == 3 and (not equal_result or not 1 <= delta <= k):
        raise TransportFailure('exhaustive negative outside search scope')
    if code == 4 and delta <= k or code == 5 and nodes != limit:
        raise TransportFailure('native unknown reason contradicts input/budget')
    return PairEvidence(left, right, code, nodes, tuple(witness))


def scan_pairs(records, query_many, *, k=8, node_limit=100000, boundary_node_limit=1000000, guard=lambda: None):
    """One event per scanned row; codes 250/251 are scope events, not pairs."""
    if type(k) is not int or k < 8 or k > 64:
        raise ValueError('K must be an integer in 8..64')
    if any(type(limit) is not int or not 1 <= limit <= 1000000000 for limit in (node_limit, boundary_node_limit)):
        raise ValueError('invalid node budget')
    pending = []
    pending_bytes = 0
    ordinal = 0
    previous = None
    seen_sources = set()

    def flush():
        nonlocal pending, pending_bytes
        if not pending:
            return
        batch = pending
        pending, pending_bytes = [], 0
        guard()
        try:
            replies = query_many([item[3] for item in batch])
            if not isinstance(replies, list) or len(replies) != len(batch):
                raise TransportFailure('native batch reply count mismatch')
            verified = [validate_reply(item[0], item[1], replies[index], item[2], item[4], k)
                        for index, item in enumerate(batch)]
        except Exception as error:
            for left, right, _, _, _ in batch:
                yield PairEvidence(left, right, 8)
            raise TransportFailure(f'native batch failed: {type(error).__name__}: {error}') from error
        yield from verified

    for record in records:
        if type(record.source_id) is not int or record.source_id < 0 or type(record.line) is not int or not 1 <= record.line < 2**32:
            raise ValueError('invalid source identity or physical line')
        if previous is not None and previous.source_id == record.source_id and record.line <= previous.line:
            raise ValueError('source records must be strictly ordered')
        if previous is None or previous.source_id != record.source_id:
            if record.source_id in seen_sources:
                raise ValueError('source identity recurs after another source')
            seen_sources.add(record.source_id)
        if previous is None or not record.contiguous:
            yield from flush()
            yield PairEvidence(previous, record, 250 if previous is None else 251, adjacent=False)
        elif previous.row is None or record.row is None:
            yield from flush()
            yield PairEvidence(previous, record, 7)
        else:
            if previous.source_id == record.source_id and record.line != previous.line + 1:
                raise ValueError('contiguous flag crosses an omitted physical row')
            ordinal += 1
            ident = f'p{ordinal}'
            cap = boundary_node_limit if previous.source_id != record.source_id else node_limit
            line = '\t'.join((ident, previous.row.fen, previous.row.result, record.row.fen, record.row.result, str(k), str(cap)))
            size = len(line.encode('utf-8')) + 1
            if size > 2048:
                raise ValueError('pair exceeds bounded native request size')
            if len(pending) == 8 or pending_bytes + size > 2048:
                yield from flush()
            pending.append((previous, record, ident, line, cap))
            pending_bytes += size
        previous = record
    yield from flush()


class SegmentAssembler:
    def __init__(self, emit_range):
        self.emit_range = emit_range
        self.segment_id = 0
        self.active = None
        self.ranges = 0

    def close(self):
        if self.active is not None:
            source, first, last, segment, code = self.active
            self.emit_range(source, (first, last, segment, code))
            self.ranges += 1
            self.active = None

    def add(self, event):
        right = event.right
        fresh = self.segment_id == 0 or event.code != 0
        if fresh:
            self.close()
            self.segment_id += 1
        elif self.active is not None and self.active[0] != right.source_id:
            self.close()
        if self.active is None:
            self.active = [right.source_id, right.line, right.line, self.segment_id, event.code]
        else:
            if right.line != self.active[2] + 1:
                raise ValueError('range cannot span a missing physical row')
            self.active[2] = right.line


def fixture_audit(records, events, authentic_games, splits):
    """Synthetic truth is explicit; this API never assigns production identities."""
    reasons = set()
    records, events = list(records), list(events)
    event_coverage_complete = bool(records) and len(records) == len(events) and all(
        event.right == record for event, record in zip(events, records))
    by_game = {}
    missing = 0
    for record in records:
        key = (record.source_id, record.line)
        game, split = authentic_games.get(key), splits.get(key)
        if game is None or split is None or record.row is None:
            missing += 1
        else:
            by_game.setdefault(game, set()).add(split)
    if any(len(values) > 1 for values in by_game.values()):
        reasons.add('game_crosses_splits')
    unknowns = 0
    for event in events:
        if not event.adjacent:
            continue
        left = authentic_games.get((event.left.source_id, event.left.line))
        right = authentic_games.get((event.right.source_id, event.right.line))
        if event.status == 'UNKNOWN':
            unknowns += 1
        if left is not None and left == right and event.status == 'UNREACHABLE':
            reasons.add('broken_authentic_chain')
        if left is not None and right is not None and left != right and event.code == 0:
            reasons.add('legal_link_between_distinct_games')
    return dict(scope='synthetic_fixture_truth', status='FAIL' if reasons else 'UNVERIFIED' if missing or unknowns or not event_coverage_complete else 'PASS',
                reasons=sorted(reasons), unknowns=unknowns, missing_bindings_or_rows=missing,
                event_coverage_complete=event_coverage_complete)


def validate_qualification(report, native_identity):
    if report.get('schema') != 1 or report.get('status') != 'PASS' or report.get('complete') is not True or report.get('scope') != 'production_helper_qualification':
        raise ValueError('completed production helper qualification PASS required')
    requested = report.get('requested_pairs')
    foundation = report.get('by_stratum', {}).get('one_ply', {}).get('resolved')
    if type(requested) is not int or requested < 1000000 or type(foundation) is not int or foundation < requested:
        raise ValueError('one-million resolved foundation required')
    if type(report.get('disagreements')) is not int or report['disagreements'] != 0:
        raise ValueError('qualification disagreements')
    for key in ('md5', 'sha256'):
        if report.get('native_' + key) != native_identity.get(key):
            raise ValueError('qualification native identity mismatch')
    if str(Path(report.get('native_exe', '')).resolve()).casefold() != str(Path(native_identity.get('path', '')).resolve()).casefold():
        raise ValueError('qualification native path mismatch')
    wanted = report.get('requested', {})
    deep, negative = wanted.get('deep_per_depth'), wanted.get('exhaustive_negatives')
    if type(deep) is not int or deep < 1 or type(negative) is not int or negative < 1:
        raise ValueError('qualification extra strata missing')
    strata = report.get('by_stratum', {})
    if strata.get('deep_positive', {}).get('attempted') != 7 * deep or strata.get('exhaustive_negative', {}).get('attempted') != negative:
        raise ValueError('qualification extra strata incomplete')
    return report


class MapWriter:
    def __init__(self, directory, guard, chunk_bytes=10 * 1024**2):
        self.directory = directory
        self.directory.mkdir(exist_ok=False)
        self.guard = guard
        self.chunk_bytes = chunk_bytes
        self.opened = {}
        self.parts = Counter()
        self.artifacts = []

    def append(self, source, kind, record):
        if kind not in ('ranges', 'pairs', 'boundaries'):
            raise ValueError('unknown map stream kind')
        layout = RANGE_STRUCT if kind == 'ranges' else PAIR_STRUCT
        payload = layout.pack(*record)
        key = (source, kind)
        current = self.opened.get(key)
        if current is not None and current['bytes'] + len(payload) > self.chunk_bytes:
            self.finish(key)
            current = None
        if current is None:
            self.guard()
            self.parts[key] += 1
            path = self.directory / f'source_{source:03}_{kind}_{self.parts[key]:04}.bin'
            current = dict(path=path, stream=path.open('xb'), bytes=0, records=0)
            self.opened[key] = current
        if current['stream'].write(payload) != len(payload):
            raise OSError('partial map write')
        current['bytes'] += len(payload)
        current['records'] += 1

    def finish(self, key):
        self.guard()
        current = self.opened[key]
        current['stream'].flush()
        os.fsync(current['stream'].fileno())
        current['stream'].close()
        identity = hashes(current['path'])
        self.artifacts.append(dict(source_id=key[0], kind=key[1], records=current['records'], bytes=current['bytes'], **identity))
        del self.opened[key]

    def close(self):
        for key in list(self.opened):
            self.finish(key)

    def abort(self):
        """Discard buffered tails after a hard stop, preserving only sealed parts."""
        for current in self.opened.values():
            try:
                current['stream'].raw.close()
            except (OSError, ValueError):
                pass
            finally:
                try:
                    current['stream'].close()
                except (OSError, ValueError):
                    pass
        self.opened.clear()


def iter_ranges(paths):
    """Read fixed-size range records in supplied part order, with no mmap/index."""
    for path in paths:
        with Path(path).open('rb') as stream:
            while payload := stream.read(RANGE_STRUCT.size):
                if len(payload) != RANGE_STRUCT.size:
                    raise ValueError('truncated range record')
                yield RANGE_STRUCT.unpack(payload)


class Guard:
    def __init__(self, seconds, cpu):
        import psutil
        if not math.isfinite(seconds) or seconds <= 0 or cpu not in (0, 1, 2, 3):
            raise ValueError('finite duration and spare CPU required')
        process = psutil.Process()
        process.nice(psutil.IDLE_PRIORITY_CLASS)
        if cpu not in process.cpu_affinity():
            raise ValueError('CPU outside inherited affinity')
        load = psutil.cpu_percent(interval=.5, percpu=True)[cpu]
        if load > 70:
            raise RuntimeError(f'CPU admission refused: CPU{cpu} at {load}%')
        process.cpu_affinity([cpu])
        self.deadline = time.monotonic() + seconds
        self.next_check = 0
        self.child = None
        self()

    def __call__(self):
        now = time.monotonic()
        if now >= self.deadline:
            raise TimeoutError('bounded segment scan deadline')
        if now >= self.next_check:
            resource_guard(self.child.process if self.child else None, reserve_bytes=32 * 1024**2)
            self.next_check = time.monotonic() + 15


def spec_set(mode, pins):
    selections = [(12, 12, 'edges', 50000, None), (13, 13, 'all', None, None),
                  (14, 14, 'all', None, None), (15, 15, 'edges', 50000, None)] if mode == 'production' else [
                  (0, 1, 'all', None, None), (1, 2, 'prefix', 583415, 533415)]
    specs = []
    for source_id, shard, selection, limit, target_limit in selections:
        path = safe_path(SOURCE / f'forge_selfplay_{shard:03}.txt')
        key = str(path).casefold()
        if key not in pins:
            raise ValueError('missing source pin')
        specs.append(SourceSpec(source_id, shard, path, pins[key], selection, limit, target_limit))
    return specs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('production', 'jobA'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pins', type=Path, default=ROOT / 'evidence/r14/input-pins-all.jsonl')
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--qualification-md5', required=True)
    parser.add_argument('--native', type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument('--cpu', type=int, default=2)
    parser.add_argument('--seconds', type=float, default=10800)
    args = parser.parse_args(argv)
    for name in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES'):
        os.environ[name] = '-1'
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[name] = '1'
    guard = Guard(args.seconds, args.cpu)
    native_identity = hashes(safe_path(args.native))
    qualification_path = safe_path(args.qualification)
    qualification_identity = hashes(qualification_path)
    if qualification_identity['md5'] != args.qualification_md5:
        raise ValueError('qualification report pin mismatch')
    with qualification_path.open(encoding='utf-8') as stream:
        validate_qualification(json.load(stream), native_identity)
    pin_path = safe_path(args.pins)
    pin_identity = hashes(pin_path)
    specs = spec_set(args.mode, load_pins(pin_path))
    out = safe_path(args.out, write=True)
    resource_guard()
    out.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__), ROOT / 'tools/r14_scan.py', ROOT / 'tools/run_policy.py',
                    ROOT / 'tools/r14_qualification/qualify.py', Path(sys.executable), Path(chess.__file__)]
    tool_identities = [hashes(path) for path in source_paths]
    began = time.monotonic()
    receipts, edges, samples = [], [], []
    counts, reason_counts, per_source = Counter(), Counter(), {}
    report = dict(schema=1, scope='bounded_adjacent_chain_segments', mode=args.mode, status='UNVERIFIED', complete=False,
                  authentic_game_ids='UNVERIFIED', native=native_identity, qualification=qualification_identity,
                  positive_witness_verification='independent legal replay and all six FEN fields including raw EP',
                  runtime_versions=dict(python=sys.version, chess=chess.__version__),
                  pins=pin_identity, tool_identities=tool_identities, k=8, node_limit=100000, boundary_node_limit=1000000,
                  code_table={str(code): dict(status=value[0], reason=value[1]) for code, value in CODES.items()},
                  binary_formats=dict(ranges=dict(format='<IIQB', bytes=17, fields=['first_line','last_line','segment_id','start_code']),
                                      pairs=dict(format='<IBI', bytes=9, fields=['right_line','outcome_code','nodes'])),
                  source_specs=[dict(source_id=s.source_id, shard=s.shard, path=str(s.path), md5=s.md5,
                                     selection=s.mode, limit=s.limit, target_limit=s.target_limit) for s in specs],
                  start_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'), reasons=[])
    writer = MapWriter(out / 'maps', guard)
    assembly = SegmentAssembler(lambda source, record: writer.append(source, 'ranges', record))
    child = None
    last_progress = 0.0

    def progress(value):
        nonlocal last_progress
        now = time.monotonic()
        if now - last_progress < 30 and not value['stage'].endswith('complete'):
            return
        guard()
        value.update(elapsed_seconds=now - began, pair_counts=dict(counts), segments=assembly.segment_id)
        text = json.dumps(value, sort_keys=True)
        print(text, flush=True)
        with (out / 'progress.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(text + '\n')
        last_progress = now

    try:
        child = Native(args.native, '--pairs', out / 'native.stderr.log', guard.deadline)
        guard.child = child
        for event in scan_pairs(selected_records(specs, receipts, guard, progress), child.query_many, guard=guard):
            source = event.right.source_id
            source_counts = per_source.setdefault(str(source), Counter())
            source_counts['scanned_rows'] += 1
            source_counts['valid_key_rows'] += event.right.row is not None
            source_counts['target_rows'] += event.right.selected
            source_counts['context_rows'] += not event.right.selected
            writer.append(source, 'pairs', (event.right.line, event.code, event.nodes))
            if event.code != 0:
                writer.append(source, 'boundaries', (event.right.line, event.code, event.nodes))
            assembly.add(event)
            if event.adjacent:
                counts[event.status] += 1
                reason_counts[event.reason] += 1
                source_counts[event.status] += 1
                if event.left.source_id != source:
                    edges.append(dict(left_source=event.left.source_id, left_line=event.left.line,
                                      right_source=source, right_line=event.right.line, code=event.code,
                                      status=event.status, reason=event.reason, nodes=event.nodes,
                                      witness=list(event.witness), continued_segment_id=assembly.segment_id if event.code == 0 else None))
                elif len(samples) < 100:
                    samples.append(dict(source_id=source, left_line=event.left.line, right_line=event.right.line,
                                        code=event.code, nodes=event.nodes, witness=list(event.witness)))
            else:
                source_counts[event.reason] += 1
        assembly.close()
        child.close()
        guard.child = None
        writer.close()
        report['complete'] = True
    except Exception as error:
        report['reasons'].append(f'{type(error).__name__}: {error}')
    finally:
        if child is not None:
            try:
                child.close()
            except Exception as error:
                report['complete'] = False
                report['reasons'].append(f'native close: {type(error).__name__}: {error}')
        # A hard storage stop permits no further evidence allocation.
        try:
            resource_guard(reserve_bytes=32 * 1024**2)
        except Exception as error:
            writer.abort()
            print(json.dumps(dict(status='UNVERIFIED', complete=False, hard_stop=str(error),
                                  pair_counts=dict(counts), reasons=report['reasons'])), flush=True)
            return 2
        try:
            # The computation deadline does not prevent a bounded evidence seal.
            writer.guard = lambda: resource_guard(reserve_bytes=32 * 1024**2)
            assembly.close()
            writer.close()
        except Exception as error:
            writer.abort()
            report['complete'] = False
            report['reasons'].append(f'map close: {type(error).__name__}: {error}')
        report.update(input_receipts=receipts, pair_counts=dict(counts), reason_counts=dict(reason_counts),
                      source_counts={key: dict(value) for key, value in per_source.items()},
                      segment_count=assembly.segment_id, range_count=assembly.ranges, artifacts=writer.artifacts,
                      cross_file_adjacent_pairs=edges, witness_samples=samples,
                      boundary_search_scope='only observed adjacent physical rows at source seams; no all-pairs cross-window search',
                      elapsed_seconds=time.monotonic()-began, end_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
        for identity in [native_identity, qualification_identity, pin_identity, *tool_identities]:
            try:
                unchanged = hashes(identity['path']) == identity
            except Exception as error:
                unchanged = False
                report['reasons'].append(f'identity read: {type(error).__name__}: {error}')
            if not unchanged:
                report['complete'] = False
                report['reasons'].append('identity changed: ' + identity['path'])
        if counts['UNKNOWN']:
            report['reasons'].append('unresolved adjacent-pair checks remain')
        if any(receipt.get('complete') is not True or receipt.get('chain_key_fill_rate') != 1.0 for receipt in receipts):
            report['reasons'].append('input consumption or selected-key coverage incomplete')
        report['reasons'].extend(['Observed segment IDs are inferred chain labels, not authenticated original game IDs.',
                                  'Historical producer-to-shard binding remains unverified.'])
        payload = json.dumps(report, sort_keys=True, indent=2) + '\n'
        try:
            resource_guard(reserve_bytes=len(payload.encode('utf-8'))+4096)
            pending = out / 'REPORT.json.part'
            with pending.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            resource_guard(reserve_bytes=4096)
            os.rename(pending, out / 'REPORT.json')
        except Exception as error:
            print(json.dumps(dict(status='UNVERIFIED', complete=False, publication_error=str(error), counts=dict(counts))), flush=True)
            return 2
        print(json.dumps(dict(status='UNVERIFIED', complete=report['complete'], pair_counts=dict(counts),
                              report=str(out/'REPORT.json'))), flush=True)
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
