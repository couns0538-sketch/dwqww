#!/usr/bin/env python3
"""kimi5 job 32 Step 4 aggregation: per setting, equal-row counts T vs B and B vs Bm on O, G
and the combined 553; plus the base DMAX / last-iteration table.
usage: agg_step4.py <jobdir>"""
import json
import os
import sys

J = sys.argv[1]
R = os.path.join(J, 'rows4')

def load(p):
    return json.load(open(p))

def eq(a, b):
    return sum(1 for i in range(a['n_positions'])
               if a['per_position'][i] == b['per_position'][i] and a['bestmove'][i] == b['bestmove'][i])

def med(v):
    v = sorted(v)
    n = len(v)
    return (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2) if n else 0

print('set last_iter_min med max | dmax_min med max')
for s in 'OG':
    j = load(f'{J}/kaA/cls_{s}_n20000.json')
    it = j['last_iter']
    dm = [x['DMAX'][0] for x in j['ran']]
    print(f"{s} {min(it)} {med(it)} {max(it)} | {min(dm)} {med(dm)} {max(dm)}")

print()
print('setting gate B_O B_G top | T==B O G 553 | B==Bm O G 553 | verdict')
settings = [
    ('RfpDepth', 'depth <= X (1937)', 'rfpd', 14, 64, 15),
    ('FutilityDepth', 'lmr_depth <= X (2132)', 'futd', 14, 64, 15),
    ('SingularDepth', 'depth >= X (2192)', 'singd', 15, 65, 20),
    ('IirDepth', 'depth >= X (2033)', 'iird', 15, 65, 20),
    ('ProbcutDepth', 'depth >= X (1996)', 'pbd', 15, 65, 20),
    ('CheckExtensionDepth', 'gives_check && depth >= X (2218)', 'ced', 15, 65, 30),
    ('HistoryBonusMax', 'min(X, raw(d)) (324)', 'hbm', 5428, 101728, 10000),
]
for name, gate, tag, bo, bg, top in settings:
    T = {s: load(f'{R}/{tag}T_{s}_n20000.json') for s in 'OG'}
    B = {s: load(f'{R}/{tag}B_{s}_n20000.json') for s in 'OG'}
    Bm = {s: load(f'{R}/{tag}Bm_{s}_n20000.json') for s in 'OG'}
    tb_o, tb_g = eq(T['O'], B['O']), eq(T['G'], B['G'])
    bb_o, bb_g = eq(B['O'], Bm['O']), eq(B['G'], Bm['G'])
    verdict = []
    verdict.append('O-flat' if tb_o == 200 else f'O-DIFFERS({200 - tb_o})')
    verdict.append('G-flat' if tb_g == 353 else f'G-DIFFERS({353 - tb_g})')
    verdict.append('below-differs-O' if bb_o < 200 else 'O-WIDER')
    verdict.append('below-differs-G' if bb_g < 353 else 'G-WIDER')
    print(f"{name} '{gate}' {bo} {bg} {top} | {tb_o} {tb_g} {tb_o + tb_g} | {bb_o} {bb_g} {bb_o + bb_g} | "
          + ' '.join(verdict))
