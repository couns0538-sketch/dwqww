"""Streaming row identities and fail-closed separation evidence primitives."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re

from run_policy import safe_path, free_guard

EXPAND = str.maketrans({str(n): '.' * n for n in range(1, 9)})
PIECES = frozenset('PNBRQKpnbrqk12345678/')
INTEGER = re.compile(r'[+-]?[0-9]+\Z')
UNSIGNED = re.compile(r'[0-9]+\Z')
EP = re.compile(r'[a-h][36]\Z')


@dataclass(frozen=True, slots=True)
class Row:
    fen: str
    score: int
    result: str
    ply: int
    keys: dict[str, bytes]


def parse_row(raw: bytes) -> Row:
    if len(raw) > 4096:
        raise ValueError('row exceeds byte limit')
    try:
        text = raw.decode('ascii').rstrip('\r\n')
    except UnicodeError as exc:
        raise ValueError('ASCII row required') from exc
    if any(ord(c) < 32 and c != '\t' for c in text):
        raise ValueError('control character in row')
    parts = text.split('|')
    if len(parts) != 3:
        raise ValueError('FEN, score and result required')
    fields = parts[0].split()
    if len(fields) != 6 or fields[1] not in ('w', 'b'):
        raise ValueError('six FEN fields and side required')
    board, side, rights, ep, half, full = fields
    if not board or not set(board).issubset(PIECES):
        raise ValueError('invalid board character')
    ranks = board.split('/')
    if re.search(r'[1-8]{2}', board):
        raise ValueError('consecutive empty-square digits')
    expanded = [rank.translate(EXPAND) for rank in ranks]
    if len(ranks) != 8 or any(len(rank) != 8 for rank in expanded):
        raise ValueError('invalid board width')
    if board.count('K') != 1 or board.count('k') != 1:
        raise ValueError('one king per side required')
    if rights != '-' and (not rights or any(c not in 'KQkq' for c in rights) or len(set(rights)) != len(rights)):
        raise ValueError('invalid rights')
    if ep != '-' and (not EP.fullmatch(ep) or ep[1] != ('6' if side == 'w' else '3')):
        raise ValueError('invalid EP field')
    if not UNSIGNED.fullmatch(half) or not UNSIGNED.fullmatch(full):
        raise ValueError('invalid clocks')
    h, f = int(half), int(full)
    if not 0 <= h <= 1000000000 or not 1 <= f <= 1000000000:
        raise ValueError('clock outside supported range')
    score_text, result_text = parts[1].strip(), parts[2].strip()
    if not INTEGER.fullmatch(score_text) or not -32767 <= int(score_text) <= 32767:
        raise ValueError('invalid score')
    results = {'0': '0', '0.0': '0', '.0': '0', '0.5': '0.5', '.5': '0.5', '1': '1', '1.0': '1'}
    if result_text not in results:
        raise ValueError('invalid White result')
    fen = ' '.join(fields)
    board_side = (''.join(expanded) + ' ' + side).encode('ascii')
    canonical_rights = ''.join(c for c in 'KQkq' if c in rights) or '-'
    four = board_side + (' ' + canonical_rights + ' ' + ep).encode('ascii')
    return Row(fen, int(score_text), results[result_text], 2 * (f - 1) + (side == 'b'),
               dict(six_field=fen.encode('ascii'), four_field=four, board_stm=board_side))


def load_pins(path: Path) -> dict[str, str]:
    pins = {}
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            item = json.loads(line)
            digest = item.get('actual_md5')
            if item.get('match') is not True or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{32}', digest) or digest != item.get('expected_md5'):
                raise ValueError('unverified input pin')
            key = str(Path(item['path']).resolve()).casefold()
            if key in pins:
                raise ValueError('duplicate input pin')
            pins[key] = digest
    if not pins:
        raise ValueError('empty input pins')
    return pins


def iter_rows(path: Path, expected_md5: str, receipt: dict):
    """Yield every physical row, including invalid rows; hash every consumed byte.

    An unconsumed iterator is incomplete. Never use its partial receipt for PASS.
    Long rows are drained in bounded chunks and count once, without large buffers.
    """
    path = safe_path(path)
    before = path.stat()
    receipt.update(path=str(path), expected_md5=expected_md5, rows=0, valid_key_rows=0,
                   parse_failures=0, missing_key_rows=0, key_fill_rate=None, complete=False)
    digest = hashlib.md5()
    with path.open('rb') as stream:
        while raw := stream.readline(4097):
            digest.update(raw)
            long = len(raw) > 4096
            if long:
                while not raw.endswith(b'\n'):
                    raw = stream.readline(4097)
                    if not raw:
                        break
                    digest.update(raw)
            receipt['rows'] += 1
            try:
                if long:
                    raise ValueError('long row')
                parsed = parse_row(raw)
            except ValueError:
                parsed = None
                receipt['parse_failures'] += 1
                receipt['missing_key_rows'] += 1
            else:
                receipt['valid_key_rows'] += 1
            if receipt['rows'] % 65536 == 0:
                free_guard()
            yield receipt['rows'], parsed
    after = path.stat()
    actual = digest.hexdigest()
    receipt['actual_md5'] = actual
    receipt['key_fill_rate'] = receipt['valid_key_rows'] / receipt['rows'] if receipt['rows'] else None
    if actual != expected_md5:
        raise ValueError(f'input hash mismatch: {path}')
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f'input metadata changed: {path}')
    receipt['complete'] = True


def final_verdict(*, authenticated: bool, complete: bool, overlaps: int, unknowns: int) -> str:
    if any(type(v) is not int or v < 0 for v in (overlaps, unknowns)):
        raise ValueError('nonnegative integer counts required')
    if overlaps:
        return 'FAIL'
    if authenticated is not True or complete is not True or unknowns:
        return 'UNVERIFIED'
    return 'PASS'


def guard_selection(rows: list[tuple[int, int]], *, boundary: int, k: int):
    """Additional ply guard around an independently certified two-game boundary.

    This utility never certifies the boundary, game identities, or a final split.
    Entire ambiguous components must already have been removed by the caller.
    """
    if type(k) is not int or k < 8:
        raise ValueError('K at least eight required')
    if type(boundary) is not int or boundary <= 0:
        raise ValueError('positive boundary row ID required')
    previous = 0
    for row, ply in rows:
        if type(row) is not int or row <= previous or type(ply) is not int or ply < 0:
            raise ValueError('ordered unique positive row IDs and nonnegative integer plies required')
        previous = row
    if boundary not in {row for row, _ in rows}:
        raise ValueError('boundary row not found')
    left = [(row, ply) for row, ply in rows if row <= boundary]
    right = [(row, ply) for row, ply in rows if row > boundary]
    if not left or not right:
        raise ValueError('both sides required')
    left_end, right_start = left[-1][1], right[0][1]
    kept, dropped = [], []
    for row, ply in rows:
        distance = left_end - ply if row <= boundary else ply - right_start
        (dropped if distance <= k else kept).append(row)
    return kept, dropped
