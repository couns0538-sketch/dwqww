#!/usr/bin/env python3
"""exact_partial.py <exact.jsonl> --root tb_root.out [--run uci_run.jsonl] [--list bad.tsv] - what can still be proved on the rows exact_check.py skips: roots where the solver left some moves unresolved.

The moves it did resolve are facts. known = best class among resolved moves is a lower bound of the root's true class. Roots the walk left undecided (no display) are counted apart: only a false claim counts there.
  P1: a kept move, resolved, ranked as decided (not 900 / -900), of a class below known: the move filter kept a provably worse move.
  P2: a shown class below known: the root report is provably too low.
  P3: all kept moves resolved and the shown class differs from the best of them: the report does not match the moves kept.
  P4: a kept move ranked 901 or 2000 (a claimed win) that the solver resolved as no win; or ranked -2000 (a claimed loss) that it resolved as no loss.
  M: the engine's move, resolved, of a class below known, on a decided root. S: the engine's score class below known, on a decided root. MU, SU: the same on undecided roots (the documented limit, not an error).
Exit 1 on any P or M or S. Standard library only.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact_check import RANK, display_class, score_class  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracle')
    ap.add_argument('--root', required=True)
    ap.add_argument('--run', default='')
    ap.add_argument('--list', default='')
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.oracle, encoding='utf-8')]
    lines = [l.rstrip('\n').split('\t') for l in open(a.root, encoding='utf-8')]
    if len(lines) < len(rows):
        sys.exit(f'row count differs: oracle {len(rows)} tool {len(lines)}')
    cnt = {'rows_with_unresolved': 0, 'decided': 0, 'undecided': 0, 'skipped': 0, 'kept_resolved': 0, 'kept_unresolved': 0, 'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
    bad = []
    info = {}
    for o, r in zip(rows, lines):
        if not o['unresolved']:
            continue
        cnt['rows_with_unresolved'] += 1
        known_moves = {u: c for u, c in o['moves'].items() if c is not None}
        if r[1] != 'ok' or o.get('castling') or o['clock'] >= 100 or o.get('root_threefold') or not known_moves:
            cnt['skipped'] += 1
            continue
        known = max(RANK[c] for c in known_moves.values())
        display, kept = r[2], ([] if r[5] == '-' else r[5].split())
        ranks = {}
        for item in ([] if r[6] == '-' else r[6].split()):
            u, rk, _v, _x = item.rsplit(':', 3)
            ranks[u] = int(rk)
        undecided = display == '-'
        cnt['undecided' if undecided else 'decided'] += 1
        info[o['fen']] = (known, undecided, known_moves)
        for u in kept:
            c = known_moves.get(u)
            if c is None:
                cnt['kept_unresolved'] += 1
                continue
            cnt['kept_resolved'] += 1
            rank = ranks.get(u)
            if RANK[c] < known and rank not in (900, -900):
                cnt['P1'] += 1
                bad.append(('P1', o['fen'], f'kept {u} {c} rank {rank}, known class {known}'))
            if rank is not None and rank >= 901 and RANK[c] != 2:
                cnt['P4'] += 1
                bad.append(('P4', o['fen'], f'{u} rank {rank} claims a win, solver says {c}'))
            if rank == -2000 and RANK[c] != -2:
                cnt['P4'] += 1
                bad.append(('P4', o['fen'], f'{u} rank -2000 claims a loss, solver says {c}'))
        if not undecided:
            shown = RANK.get(display_class(display), 99)
            if shown < known:
                cnt['P2'] += 1
                bad.append(('P2', o['fen'], f'display {display} below known class {known}'))
            if kept and all(u in known_moves for u in kept) and shown != max(RANK[known_moves[u]] for u in kept):
                cnt['P3'] += 1
                bad.append(('P3', o['fen'], f'display {display} kept {" ".join(kept)} classes {[known_moves[u] for u in kept]}'))
    if a.run:
        cnt.update({'run_roots': 0, 'M': 0, 'S': 0, 'MU': 0, 'SU': 0, 'move_unresolved': 0})
        for line in open(a.run, encoding='utf-8'):
            r = json.loads(line)
            x = info.get(r['fen'])
            if x is None:
                continue
            known, undecided, known_moves = x
            cnt['run_roots'] += 1
            c = known_moves.get(r['bestmove'])
            if c is None:
                cnt['move_unresolved'] += 1
            elif RANK[c] < known:
                cnt['MU' if undecided else 'M'] += 1
                if not undecided:
                    bad.append(('M', r['fen'], f'played {r["bestmove"]} {c}, known class {known}'))
            # an ordinary score ('other') on a root the report decided counts too, as in exact_check.py
            sc = score_class(r)
            s = RANK.get(sc, -3)
            if sc is None or s < known:
                cnt['SU' if undecided else 'S'] += 1
                if not undecided:
                    bad.append(('S', r['fen'], f'score {r.get("score_type")} {r.get("score")}, known class {known}'))
    print(json.dumps(cnt))
    if a.list:
        with open(a.list, 'w', encoding='utf-8', newline='\n') as f:
            for b in bad:
                f.write('\t'.join(b) + '\n')
    for b in bad[:6]:
        print('\t'.join(b)[:170])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
