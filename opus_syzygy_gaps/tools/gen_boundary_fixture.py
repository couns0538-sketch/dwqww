#!/usr/bin/env python3
"""gen_boundary_fixture.py - boundary rows for oracle_exact.py: from oracle_chess.py rows, roots with a move at distance + clock = 100, sorted by clock,
highest first; plus fixed review rows. Also writes clock-0 rows whose root is a cursed win / blessed loss or has a child at dtz -100 / +100 (WDL-only fixture).

usage: python -I -B gen_boundary_fixture.py <oracle.jsonl> [<oracle.jsonl> ...] --out <prefix> [--max 6000]
Writes <prefix>.boundary.fens and <prefix>.clock0.fens
"""
import argparse
import json
import os
import sys

REVIEW_ROWS = [
    '1B6/8/R7/4k3/8/8/K4Q2/8 b - - 96 49',
    '8/8/2RNR3/5k2/8/8/7K/8 b - - 96 49',
    '8/K7/5B2/8/2k5/3Q3N/8/8 b - - 96 49',
    '1r6/5K2/1k2Q3/8/8/4R3/8/8 b - - 96 49',
    '2K5/8/8/R7/3B4/8/3k4/5Q2 b - - 98 50',
    '8/8/1K6/B7/8/k7/5B2/3Q4 w - - 97 49',
    '8/7K/7Q/5k2/6q1/2Q5/8/8 w - - 97 49',
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracles', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--max', type=int, default=6000)
    a = ap.parse_args()
    for ext in ('.boundary.fens', '.clock0.fens'):
        if os.path.exists(a.out + ext):
            sys.exit(f'refusing: {a.out + ext} exists')
    boundary = {}
    clock0 = set()
    for path in a.oracles:
        for line in open(path, encoding='utf-8'):
            o = json.loads(line)
            if ' moves ' in o['fen']:
                continue
            c = o['clock']
            at_boundary = False
            for m in o['moves']:
                d = m['child_dtz']
                if d is None or m['zeroing'] or d == 0 or m['mate']:
                    continue
                if abs(d) + 1 + c == 100:
                    at_boundary = True
                if c == 0 and abs(d) == 100:
                    clock0.add(o['fen'])
            if at_boundary:
                boundary[o['fen']] = c
            if c == 0 and o['wdl'] in (1, -1):
                clock0.add(o['fen'])
    rows = sorted(boundary, key=lambda f: (-boundary[f], f))[:a.max]
    with open(a.out + '.boundary.fens', 'w', encoding='ascii', newline='\n') as f:
        for r in REVIEW_ROWS + [x for x in rows if x not in REVIEW_ROWS]:
            f.write(r + '\n')
    with open(a.out + '.clock0.fens', 'w', encoding='ascii', newline='\n') as f:
        for r in sorted(clock0):
            f.write(r + '\n')
    print(f'boundary rows {len(rows)} of {len(boundary)} + {len(REVIEW_ROWS)} review rows; clock-0 rows {len(clock0)}')


if __name__ == '__main__':
    main()
