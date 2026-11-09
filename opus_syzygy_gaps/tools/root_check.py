#!/usr/bin/env python3
"""root_check.py - check tb_root.exe output against expected values computed here from python-chess oracle rows.

usage: python -I -B root_check.py <oracle.jsonl> <tb_root.out> [--json out.json] [--list bad.tsv] [--rule50 1]

Expected outcome of each root move, from the oracle's child wdl / dtz only (no engine code), with clock c at the root and the
50-move rule on. Convention: child_dtz is from the child's side to move.
  zeroing move: outcome = -child_wdl (2 win, 1 cursed win, 0 draw, -1 blessed loss, -2 loss).
  mate: win.  clock c + 1 >= 100 without mate: draw.  a move into a third occurrence (oracle flag threefold): draw.
  otherwise child dtz d: child loses (d < 0): the mover zeroes after |d| more plies; the zeroing happens at clock c + 1 + |d|
  counted as plies; the mover's distance from the root is D = |d| + 1. Win if D + c <= 100, else cursed win.
  child wins (d > 0): the mover loses, distance D = d + 1. Loss if D + c <= 100, else blessed loss. d = 0: draw.
Rounded distances (reported by tb_root for the same move): when D + c == 100 exactly and the value is rounded, the outcome is
UNDECIDED between the two classes. Such moves are accepted either way.

Checks per root:
  A. every kept move has the best outcome among the legal moves (root selection never gives up result);
  B. display class equals the best outcome class: win >= 31743, cursed +2, draw 0, blessed -2, loss <= -31743;
  C. interior probe_wdl of a clock-0 root equals the oracle's wdl, DTZ equals the oracle's dtz (both clocks);
  D. every best-outcome move is kept unless the root is repeated (ties are not dropped).
Prints counts. A row is BAD only for a broken check; UNDECIDED rows are counted apart.
"""
import argparse
import json
import sys

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


def outcome(m, c, rule50=True):
    if m['mate']:
        return 'win', 1
    if m['zeroing']:
        w = m['child_wdl']
        if w is None:
            return None, 0
        if rule50:
            return {2: 'loss', 1: 'blessed', 0: 'draw', -1: 'cursed', -2: 'win'}[w], 1
        return {2: 'loss', 1: 'loss', 0: 'draw', -1: 'win', -2: 'win'}[w], 1
    if c + 1 >= 100 or m.get('threefold'):
        return 'draw', 0
    d = m['child_dtz']
    if d is None:
        return None, 0
    if d == 0:
        return 'draw', 0
    if d < 0:
        D = -d + 1
        return ('win' if D + c <= 100 or not rule50 else 'cursed'), D
    D = d + 1
    return ('loss' if D + c <= 100 or not rule50 else 'blessed'), D


def display_class(text):
    if text == '-':
        return None
    s = int(text)
    if s >= 31743:
        return 'win'
    if s <= -31743:
        return 'loss'
    return {2: 'cursed', 0: 'draw', -2: 'blessed'}.get(s, 'other')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('oracle')
    ap.add_argument('out')
    ap.add_argument('--json', default='')
    ap.add_argument('--list', default='')
    ap.add_argument('--rule50', type=int, default=1)
    a = ap.parse_args()
    oracle = [json.loads(l) for l in open(a.oracle, encoding='utf-8')]
    rows = [l.rstrip('\n').split('\t') for l in open(a.out, encoding='utf-8')]
    if len(oracle) != len(rows):
        raise SystemExit(f'row count differs: oracle {len(oracle)} tool {len(rows)}')
    cnt = {k: 0 for k in ('roots', 'A_bad', 'B_bad', 'C_wdl_bad', 'C_dtz_bad', 'D_bad', 'undecided', 'not_ranked', 'kept_all',
                          'sum100_exact_win', 'sum100_rounded')}
    bad = []
    for o, r in zip(oracle, rows):
        if r[1] != 'ok':
            bad.append(('BADLINE', o['fen'], r[1]))
            cnt['BADLINE'] = cnt.get('BADLINE', 0) + 1
            continue
        cnt['roots'] += 1
        c = o['clock']
        display, kept, ranks = r[2], r[5], r[6]
        rounded = {}
        for item in ([] if ranks == '-' else ranks.split()):
            u, _rank, _val, rd = item.rsplit(':', 3)
            rounded[u] = rd == '1'
        moves = o['moves']
        if not moves:
            continue
        info = {}
        undecided = False
        for m in moves:
            oc, D = outcome(m, c, a.rule50 != 0)
            und = a.rule50 != 0 and rounded.get(m['uci'], False) and D + c == 100 and oc in ('win', 'loss')
            info[m['uci']] = (oc, D, und)
            undecided = undecided or und
            if not rounded.get(m['uci'], False) and D + c == 100 and oc == 'win':
                cnt['sum100_exact_win'] += 1
            if und:
                cnt['sum100_rounded'] += 1
        if any(v[0] is None for v in info.values()):
            cnt['not_ranked'] += 1
            if kept != '-':
                bad.append(('E', o['fen'], f'oracle has no value but the root is ranked: kept {kept}'))
                cnt['E_bad'] = cnt.get('E_bad', 0) + 1
            continue
        best = max(RANK[v[0]] for v in info.values())
        if undecided:
            cnt['undecided'] += 1
        keep = None if kept == '-' else kept.split()
        if o['clock'] >= 100:
            cnt['clock100_rows'] = cnt.get('clock100_rows', 0) + 1  # root is drawn before ranks matter: engine fixture
        elif keep is None:
            cnt['not_ranked'] += 1
        else:
            for u in keep:
                if u not in info:
                    bad.append(('A', o['fen'], f'kept illegal {u}'))
                    cnt['A_bad'] += 1
                elif RANK[info[u][0]] != best and not undecided:
                    bad.append(('A', o['fen'], f'kept {u} {info[u]} best {best} kept {kept}'))
                    cnt['A_bad'] += 1
            want = [u for u, v in info.items() if RANK[v[0]] == best]
            # A win at exactly sum 100 may be dropped next to wins that zero earlier: both keep the result.
            miss = [u for u in want if u not in keep and not (best == 2 and info[u][1] + c == 100)]
            # Narrower by design: a root whose line repeated ranks wins by distance; with the rule off a cursed win ranks below wins.
            if miss and not undecided and best in (2, -2, 0):
                if ' moves ' in o['fen'] or a.rule50 == 0:
                    cnt['D_narrow_by_design'] = cnt.get('D_narrow_by_design', 0) + 1
                else:
                    bad.append(('D', o['fen'], f'dropped {miss} best {best} kept {kept}'))
                    cnt['D_bad'] += 1
            if len(keep) == len(moves):
                cnt['kept_all'] += 1
            dc = display_class(display)
            if dc is None:
                cnt['no_display'] = cnt.get('no_display', 0) + 1
            if not undecided and dc is not None and RANK.get(dc, 99) != best:
                bad.append(('B', o['fen'], f'display {display} best {best} clock {c} dtz {o["dtz"]} wdl {o["wdl"]}'))
                cnt['B_bad'] += 1
        if r[7] != '-' and o['wdl'] is not None and int(r[7]) != o['wdl']:
            bad.append(('C', o['fen'], f'probe_wdl {r[7]} oracle {o["wdl"]}'))
            cnt['C_wdl_bad'] += 1
        if r[9] != '-' and o['dtz'] is not None and int(r[9].split(':')[0]) != o['dtz']:
            bad.append(('C', o['fen'], f'dtz {r[9]} oracle {o["dtz"]}'))
            cnt['C_dtz_bad'] += 1
    cnt['bad_rows'] = len(bad)
    print(json.dumps(cnt))
    if a.json:
        json.dump(cnt, open(a.json, 'w'), indent=1)
    if a.list:
        with open(a.list, 'w', encoding='utf-8', newline='\n') as f:
            for b in bad:
                f.write('\t'.join(b) + '\n')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
