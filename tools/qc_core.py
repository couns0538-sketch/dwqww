"""Original streaming statistics and documented Forge FPOS-v1 column reader."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path
import re
import struct

MATE = 30000
PIECES = ' PNBRQKpnbrqk'
EDGES = (-30000, -10000, -3000, -1000, -300, -100, 0, 100, 300, 1000, 3000, 10000, 30000)


def signed_score(value):
    if type(value) is int:
        score = value
    elif isinstance(value, str) and re.fullmatch(r'[+-]?[0-9]+', value):
        score = int(value)
    else:
        raise ValueError('score must be an integer')
    if not -32767 <= score <= 32767:
        raise ValueError('score outside documented FPOS range')
    return score


def is_mate(score):
    return abs(signed_score(score)) >= MATE


def outcome(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError('boolean outcome')
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('invalid outcome') from None
    if not number.is_finite() or number not in (0, Decimal('0.5'), 1):
        raise ValueError('outcome must be White 0, 0.5, 1 or null')
    return float(number)


def fen_info(fen):
    if not isinstance(fen,str) or not fen.isascii() or any(ord(c)<32 and c!='\t' for c in fen):
        raise ValueError('original single-line ASCII FEN required')
    fields = fen.split()
    if len(fields) != 6 or fields[1] not in ('w', 'b'):
        raise ValueError('full six-field FEN required')
    ranks = fields[0].split('/')
    if len(ranks) != 8:
        raise ValueError('eight ranks required')
    board = bytearray(32)
    pieces, phase = 0, 0
    for rank, text in enumerate(reversed(ranks)):
        file = 0
        for char in text:
            if char in '12345678':
                file += int(char)
            elif char in PIECES[1:] and file < 8:
                square = rank * 8 + file
                board[square // 2] |= PIECES.index(char) << (4 * (square % 2))
                pieces += 1
                phase += {'n': 1, 'b': 1, 'r': 2, 'q': 4}.get(char.lower(), 0)
                file += 1
            else:
                raise ValueError('invalid board symbol')
            if file > 8:
                raise ValueError('rank overflow')
        if file != 8:
            raise ValueError('rank width not eight')
    if fields[0].count('K') != 1 or fields[0].count('k') != 1:
        raise ValueError('exactly one king per side required')
    rights = fields[2]
    if rights != '-' and (not re.fullmatch('[KQkq]+', rights) or len(set(rights)) != len(rights)):
        raise ValueError('invalid standard-chess castling rights')
    if fields[3] != '-' and not re.fullmatch('[a-h][36]', fields[3]):
        raise ValueError('invalid EP square')
    if not all(re.fullmatch('[0-9]+', v) for v in fields[4:]) or int(fields[5]) < 1:
        raise ValueError('invalid clocks')
    phase = min(24, phase)
    return dict(fen=' '.join(fields), board=bytes(board), stm=fields[1], pieces=pieces,
                phase=phase, phase_group='end' if phase <= 8 else 'middle' if phase <= 16 else 'early')


def histogram_bucket(score):
    low = '-inf'
    for high in EDGES:
        if score < high:
            return f'[{low},{high})'
        low = str(high)
    return f'[{low},inf)'


class Moments:
    def __init__(self):
        self.n = self.total = self.squares = 0
        self.minimum = self.maximum = None
        self.histogram = Counter()

    def add(self, value):
        self.n += 1
        self.total += value
        self.squares += value * value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)
        self.histogram[histogram_bucket(value)] += 1

    def report(self):
        return dict(rows=self.n, sum=self.total, minimum=self.minimum, maximum=self.maximum,
                    mean=self.total / self.n if self.n else None,
                    standard_deviation=math.sqrt(max(0, self.squares / self.n - (self.total / self.n)**2)) if self.n else None,
                    histogram=dict(self.histogram))


class Profile:
    def __init__(self):
        self.n = self.mates = self.abs_delta = self.changed = 0
        self.score_stm, self.score_white, self.old = Moments(), Moments(), Moments()
        self.stm, self.wdl_stm, self.wdl_white = Counter(), Counter(), Counter()
        self.pieces, self.phase, self.phase_group, self.splits = Counter(), Counter(), Counter(), Counter()
        self.pair_n = 0

    def add(self, fen, score, result, split, old=None):
        info = fen_info(fen)
        score = signed_score(score)
        result = outcome(result)
        old = signed_score(old) if old is not None else None
        self.n += 1
        self.mates += is_mate(score)
        self.score_stm.add(score)
        self.score_white.add(score if info['stm'] == 'w' else -score)
        self.stm[info['stm']] += 1
        white = 'unknown' if result is None else {0: 'loss', 0.5: 'draw', 1: 'win'}[result]
        stm_result = result if result is None or info['stm'] == 'w' else 1 - result
        side = 'unknown' if stm_result is None else {0: 'loss', 0.5: 'draw', 1: 'win'}[stm_result]
        self.wdl_white[white] += 1
        self.wdl_stm[side] += 1
        self.pieces[info['pieces']] += 1
        self.phase[info['phase']] += 1
        self.phase_group[info['phase_group']] += 1
        self.splits[split] += 1
        if old is not None:
            self.old.add(old)
            self.pair_n += 1
            self.abs_delta += abs(old - score)
            self.changed += old != score
        return info

    def report(self):
        return dict(rows=self.n, mate_rows=self.mates, score_stm=self.score_stm.report(),
                    score_white=self.score_white.report(), wdl_stm=dict(self.wdl_stm), wdl_white=dict(self.wdl_white),
                    side_to_move=dict(self.stm), piece_count=dict(self.pieces), material_phase=dict(self.phase),
                    phase_group=dict(self.phase_group), splits=dict(self.splits),
                    paired_old_score=dict(rows=self.pair_n, changed=self.changed, mean_absolute_delta=self.abs_delta / self.pair_n if self.pair_n else None,
                                          old_score_stm=self.old.report()))


def decode_pos(payload):
    if len(payload) < 16:
        raise ValueError('truncated FPOS header')
    magic, version, n = struct.unpack_from('<4sIQ', payload)
    if magic != b'FPOS' or version != 1 or len(payload) != 16 + 35 * n:
        raise ValueError('FPOS magic/version/size/count mismatch')
    for index in range(n):
        board = payload[16 + index * 32:16 + (index + 1) * 32]
        if any((b & 15) > 12 or (b >> 4) > 12 for b in board):
            raise ValueError('invalid FPOS piece code')
        score = signed_score(struct.unpack_from('<h', payload, 16 + 32 * n + index * 2)[0])
        meta = payload[16 + 34 * n + index]
        if meta > 5:
            raise ValueError('invalid FPOS metadata')
        yield board, score, meta


def read_pos(path):
    # Small fixture/shard API. Production uses Snapshot.bytes before decode_pos.
    yield from decode_pos(Path(path).read_bytes())
