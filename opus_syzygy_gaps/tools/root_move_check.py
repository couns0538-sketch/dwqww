#!/usr/bin/env python3
"""root_move_check.py - UCI-level check on tablebase roots: the engine's bestmove and last reported score against the oracle.

usage: python -I -B root_move_check.py <oracle.jsonl> <run.jsonl> [--rule50 1] [--ranks tb_root.out] [--json out.json] [--list bad.tsv]
Uses root_check.outcome for each legal move (independent of engine code). Checks per root:
  M: the chosen move has the best outcome. Rows with an undecided move (rounded distance, sum exactly 100) are counted apart.
  S: the reported score class equals the best outcome: win (>= 31743 or positive mate), cursed (+2), draw (0), blessed (-2), loss. A real mate
     is accepted for win / loss only. Clock >= 100: the score must be 0 if a legal move exists.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from root_check import RANK, outcome  # noqa: E402


def score_class(r):
    if r.get('score') is None:
        return None
    if r['score_type'] == 'mate':
        return 'win' if r['score'] > 0 else 'loss'
    s = r['score']
    if s >= 31743:
        return 'win'
    if s <= -31743:
        return 'loss'
    return {2: 'cursed', 0: 'draw', -2: 'blessed'}.get(s, 'other')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracle')
    ap.add_argument('run')
    ap.add_argument('--rule50', type=int, default=1)
    ap.add_argument('--ranks', default='')
    ap.add_argument('--json', default='')
    ap.add_argument('--list', default='')
    a = ap.parse_args()
    oracle = {}
    rounded_rows = []
    for line in open(a.oracle, encoding='utf-8'):
        r = json.loads(line)
        oracle[r['fen']] = r
    if a.ranks:
        fens = [json.loads(l)['fen'] for l in open(a.oracle, encoding='utf-8')]
        rounded_rows = {}
        for fen, line in zip(fens, open(a.ranks, encoding='utf-8')):
            p = line.rstrip('\n').split('\t')
            rd = {}
            if len(p) > 6 and p[6] != '-':
                for item in p[6].split():
                    u, _r, _v, x = item.rsplit(':', 3)
                    rd[u] = x == '1'
            rounded_rows[fen] = rd
    cnt = {'roots': 0, 'M_bad': 0, 'S_bad': 0, 'undecided': 0, 'clock100': 0, 'no_moves': 0}
    bad = []
    for line in open(a.run, encoding='utf-8'):
        r = json.loads(line)
        o = oracle[r['fen']]
        cnt['roots'] += 1
        c = o['clock']
        if not o['moves']:
            cnt['no_moves'] += 1
            continue
        legal = {m['uci'] for m in o['moves']}
        if r['bestmove'] not in legal:
            bad.append(('L', r['fen'], f'illegal bestmove {r["bestmove"]}'))
            cnt['L_bad'] = cnt.get('L_bad', 0) + 1
            continue
        if c >= 100:
            cnt['clock100'] += 1
            if r.get('score') != 0:
                bad.append(('S', r['fen'], f'clock {c} score {r.get("score")}'))
                cnt['S_bad'] += 1
            continue
        vals = {}
        und = False
        rd = rounded_rows.get(r['fen'], {}) if rounded_rows else {}
        for m in o['moves']:
            oc, D = outcome(m, c, a.rule50 != 0)
            if oc is None:
                vals = None
                break
            vals[m['uci']] = oc
            if a.rule50 and D + c == 100 and oc in ('win', 'loss') and rd.get(m['uci'], False):
                und = True
        if vals is None:
            cnt['no_value'] = cnt.get('no_value', 0) + 1
            continue
        if und:
            cnt['undecided'] += 1
            continue
        best = max(RANK[v] for v in vals.values())
        if RANK[vals[r['bestmove']]] != best:
            bad.append(('M', r['fen'], f'chose {r["bestmove"]} {vals[r["bestmove"]]} best {best} score {r.get("score")}'))
            cnt['M_bad'] += 1
        sc = score_class(r)
        if sc is None or RANK.get(sc, 99) != best:
            bad.append(('S', r['fen'], f'score {r.get("score_type")} {r.get("score")} best {best} clock {c} dtz {o["dtz"]}'))
            cnt['S_bad'] += 1
    print(json.dumps(cnt))
    if a.json:
        json.dump(cnt, open(a.json, 'w'), indent=1)
    if a.list:
        with open(a.list, 'w', encoding='utf-8', newline='\n') as f:
            for b in bad:
                f.write('\t'.join(b) + '\n')


if __name__ == '__main__':
    main()
