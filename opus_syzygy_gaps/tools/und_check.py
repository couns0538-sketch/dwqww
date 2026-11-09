#!/usr/bin/env python3
"""und_check.py <fens> <root_boundary.out> <uci bad.tsv> [--expect-undecided N] - are the engine's bad boundary rows (exact_check.py --list) all on roots the root walk left undecided?

A root is undecided when tb_root shows no display: the third column ("displayed score (or -)", see tb_root.cpp) is `-`. Bad rows on undecided roots are the documented limit; a bad row on a decided
root is a finding. --expect-undecided guards this tool's own column choice: the count must equal no_display of exact_check.py on the same rows plus any undecided row that check does not judge.
Exit 1 on a finding or a failed guard. Standard library only.
"""
import argparse
import sys
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fens')
    ap.add_argument('root')
    ap.add_argument('bad')
    ap.add_argument('--expect-undecided', type=int, default=-1)
    a = ap.parse_args()
    fens = [l.strip() for l in open(a.fens, encoding='utf-8') if l.strip()]
    index = {f: i for i, f in enumerate(fens)}
    display = {}
    for line in open(a.root, encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        display[int(p[0]) - 1] = p[2] if len(p) > 2 else ''
    undecided_roots = sum(1 for v in display.values() if v == '-')
    counts = Counter()
    decided = []
    for line in open(a.bad, encoding='utf-8'):
        b = line.rstrip('\n').split('\t')
        i = index.get(b[1])
        if i is None:
            counts[(b[0], 'fen not found')] += 1
            continue
        kind = 'undecided' if display.get(i) == '-' else 'decided'
        counts[(b[0], kind)] += 1
        if kind == 'decided':
            decided.append(b)
    print(f'root rows {len(display)} of {len(fens)} fens, undecided roots {undecided_roots}')
    print(' '.join(f'{k[0]}/{k[1]}={v}' for k, v in sorted(counts.items())) or 'no bad rows')
    for b in decided[:10]:
        print('DECIDED', '\t'.join(b)[:160])
    ok = not decided and not any(k[1] == 'fen not found' for k in counts)
    if a.expect_undecided >= 0 and undecided_roots != a.expect_undecided:
        print(f'GUARD FAILED: {undecided_roots} undecided roots, expected {a.expect_undecided}')
        ok = False
    print('und_check:', 'ALL BAD ROWS ON UNDECIDED ROOTS' if ok else 'FINDING')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
