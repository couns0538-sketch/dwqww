#!/usr/bin/env python3
"""block_rule_check.py - cheap game-block rule on self-play text rows, checked against the R14 segment scan.

usage: python -I -B block_rule_check.py --out F:/odr/work/block_rule_013_014.json
Rule (writer invariants: one game's rows are written as one block in play order with the game's final result):
a new block starts at row i+1 when result(i+1) != result(i)  ("result_mismatch")  or  ply(i+1) <= ply(i)
("nonpositive_ply_gap"; ply = 2 * (fullmove - 1) + (1 if black to move)). Blocks are supersets of games as long as
those invariants hold (two games can merge into one block, a game is never cut). Reads the same range as the R14 scan
segments-production02 (last 100,000 rows of 012, all of 013 and 014, first 100,000 rows of 015) read-only, counts
breaks per class and at the three file seams, and writes one JSON (refuses an existing --out).
"""
import argparse
import collections
import hashlib
import json
import os
import sys
import time

SRC = 'D:/grok-pc-data/selfplay_out/forge_selfplay_{:03d}.txt'


def rows(path, first=None, last=None):
    with open(path, 'rb') as f:
        if last is not None:
            dq = collections.deque(maxlen=last)
            for n, line in enumerate(f, 1):
                dq.append((n, line))
            yield from dq
            return
        for n, line in enumerate(f, 1):
            if first is not None and n > first:
                return
            yield n, line


def parse(line):
    fen, _score, result = line.decode('ascii').split('|')
    f = fen.split()
    ply = 2 * (int(f[5]) - 1) + (1 if f[1] == 'b' else 0)
    return ply, result.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing existing {a.out}')
    t0 = time.time()
    plan = [(12, None, 100000), (13, None, None), (14, None, None), (15, 100000, None)]
    counts = collections.Counter()
    seams = []
    prev = None
    nrows = 0
    md5 = {}
    for num, first, last in plan:
        path = SRC.format(num)
        h = hashlib.md5()
        firstrow = True
        for n, line in rows(path, first=first, last=last):
            h.update(line)
            ply, res = parse(line)
            nrows += 1
            if prev is not None:
                pply, pres, pfile, pline = prev
                if res != pres:
                    cls = 'result_mismatch'
                elif ply <= pply:
                    cls = 'nonpositive_ply_gap'
                else:
                    cls = 'same_block'
                counts[cls] += 1
                if firstrow:
                    seams.append({'from': f'{pfile:03d}:{pline}', 'to': f'{num:03d}:{n}', 'class': cls})
            prev = (ply, res, num, n)
            firstrow = False
        md5[f'{num:03d} ({"last %d" % last if last else "first %d" % first if first else "all"} rows)'] = h.hexdigest()
    breaks = counts['result_mismatch'] + counts['nonpositive_ply_gap']
    out = {
        'rule': 'new block when result changes or ply does not increase',
        'range': 'last 100,000 rows of 012, all of 013 and 014, first 100,000 rows of 015 (as segments-production02)',
        'rows': nrows, 'adjacent_pairs': sum(counts.values()), 'classes': dict(counts),
        'blocks': breaks + 1, 'mean_rows_per_block': round(nrows / (breaks + 1), 2), 'seams': seams,
        'md5_of_bytes_read': md5, 'seconds': round(time.time() - t0, 1),
        'compare_r14_segments_production02': {'result_mismatch': 121467, 'nonpositive_ply_gap': 67730,
                                              'segments': 293783},
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out + '.part', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
    os.replace(a.out + '.part', a.out)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
