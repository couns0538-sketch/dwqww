"""Exhaustive necessary-condition enumeration for bounded endpoint windows."""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import sys

for _name in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES'):
    os.environ[_name] = '-1'
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import chess
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r14_scan import Row, parse_row
from run_policy import safe_path

MAX_LINE = 4096
UINT32_LIMIT = 2**32
ACCOUNTING_FIELDS = ('invalid_endpoint_pairs', 'excluded_result', 'excluded_ply',
                     'excluded_clock', 'excluded_rights', 'excluded_material',
                     'excluded_piece_squares', 'survivors')


@dataclass(frozen=True)
class Endpoint:
    source_id: int
    line: int
    fen: str
    result: str
    ply: int
    halfmove: int
    rights: int
    counts: tuple[int, int]
    pieces: tuple[int, ...]

    def row(self):
        return Row(self.fen, 0, self.result, self.ply, {})


@dataclass(frozen=True)
class CandidateChunk:
    left: Endpoint
    depth: int
    right_indices: np.ndarray


class InputHashMismatch(ValueError):
    pass


def _endpoint_from_row(row, source_id, line):
    if type(line) is not int or not 1 <= line < UINT32_LIMIT:
        raise ValueError('physical line does not fit uint32')
    if type(row.ply) is not int or not 0 <= row.ply < UINT32_LIMIT:
        raise ValueError('absolute ply does not fit uint32')
    board = chess.Board(row.fen)
    if not board.is_valid():
        raise ValueError('independent legal-state validity failed')
    rights_text = row.fen.split()[2]
    rights = sum(1 << index for index, token in enumerate('KQkq') if token in rights_text)
    pieces = tuple(int(board.pieces_mask(kind, color)) for color in (True, False) for kind in range(1, 7))
    counts = tuple(int(board.occupied_co[color]).bit_count() for color in (True, False))
    return Endpoint(source_id, line, row.fen, row.result, row.ply, board.halfmove_clock, rights, counts, pieces)


def parse_endpoint(raw, source_id, line):
    return _endpoint_from_row(parse_row(raw), source_id, line)


def _metadata(path):
    value = path.stat()
    return dict(size=value.st_size, mtime_ns=value.st_mtime_ns, device=value.st_dev, inode=value.st_ino)


def read_window(path, expected_md5, side, count, source_id, guard=lambda: None,
                progress=lambda value: None, receipt=None):
    """Hash every source byte; retain bounded physical rows and parse only those."""
    if side not in ('first', 'last') or type(count) is not int or count < 1 or count > 50000:
        raise ValueError('bounded first/last window required')
    if not isinstance(expected_md5, str) or not re.fullmatch('[0-9a-f]{32}', expected_md5):
        raise ValueError('full lowercase expected MD5 required')
    path = safe_path(path)
    if receipt is None:
        receipt = {}
    before = _metadata(path)
    receipt.update(path=str(path), source_id=source_id, side=side, requested_rows=count,
                   expected_md5=expected_md5, before=before, complete=False, rows=0, consumed_bytes=0,
                   parse_scope='retained_endpoints_only', full_source_parse_verified=False,
                   full_source_byte_hash_verified=False)
    retained = deque(maxlen=count) if side == 'last' else []
    digest = hashlib.md5()
    line_number, consumed = 0, 0
    guard()
    try:
        with path.open('rb', buffering=1024**2) as stream:
            while True:
                raw = stream.readline(MAX_LINE + 1)
                if not raw:
                    break
                digest.update(raw)
                consumed += len(raw)
                oversized = len(raw) > MAX_LINE
                chunk = raw
                while oversized and chunk and not chunk.endswith(b'\n'):
                    chunk = stream.readline(MAX_LINE + 1)
                    digest.update(chunk)
                    consumed += len(chunk)
                    guard()
                line_number += 1
                if line_number >= UINT32_LIMIT:
                    raise ValueError('physical line exceeds uint32 format')
                if side == 'last' or len(retained) < count:
                    retained.append((line_number, None if oversized else raw))
                if line_number % 16384 == 0:
                    guard()
                    progress(dict(stage='window_source_read', source_id=source_id, rows=line_number,
                                  consumed_bytes=consumed))
        after = _metadata(path)
        receipt['after'] = after
        if before != after or consumed != before['size']:
            raise ValueError('source metadata changed during complete-byte read')
        if digest.hexdigest() != expected_md5:
            raise InputHashMismatch('input hash mismatch: ' + str(path))
        receipt['full_source_byte_hash_verified'] = True
        records = []
        key_rows, valid_rows = 0, 0
        failures = Counter()
        for index, (physical_line, raw) in enumerate(retained):
            if index % 1024 == 0:
                guard()
            if raw is None:
                records.append(None)
                failures['oversized_line'] += 1
                continue
            try:
                row = parse_row(raw)
            except (ValueError, UnicodeError):
                records.append(None)
                failures['unparsable_row'] += 1
                continue
            key_rows += 1
            try:
                records.append(_endpoint_from_row(row, source_id, physical_line))
            except ValueError:
                records.append(None)
                failures['invalid_legal_state'] += 1
                continue
            valid_rows += 1
        selected = len(retained)
        receipt.update(window_rows=selected, first_line=retained[0][0] if retained else None,
                       last_line=retained[-1][0] if retained else None, endpoint_valid_key_rows=key_rows,
                       endpoint_valid_legal_states=valid_rows, endpoint_key_fill_rate=key_rows/selected if selected else None,
                       endpoint_legal_state_fill_rate=valid_rows/selected if selected else None,
                       failures=dict(failures), complete=True)
        return records, receipt
    finally:
        receipt.update(rows=line_number, consumed_bytes=consumed, actual_md5=digest.hexdigest(),
                       hash_scope='full_source' if consumed == before['size'] else 'consumed_prefix')


class Population:
    def __init__(self, records):
        records = list(records)
        self.total = len(records)
        self.valid = [record for record in records if record is not None]
        for record in self.valid:
            if type(record.ply) is not int or not 0 <= record.ply < UINT32_LIMIT:
                raise ValueError('absolute ply does not fit uint32')
            if type(record.line) is not int or not 1 <= record.line < UINT32_LIMIT:
                raise ValueError('physical line does not fit uint32')
            if type(record.halfmove) is not int or not 0 <= record.halfmove < UINT32_LIMIT:
                raise ValueError('halfmove does not fit uint32')
            if record.result not in ('0', '0.5', '1') or not 0 <= record.rights <= 15:
                raise ValueError('invalid endpoint labels')
            if len(record.counts) != 2 or any(type(n) is not int or not 0 <= n <= 64 for n in record.counts):
                raise ValueError('invalid piece cardinalities')
            if len(record.pieces) != 12 or any(type(n) is not int or not 0 <= n < 2**64 for n in record.pieces):
                raise ValueError('invalid piece membership words')
        self.invalid = self.total - len(self.valid)
        self.ply = np.array([r.ply for r in self.valid], dtype=np.uint32)
        self.halfmove = np.array([r.halfmove for r in self.valid], dtype=np.uint32)
        self.rights = np.array([r.rights for r in self.valid], dtype=np.uint8)
        # Signed widening precedes subtraction. A legal board has at most 64 squares.
        self.counts = np.array([r.counts for r in self.valid], dtype=np.int32).reshape((-1, 2))
        self.pieces = np.array([r.pieces for r in self.valid], dtype=np.uint64).reshape((-1, 2, 6))
        self.result_counts = Counter(r.result for r in self.valid)
        temporary = {}
        for index, record in enumerate(self.valid):
            temporary.setdefault((record.result, record.ply), []).append(index)
        self.buckets = {key: np.array(value, dtype=np.int64) for key, value in temporary.items()}


def filter_indices(left, right, indices, depth, metrics):
    """Apply only the four reviewed necessary-condition filters, in order."""
    indices = np.asarray(indices, dtype=np.int64)
    if not 1 <= depth <= 8:
        raise ValueError('candidate depth must be 1..8')

    def retain(mask, field):
        nonlocal indices
        kept = int(np.count_nonzero(mask))
        metrics[field] += int(len(indices)) - kept
        indices = indices[mask]

    clocks = right.halfmove[indices].astype(np.uint64)
    retain((clocks == left.halfmove + depth) | (clocks < depth), 'excluded_clock')
    if not len(indices):
        return indices
    retain((right.rights[indices] & (15 ^ left.rights)) == 0, 'excluded_rights')
    if not len(indices):
        return indices
    white_turns = (depth + int(left.ply % 2 == 0)) // 2
    turns = np.array([white_turns, depth - white_turns], dtype=np.int32)
    losses = np.array(left.counts, dtype=np.int32) - right.counts[indices]
    retain(np.all((losses >= 0) & (losses <= turns[::-1]), axis=1), 'excluded_material')
    if not len(indices):
        return indices
    losses = np.array(left.counts, dtype=np.int32) - right.counts[indices]
    memberships = np.array(left.pieces, dtype=np.uint64).reshape((2, 6))
    changed = np.bitwise_count(right.pieces[indices] ^ memberships).sum(axis=2, dtype=np.uint16).astype(np.int32)
    castle = np.array([bool(left.rights & 3), bool(left.rights & 12)], dtype=np.int32) * (turns > 0)
    bound = 2 * turns + losses + 2 * castle
    retain(np.all(changed <= bound, axis=1), 'excluded_piece_squares')
    return indices


def candidate_chunks(left, right, metrics, guard=lambda: None):
    """Enumerate all surviving physical pairs; no Cartesian product is stored."""
    metrics.clear()
    metrics.update({name: 0 for name in ACCOUNTING_FIELDS})
    metrics.update(total_pairs=int(left.total)*int(right.total), complete=False,
                   invalid_endpoint_pairs=int(left.invalid)*int(right.total)+len(left.valid)*int(right.invalid))
    same_result = sum(int(number)*int(right.result_counts[result]) for result, number in left.result_counts.items())
    metrics['excluded_result'] = len(left.valid)*len(right.valid)-same_result
    try:
        guard()
        for ordinal, record in enumerate(left.valid):
            if ordinal % 128 == 0:
                guard()
            groups = [(depth, right.buckets.get((record.result, record.ply+depth))) for depth in range(1,9)]
            ply_eligible = sum(len(indices) for _, indices in groups if indices is not None)
            metrics['excluded_ply'] += int(right.result_counts[record.result])-ply_eligible
            for depth, indices in groups:
                if indices is None:
                    continue
                remaining = filter_indices(record, right, indices, depth, metrics)
                metrics['survivors'] += int(len(remaining))
                if len(remaining):
                    yield CandidateChunk(record, depth, remaining)
        if sum(metrics[name] for name in ACCOUNTING_FIELDS) != metrics['total_pairs']:
            raise RuntimeError('candidate population accounting mismatch')
        metrics['complete'] = True
    finally:
        metrics['unclassified_pairs'] = metrics['total_pairs']-sum(metrics[name] for name in ACCOUNTING_FIELDS)


def count_candidates(left, right, guard=lambda: None):
    metrics = {}
    for _ in candidate_chunks(left, right, metrics, guard):
        pass
    return metrics
