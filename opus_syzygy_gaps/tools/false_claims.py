#!/usr/bin/env python3
"""false_claims.py - compare engine scores on roots above the loaded tables with the full-set oracle (Fathom batch output).

usage: python -I -B false_claims.py <fens> <fathom.out> <run.jsonl> [--json out.json] [--list out.tsv]
A root is searched with fewer tables than the oracle has, so its own result is not looked up: every TB-band or mate score
is something the search claims to have proved. Scores (cp) in the band 31743..31871 are TB claims, mate scores are mates.
False claim: TB win / mate win claimed and the oracle's WDL is not +2 (clock 0 roots); same for losses with -2.
(A cursed root (+1) has dtz > 100 by definition; a TB win or mate found by a search that stops at 100 quiet plies cannot be
true there, so it counts as false as well.)
Prints counts per class, with the sign accuracy of the search on decided roots as a secondary number.
"""
import argparse
import json
import sys

TB_LOW = 31743
MATE_LOW = 31872


def classify(row):
    if row.get('score') is None:
        return 'none'
    if row['score_type'] == 'mate':
        return 'mate_win' if row['score'] > 0 else 'mate_loss'
    s = row['score']
    if s >= TB_LOW:
        return 'tb_win'
    if s <= -TB_LOW:
        return 'tb_loss'
    return 'cp'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fens')
    ap.add_argument('fathom')
    ap.add_argument('run')
    ap.add_argument('--json', default='')
    ap.add_argument('--list', default='')
    a = ap.parse_args()
    fens = [l.strip() for l in open(a.fens, encoding='utf-8') if l.strip() and not l.startswith('#')]
    oracle = {}
    for fen, line in zip(fens, open(a.fathom, encoding='utf-8')):
        p = line.split()
        oracle[fen] = (None if p[0] in ('NA', '99') else int(p[0]), p[2] if len(p) > 2 else '')
    rows = [json.loads(l) for l in open(a.run, encoding='utf-8')]
    counts = {}
    false_rows = []
    sign_ok = sign_all = 0
    nodes = 0
    for r in rows:
        wdl, status = oracle[r['fen']]
        cls = classify(r)
        counts[cls] = counts.get(cls, 0) + 1
        nodes += r.get('nodes') or 0
        if wdl is None:
            counts['oracle_missing'] = counts.get('oracle_missing', 0) + 1
            continue
        is_false = (cls in ('tb_win', 'mate_win') and wdl != 2) or (cls in ('tb_loss', 'mate_loss') and wdl != -2)
        if is_false:
            key = 'false_' + cls
            counts[key] = counts.get(key, 0) + 1
            false_rows.append((cls, wdl, r['score'], r['depth'], r['nodes'], r['bestmove'], r['fen'], ' '.join(r['pv'])))
        if cls != 'none' and wdl != 0:
            s = r['score']
            sign_all += 1
            sign_ok += (s > 0) == (wdl > 0)
    res = {'rows': len(rows), 'nodes': nodes, 'counts': dict(sorted(counts.items())),
           'decided_sign_ok': sign_ok, 'decided_total': sign_all}
    print(json.dumps(res))
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
    if a.list:
        with open(a.list, 'w', encoding='utf-8', newline='\n') as f:
            for row in false_rows:
                f.write('\t'.join(str(x) for x in row) + '\n')
    sys.exit(1 if false_rows else 0)


if __name__ == '__main__':
    main()
