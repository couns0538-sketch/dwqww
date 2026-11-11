#!/usr/bin/env python3
"""eval_compare.py - JOB D (own code, 2026-11-11): compare two `evalfens` dumps position by position.

  eval_compare.py --ref REF.tsv --cand CAND.tsv --fens FENS.txt --name LABEL --out OUT.json [--top 10]

Each dump line: fen line index, total, network, hce, kernel_ok (centipawns, side to move). Reported for the
total static evaluation (and separately for the network term and the hand-crafted term): exact-match count,
maximum absolute error, mean absolute error, mean signed error (cand - ref), a histogram of |error|, sign
flips of the total, and the --top worst positions with their FEN. A finite set shows agreement on that set.
"""
import argparse
import json
import sys

BINS = [(0, 0), (1, 2), (3, 4), (5, 9), (10, 19), (20, 49), (50, 10 ** 9)]


def load(path):
    rows = {}
    with open(path, encoding='ascii') as f:
        for line in f:
            p = line.split('\t')
            if len(p) >= 5:
                rows[int(p[0])] = tuple(int(x) for x in p[1:5])
    return rows


def stats(pairs):
    n = len(pairs)
    d = [c - r for r, c in pairs]
    a = [abs(x) for x in d]
    hist = {}
    for lo, hi in BINS:
        key = str(lo) if lo == hi else (f'>={lo}' if hi >= 10 ** 9 else f'{lo}-{hi}')
        hist[key] = sum(1 for x in a if lo <= x <= hi)
    return {'n': n, 'exact': sum(1 for x in a if x == 0), 'max_abs': max(a) if a else 0,
            'mean_abs': (sum(a) / n) if n else 0.0, 'mean_signed': (sum(d) / n) if n else 0.0,
            'ge20': sum(1 for x in a if x >= 20), 'hist_abs_cp': hist}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--fens', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--top', type=int, default=10)
    a = ap.parse_args()
    ref, cand = load(a.ref), load(a.cand)
    fens = [ln.strip() for ln in open(a.fens, encoding='utf-8', errors='replace') if ln.strip()]
    common = sorted(set(ref) & set(cand))
    res = {'name': a.name, 'ref': a.ref, 'cand': a.cand, 'fen_lines': len(fens), 'ref_rows': len(ref),
           'cand_rows': len(cand), 'compared': len(common),
           'only_in_one': len(set(ref) ^ set(cand))}
    for col, label in ((0, 'total'), (1, 'network'), (2, 'hce')):
        res[label] = stats([(ref[i][col], cand[i][col]) for i in common])
    res['total']['sign_flips'] = sum(1 for i in common if (ref[i][0] > 0 > cand[i][0]) or (ref[i][0] < 0 < cand[i][0]))
    res['cand_kernel_mismatch'] = sum(1 for i in common if cand[i][3] == 0)
    res['cand_kernel_checked'] = sum(1 for i in common if cand[i][3] in (0, 1))
    worst = sorted(common, key=lambda i: -abs(cand[i][0] - ref[i][0]))[:a.top]
    res['worst'] = [{'fen_line': i, 'fen': fens[i] if i < len(fens) else '?', 'ref_total': ref[i][0],
                     'cand_total': cand[i][0], 'ref_network': ref[i][1], 'cand_network': cand[i][1]}
                    for i in worst if cand[i][0] != ref[i][0]]
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, indent=1)
    t = res['total']
    print(f"{a.name}: compared {res['compared']} (only in one {res['only_in_one']}); total exact {t['exact']} "
          f"max|d| {t['max_abs']} mean|d| {t['mean_abs']:.3f} signed {t['mean_signed']:+.3f} >=20cp {t['ge20']} "
          f"sign flips {t['sign_flips']}; network exact {res['network']['exact']} max {res['network']['max_abs']}; "
          f"hce exact {res['hce']['exact']} max {res['hce']['max_abs']}; kernel mismatch "
          f"{res['cand_kernel_mismatch']}/{res['cand_kernel_checked']}")
    print('  hist |d| cp: ' + ', '.join(f'{k}: {v}' for k, v in t['hist_abs_cp'].items()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
