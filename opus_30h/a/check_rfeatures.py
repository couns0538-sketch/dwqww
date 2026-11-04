#!/usr/bin/env python3
"""check_rfeatures.py <rfeatures output file> <kb map one|rank4|rank4x2> <mirror 0|1> - Opus 30-h job: the Rust feature map of
forge-v2-bullet `r` mode (forge_r.rs) against o30_fit.py's features() (which reproduces the engine through the scorer:
o30_fit.py selfcheck), row by row: stm / ntm index lists, output bucket (piece count), stm, and the result / score / hce
fields against the FPOS / FHCE decoding rules. Exit 0 = every row equal."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_fit import features  # noqa: E402
from o30_v2net import king_map, output_map  # noqa: E402


def main():
    path, kbname, mirror = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
    kmap = np.array(king_map(kbname), np.int64)
    omap = output_map(8)
    lines = [l.rstrip('\n') for l in open(path, encoding='utf-8')]
    rows = bad = 0
    i = 0
    while i + 3 < len(lines) and lines[i].startswith('P '):
        board = np.frombuffer(bytes.fromhex(lines[i][2:]), np.uint8).reshape(1, 32)
        s_rust = [int(x) for x in lines[i + 1][2:].split()]
        n_rust = [int(x) for x in lines[i + 2][2:].split()]
        f = dict(zip(lines[i + 3].split()[0::2], lines[i + 3].split()[1::2]))
        stm = np.array([int(f['M'])], np.int64)
        i_s, _, i_n, _, cnt = features(board, stm, kmap, mirror)
        ok = list(i_s) == s_rust and list(i_n) == n_rust and omap[min(int(cnt[0]), 32)] == int(f['B'])
        rows += 1
        if not ok:
            bad += 1
            if bad <= 3:
                print('MISMATCH row', rows, list(i_s)[:6], s_rust[:6], omap[min(int(cnt[0]), 32)], f['B'])
        i += 4
    print(f'rows {rows}, mismatches {bad} -> {"PASS" if rows and not bad else "FAIL"}')
    sys.exit(0 if rows and not bad else 1)


if __name__ == '__main__':
    main()
