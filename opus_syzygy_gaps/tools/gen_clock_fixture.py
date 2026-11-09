#!/usr/bin/env python3
"""gen_clock_fixture.py - clock-boundary root positions. Takes clock-0 FENs with Fathom labels (wdl, signed dtz) and
writes each decided position with halfmove clocks around the boundary dtz + clock = 100, plus clocks 98, 99, 100 for draws
and cursed wins / blessed losses. The full-move number is raised so that clock and move number are consistent.

usage: python -I -B gen_clock_fixture.py <fens> <fathom labels> <out.fens> [--max 20000] [--seed 7]
Keeps at most --max lines, sampled evenly over classes (sum offset, wdl, large / small dtz).
"""
import argparse
import os
import random
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fens')
    ap.add_argument('labels')
    ap.add_argument('out')
    ap.add_argument('--max', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    rng = random.Random(a.seed)
    classes = {}
    for fen, lab in zip(open(a.fens, encoding='ascii'), open(a.labels, encoding='ascii')):
        fen = fen.strip()
        p = lab.split()
        if len(p) < 3 or p[2] != 'ok' or p[0] in ('NA', '99'):
            continue
        wdl, dtz = int(p[0]), int(p[1])
        f = fen.split()
        d = abs(dtz)
        if wdl == 0 or abs(wdl) == 1:
            offsets = [(c, 'wdl%+d:clock%d' % (wdl, c)) for c in (1, 50, 97, 98, 99)]
        else:
            offsets = []
            for off in (-3, -2, -1, 0, 1, 2):  # dtz + clock = 100 + off
                c = 100 + off - d
                if 0 < c < 100:
                    offsets.append((c, 'wdl%+d:off%+d:%s' % (wdl, off, 'big' if d >= 30 else 'small')))
        for c, key in offsets:
            move_no = max(1, c // 2 + 1)
            line = ' '.join(f[:4] + [str(c), str(move_no)])
            classes.setdefault(key, []).append(line)
    keys = sorted(classes)
    per = max(1, a.max // max(1, len(keys)))
    written = 0
    with open(a.out, 'w', encoding='ascii', newline='\n') as out:
        for k in keys:
            rows = classes[k]
            rng.shuffle(rows)
            for line in rows[:per]:
                out.write(line + '\n')
                written += 1
    print(f'wrote {written} lines; classes:', ' '.join(f'{k}={min(len(classes[k]), per)}' for k in keys))


if __name__ == '__main__':
    main()
