#!/usr/bin/env python3
"""compare_runs.py - node identity of two uci_tb.py runs: depth, score, nodes, bestmove and pv of every row must be equal.

usage: python -I -B compare_runs.py <a.jsonl> <b.jsonl> [--json out.json]
Fails closed: rows missing on either side, any row with an `invalid` engine line, fewer distinct result rows than n / 10 (a degenerate
run, e.g. all rows from one position). Exit 0 = IDENTICAL, 1 = differs or refused.
"""
import argparse
import json
import sys

KEYS = ('depth', 'score_type', 'score', 'nodes', 'bestmove', 'pv')


def load(path):
    rows = {}
    for line in open(path, encoding='utf-8'):
        r = json.loads(line)
        rows[r['fen']] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    x, y = load(a.a), load(a.b)
    res = {'a': a.a, 'b': a.b, 'rows_a': len(x), 'rows_b': len(y), 'different': 0, 'invalid': 0, 'nodes_a': 0, 'nodes_b': 0}
    examples = []
    distinct = set()
    if set(x) != set(y):
        res['row_sets_differ'] = len(set(x) ^ set(y))
    for fen in set(x) & set(y):
        p, q = x[fen], y[fen]
        res['invalid'] += ('invalid' in p) + ('invalid' in q)
        res['nodes_a'] += p.get('nodes') or 0
        res['nodes_b'] += q.get('nodes') or 0
        distinct.add((p['score'], p['nodes'], p['bestmove']))
        if any(p.get(k) != q.get(k) for k in KEYS):
            res['different'] += 1
            if len(examples) < 5:
                examples.append({'fen': fen, 'a': {k: p.get(k) for k in KEYS[:5]}, 'b': {k: q.get(k) for k in KEYS[:5]}})
    res['distinct_rows'] = len(distinct)
    degenerate = len(distinct) < max(1, len(x) // 10)
    ok = res['different'] == 0 and res['invalid'] == 0 and 'row_sets_differ' not in res and not degenerate and len(x) > 0
    res['verdict'] = 'IDENTICAL' if ok else ('DEGENERATE' if degenerate else 'DIFFERENT')
    res['examples'] = examples
    print(json.dumps(res))
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
