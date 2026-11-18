"""Decode and cross-check the C10 search-counter protocol (one response per go)."""
MAIN = ('nm','fh','mate','t1','t2')
PIECE = ('p2_5','p6_9','p10_15','p16_32')
DEPTH = ('d1_6','d7_10','d11plus')
JOINT = tuple(f'{p}_{d}' for p in PIECE for d in DEPTH)
CLASS = PIECE + DEPTH + JOINT
ALL = MAIN + CLASS

def parse_counters(lines):
    row = {}
    for key, fields in (('guard10', MAIN), ('guard10cls', CLASS)):
        prefix = 'info string ' + key + ' '
        found = [s.strip() for s in lines if s.startswith(prefix)]
        if len(found) != 1:
            raise ValueError(f'expected one {key} line, got {len(found)}')
        words = found[0][len(prefix):].split()
        if tuple(words[::2]) != fields or len(words) != 2*len(fields):
            raise ValueError(f'unexpected {key} fields: {found[0]}')
        for name,value in zip(fields,words[1::2]):
            if not value.isascii() or not value.isdecimal():
                raise ValueError(f'invalid {name} value {value!r}')
            row[name] = int(value)
    if row['fh'] > row['nm'] or any(row[k] > row['fh'] for k in ('mate','t1','t2')):
        raise ValueError(f'impossible null/fail-high totals: {row}')
    if sum(row[p] for p in PIECE) != row['t1'] or sum(row[d] for d in DEPTH) != row['t1']:
        raise ValueError(f'counts fail to partition A: {row}')
    for p in PIECE:
        if row[p] != sum(row[f'{p}_{d}'] for d in DEPTH):
            raise ValueError(f'joint bins differ from {p}: {row}')
    for d in DEPTH:
        if row[d] != sum(row[f'{p}_{d}'] for p in PIECE):
            raise ValueError(f'joint bins differ from {d}: {row}')
    return row
