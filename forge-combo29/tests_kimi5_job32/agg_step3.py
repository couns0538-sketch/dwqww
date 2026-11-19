#!/usr/bin/env python3
"""kimi5 job 32 Step 3 aggregation: one line per run (sums, cls0/cls4 reached+fired, movmax,
equal rows vs base), and the three-pair equality per boundary setting.
usage: agg_step3.py <jobdir>"""
import json
import os
import sys

J = sys.argv[1]
R = os.path.join(J, 'rows3')

def load(p):
    return json.load(open(p))

base = {s: load(f'{J}/kaA/cls_{s}_d12.json') for s in 'OG'}

def cls_sums(j):
    ranc = {}
    for search in j['ranc']:
        for c, r, f in search:
            a = ranc.setdefault(c, [0, 0])
            a[0] += r
            a[1] += f
    return ranc

def movmax(j):
    mm = [0, 0, 0]
    for search in j['hpmovmax']:
        if search:
            for d in range(3):
                mm[d] = max(mm[d], search[d])
    return mm

def eq(a, b):
    return sum(1 for i in range(a['n_positions'])
               if a['per_position'][i] == b['per_position'][i] and a['bestmove'][i] == b['bestmove'][i])

tags = ['lqb99', 'lqb100', 'lqd161', 'lqd160', 'lmp19', 'lmp20', 'lqb300',
        'lqb100_hpd0', 'lqb100_hpm20000', 'lqb100_hpboth0',
        'lqd160_hpd0', 'lqd160_hpm20000', 'lqd160_hpboth0',
        'lmp20_hpd0', 'lmp20_hpm20000', 'lmp20_hpboth0']
print('run set nodes_sum eq_vs_base cls0_r cls0_f cls4_r cls4_f movmax1 movmax2 movmax3 fired_classes')
for t in ['base'] + tags:
    for s in 'OG':
        j = base[s] if t == 'base' else load(f'{R}/{t}_{s}_d12.json')
        ranc = cls_sums(j)
        mm = movmax(j)
        fc = sorted(c for c in range(8) if ranc.get(c, [0, 0])[1] > 0)
        print(f"{t} {s} {j['nodes_sum']} {eq(j, base[s])}/{j['n_positions']} "
              f"{ranc.get(0, [0, 0])[0]} {ranc.get(0, [0, 0])[1]} {ranc.get(4, [0, 0])[0]} {ranc.get(4, [0, 0])[1]} "
              f"{mm[0]} {mm[1]} {mm[2]} {fc}")
print()
for x in ('lqb100', 'lqd160', 'lmp20'):
    runs = {k: {s: load(f'{R}/{x}_{k}_{s}_d12.json') for s in 'OG'}
            for k in ('hpd0', 'hpm20000', 'hpboth0')}
    pairs = []
    for a, b in (('hpd0', 'hpm20000'), ('hpd0', 'hpboth0'), ('hpm20000', 'hpboth0')):
        n = sum(eq(runs[a][s], runs[b][s]) for s in 'OG')
        pairs.append(f"{a}=={b}: {n}/553")
    print(f"{x}: " + ' | '.join(pairs))
