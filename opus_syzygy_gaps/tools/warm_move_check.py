#!/usr/bin/env python3
"""warm_move_check.py - does the move played on a warm table keep the result? warm_claims.py clock rows against oracle_exact.py rows of the same later-clock FENs.

usage: python -I -B warm_move_check.py <exact.jsonl> <name=warm_claims.jsonl> [...]
Counts, per run, the roots where the warm and the cold move are worse than the best class. Exit 1 if a row has no oracle value. Search quality on these roots, no Elo claim.
"""
import json
import sys

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


def main():
    oracle = {}
    for line in open(sys.argv[1], encoding='utf-8'):
        r = json.loads(line)
        oracle[r['fen']] = r
    bad_sets = {}
    for spec in sys.argv[2:]:
        name, path = spec.split('=', 1)
        cnt = {'rows': 0, 'unresolved': 0, 'warm_worse': 0, 'cold_worse': 0}
        worse = set()
        for line in open(path, encoding='utf-8'):
            r = json.loads(line)
            o = oracle[r['fen']]
            cnt['rows'] += 1
            if o['unresolved'] or o.get('best') is None or not o['moves']:
                cnt['unresolved'] += 1
                continue
            if RANK[o['moves'][r['warm_move']]] != o['best']:
                cnt['warm_worse'] += 1
                worse.add(r['fen'])
            if RANK[o['moves'][r['cold_move']]] != o['best']:
                cnt['cold_worse'] += 1
        bad_sets[name] = worse
        print(name, json.dumps(cnt))
    names = list(bad_sets)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            print(f'{x} vs {y}: only {x} {len(bad_sets[x] - bad_sets[y])}, only {y} {len(bad_sets[y] - bad_sets[x])}')


if __name__ == '__main__':
    main()
