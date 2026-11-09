#!/usr/bin/env python3
"""move_quality.py - does the engine's move keep the game-theoretic result? Compares runs (uci_tb.py JSONL) with the python-chess
oracle's per-move values (oracle_chess.py JSONL). Clock-0 roots only, the 50-move rule on.

usage: python -I -B move_quality.py <oracle.jsonl> <name=run.jsonl> [<name=run.jsonl> ...] [--json out.json]
A blunder: the outcome of the chosen move is worse than the best outcome among the legal moves (win > cursed > draw > blessed > loss).
For each run: roots, blunders, by best-outcome class. For each pair of runs: discordant roots (a blunders, b not; b blunders, a not), and the
exact two-sided sign-test p value on the discordant roots. This is search quality on the given roots at the given depth, not an Elo claim.
"""
import argparse
import json
import math

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


def outcome(m):
    if m['mate']:
        return 'win'
    w = m['child_wdl']
    if w is None:
        return None
    return {2: 'loss', 1: 'blessed', 0: 'draw', -1: 'cursed', -2: 'win'}[w]


def sign_p(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    # exact two-sided binomial with p = 1/2, in logs for large n
    total = 0.0
    log_half_n = -n * math.log(2)
    for i in range(k + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + log_half_n)
    return min(1.0, 2 * total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracle')
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    table = {}
    for line in open(a.oracle, encoding='utf-8'):
        r = json.loads(line)
        if r['clock'] != 0 or not r['moves']:
            continue
        vals = {}
        ok = True
        for m in r['moves']:
            o = outcome(m)
            if o is None:
                ok = False
                break
            vals[m['uci']] = RANK[o]
        if ok:
            table[r['fen']] = vals
    res = {'oracle_roots': len(table), 'runs': {}, 'pairs': {}}
    blunders = {}
    for spec in a.runs:
        name, path = spec.split('=', 1)
        count = {2: [0, 0], 1: [0, 0], 0: [0, 0], -1: [0, 0], -2: [0, 0]}
        bad = set()
        nodes = 0
        roots = 0
        for line in open(path, encoding='utf-8'):
            r = json.loads(line)
            vals = table.get(r['fen'])
            if vals is None or r.get('bestmove') is None:
                continue
            roots += 1
            nodes += r.get('nodes') or 0
            best = max(vals.values())
            count[best][0] += 1
            if vals.get(r['bestmove'], -9) < best:
                count[best][1] += 1
                bad.add(r['fen'])
        blunders[name] = bad
        res['runs'][name] = {'roots': roots, 'nodes': nodes, 'blunders': len(bad),
                             'by_best': {str(k): {'roots': v[0], 'blunders': v[1]} for k, v in count.items()}}
    names = list(blunders)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            only_x = len(blunders[x] - blunders[y])
            only_y = len(blunders[y] - blunders[x])
            res['pairs'][f'{x}_vs_{y}'] = {'only_' + x: only_x, 'only_' + y: only_y, 'sign_p': sign_p(only_x, only_y)}
    print(json.dumps(res, indent=1))
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
