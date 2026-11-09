#!/usr/bin/env python3
"""exact_check.py - judge the root path and the engine against oracle_exact.py rows. Exit 1 on any broken check.

usage: python -I -B exact_check.py <exact.jsonl> [--root tb_root.out] [--run uci_run.jsonl] [--json out.json] [--list bad.tsv]
--root (tb_root.exe output, same order as the oracle rows):
  A: every kept move has the best class among the legal moves;
  B: the displayed class equals the best class (win >= 31743, cursed +2, draw 0, blessed -2, loss <= -31743); `-` is counted as no_display and judged
     as wrong when a DTZ-ranked root (used_dtz = 1) has no display;
  D: on clock-0-free rows, every best-class move is kept unless the line repeated, or the dropped move is an equal class at a higher distance (counted);
--run (uci_tb.py rows): M: the chosen move has the best class. S: the reported score class equals the best class; a mate is accepted for win or loss.
Roots with an unresolved move (solver budget) are counted apart and not judged. Roots with a third occurrence already on the board are draws for
the engine: score 0 expected, the move is not judged.
"""
import argparse
import json
import sys

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


def display_class(text):
    s = int(text)
    if s >= 31743:
        return 'win'
    if s <= -31743:
        return 'loss'
    return {2: 'cursed', 0: 'draw', -2: 'blessed'}.get(s, 'other')


def score_class(r):
    if r.get('score') is None:
        return None
    if r['score_type'] == 'mate':
        return 'win' if r['score'] > 0 else 'loss'
    return display_class(str(r['score']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracle')
    ap.add_argument('--root', default='')
    ap.add_argument('--run', default='')
    ap.add_argument('--json', default='')
    ap.add_argument('--list', default='')
    ap.add_argument('--wdl-only', action='store_true', help='WDL tables only: the move filter cannot see the clock, a worse kept move is counted as a known limit')
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.oracle, encoding='utf-8')]
    cnt = {'rows': len(rows), 'unresolved': 0, 'no_moves': 0, 'castling': 0, 'root_threefold': 0, 'clock100': 0}
    bad = []
    if a.root:
        cnt.update({'roots_judged': 0, 'A_bad': 0, 'B_bad': 0, 'D_dropped_best': 0, 'no_display': 0, 'not_ranked': 0})
        lines = [l.rstrip('\n').split('\t') for l in open(a.root, encoding='utf-8')]
        # The oracle may be a prefix of the FEN list the tool ran on (solver still running): extra tool rows are ignored, fewer are an error.
        if len(lines) < len(rows):
            sys.exit(f'row count differs: oracle {len(rows)} tool {len(lines)}')
        cnt['tool_rows'] = len(lines)
        for o, r in zip(rows, lines):
            if r[1] != 'ok':
                bad.append(('BADLINE', o['fen'], r[1]))
                continue
            if o.get('castling'):
                cnt['castling'] += 1
                if r[5] != '-':
                    bad.append(('E', o['fen'], f'castling root was ranked: kept {r[5]}'))
                continue
            if not o['moves']:
                cnt['no_moves'] += 1
                continue
            if o['unresolved']:
                cnt['unresolved'] += 1
                continue
            if o['clock'] >= 100:
                cnt['clock100'] += 1
                continue
            if o.get('root_threefold'):
                cnt['root_threefold'] += 1
                continue
            cnt['roots_judged'] += 1
            best = o['best']
            display, used_dtz, kept = r[2], r[4], r[5]
            if kept == '-':
                cnt['not_ranked'] += 1
                bad.append(('E', o['fen'], 'not ranked'))
                continue
            ranks = {}
            for item in ([] if r[6] == '-' else r[6].split()):
                u, rk, _v, _x = item.rsplit(':', 3)
                ranks[u] = int(rk)
            for u in kept.split():
                if u not in o['moves']:
                    bad.append(('A', o['fen'], f'kept illegal {u}'))
                    cnt['A_bad'] += 1
                elif RANK[o['moves'][u]] != best and a.wdl_only:
                    cnt['A_wdl_limit'] = cnt.get('A_wdl_limit', 0) + 1
                elif RANK[o['moves'][u]] != best and ranks.get(u) in (900, -900):
                    # the walk's budget ran out: not proved either way, a known limit, counted and listed apart
                    cnt['A_undecided_worse'] = cnt.get('A_undecided_worse', 0) + 1
                elif RANK[o['moves'][u]] != best:
                    bad.append(('A', o['fen'], f'kept {u} {o["moves"][u]} best {best} clock {o["clock"]} dtz {o["dtz"]} kept {kept}'))
                    cnt['A_bad'] += 1
            if not any(RANK[o['moves'][u]] == best for u in kept.split() if u in o['moves']):
                bad.append(('A2', o['fen'], f'no best move kept, best {best} kept {kept}'))
                cnt['A2_no_best_kept'] = cnt.get('A2_no_best_kept', 0) + 1
            cnt['D_dropped_best'] += sum(RANK[v] == best and u not in kept.split() for u, v in o['moves'].items())
            if display == '-':
                cnt['no_display'] += 1
                if used_dtz == '1' and not any(ranks.get(u) in (900, -900) for u in kept.split()):
                    bad.append(('B', o['fen'], 'DTZ-ranked root without display'))
                    cnt['B_bad'] += 1
            elif RANK.get(display_class(display), 99) != best:
                bad.append(('B', o['fen'], f'display {display} best {best} clock {o["clock"]} dtz {o["dtz"]} wdl {o["wdl"]}'))
                cnt['B_bad'] += 1
    if a.run:
        cnt.update({'run_roots': 0, 'M_bad': 0, 'S_bad': 0})
        by_fen = {o['fen']: o for o in rows}
        for line in open(a.run, encoding='utf-8'):
            r = json.loads(line)
            o = by_fen.get(r['fen'])
            if o is None or not o['moves'] or o.get('castling'):
                continue
            if r['bestmove'] not in o['moves']:
                bad.append(('L', r['fen'], f'illegal bestmove {r["bestmove"]}'))
                cnt['L_bad'] = cnt.get('L_bad', 0) + 1
                continue
            if o['clock'] >= 100 or o.get('root_threefold'):
                if r.get('score') != 0:
                    bad.append(('S', r['fen'], f'drawn root: score {r.get("score")}'))
                    cnt['S_bad'] += 1
                continue
            if o['unresolved']:
                continue
            cnt['run_roots'] += 1
            best = o['best']
            if RANK[o['moves'][r['bestmove']]] != best:
                bad.append(('M', r['fen'], f'chose {r["bestmove"]} {o["moves"][r["bestmove"]]} best {best} clock {o["clock"]} score {r.get("score")}'))
                cnt['M_bad'] += 1
            sc = score_class(r)
            if sc is None or RANK.get(sc, 99) != best:
                bad.append(('S', r['fen'], f'score {r.get("score_type")} {r.get("score")} best {best} clock {o["clock"]} dtz {o["dtz"]}'))
                cnt['S_bad'] += 1
    print(json.dumps(cnt))
    if a.json:
        json.dump(cnt, open(a.json, 'w'), indent=1)
    if a.list:
        with open(a.list, 'w', encoding='utf-8', newline='\n') as f:
            for b in bad:
                f.write('\t'.join(b) + '\n')
    broken = sum(1 for b in bad)
    sys.exit(1 if broken else 0)


if __name__ == '__main__':
    main()
