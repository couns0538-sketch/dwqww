#!/usr/bin/env python3
"""adjudication_audit.py - what adjudication / book / TC each gate used, how its games ended, and what a draw or
resign adjudication rule WOULD have saved (report only; any change is a crew decision).

usage: python -I -B adjudication_audit.py GATE_DIR [GATE_DIR ...] [--json OUT.json] [--md OUT.md]
       python -I -B adjudication_audit.py --all ROOT [--match TEXT] [--last N] [--json OUT.json] [--md OUT.md]

Per gate (read-only): the settings from config.json (resign / draw / maxmoves / tablebase blocks, opening book file,
format, order, start) and RUN_INFO argv (tc, timemargin, Threads, Hash, concurrency); the game endings from the
log's "Finished game" reasons and the PGN Termination tags; plies per game and engine seconds per game from the
PGN. Then a simulation of fastchess adjudication rules on the PGN move comments (scores are the mover's view,
mate scores count as beyond every threshold, book plies carry no score):
  -draw movenumber=M movecount=C score=S   after full move M, C consecutive plies (either side) with |score| <= S
  -resign movecount=C score=S [twosided]  one side's C consecutive own moves at score <= -S (twosided: the
                                          opponent's last score >= +S as well) -> that side loses
  -maxmoves N                              draw at full move N
For each rule set: games it would have ended early, plies saved (and the share of all plies), engine seconds saved
(sum of the per-move times after the cut, and the share of all engine time), and the DISAGREEMENTS = games whose
adjudicated result differs from the result actually played (the price of the rule). Nothing here changes a gate.
"""
import argparse
import datetime
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as gl  # noqa: E402

RULESETS = {
    'draw34/8/20': {'draw': (34, 8, 20)},
    'draw34/8/10': {'draw': (34, 8, 10)},
    'draw40/16/5': {'draw': (40, 16, 5)},
    'resign3/600': {'resign': (3, 600, False)},
    'resign3/600two': {'resign': (3, 600, True)},
    'resign5/1000two': {'resign': (5, 1000, True)},
    'fishtest-like (resign3/600two + draw34/8/20)': {'resign': (3, 600, True), 'draw': (34, 8, 20)},
    'maxmoves200': {'maxmoves': 200},
}
BIG = 10 ** 6


def ply_scores(plies):
    """[(cp_mover_view or None for book, seconds)] per ply; mate = +/-BIG."""
    out = []
    for san, c in plies:
        if not c or c.get('book'):
            out.append((None, 0.0))
            continue
        if 'mate' in c:
            cp = BIG if c['mate'] > 0 else -BIG
        else:
            cp = c.get('cp')
        out.append((cp, c.get('sec', 0.0) or 0.0))
    return out


def start_of(tags):
    """(first ply is Black's?, full-move number of the first ply) from the FEN tag of an EPD-book game (UHO openings
    start with either side to move); a PGN-book game starts from the initial position."""
    fen = tags.get('FEN')
    if not fen:
        return False, 1
    f = fen.split()
    black = len(f) > 1 and f[1] == 'b'
    try:
        full = int(f[5]) if len(f) > 5 else 1
    except ValueError:
        full = 1
    return black, full


def simulate(plies, rules, tags):
    """(ply index after which the game would stop, adjudicated result, kind) or (None, None, None).
    Side parity and full-move numbers honour the FEN tag (Black-to-move starts of EPD books)."""
    sc = ply_scores(plies)
    n = len(sc)
    best = None
    black_first, full0 = start_of(tags)
    off = 1 if black_first else 0          # ply index i is Black's move when (i + off) is odd

    def full_move(i):
        return full0 + (i + off) // 2

    if 'maxmoves' in rules:
        p = next((i for i in range(n) if full_move(i) >= rules['maxmoves'] and (i + off) % 2 == 1), None)
        if p is not None and p + 1 < n:
            best = (p + 1, '1/2-1/2', 'maxmoves')
    if 'draw' in rules:
        mn, mc, s = rules['draw']
        cnt = 0
        for i, (cp, _) in enumerate(sc):
            if cp is None:
                cnt = 0
                continue
            if abs(cp) <= s:
                cnt += 1
            else:
                cnt = 0
            if cnt >= mc and full_move(i) >= mn and i < n - 1:
                if best is None or i + 1 < best[0]:
                    best = (i + 1, '1/2-1/2', 'draw')
                break
    if 'resign' in rules:
        mc, s, two = rules['resign']
        cnt = [0, 0]
        last = [None, None]
        for i, (cp, _) in enumerate(sc):
            side = (i + off) % 2            # 0 = White's move, 1 = Black's move
            if cp is None:
                cnt[side] = 0
                last[side] = None
                continue
            last[side] = cp
            if cp <= -s and (not two or (last[1 - side] is not None and last[1 - side] >= s)):
                cnt[side] += 1
            else:
                cnt[side] = 0
            if cnt[side] >= mc and i < n - 1:
                res = '0-1' if side == 0 else '1-0'
                if best is None or i + 1 < best[0]:
                    best = (i + 1, res, 'resign')
                break
    if best is None:
        return None, None, None
    return best


def audit_gate(d):
    tag = os.path.basename(os.path.normpath(d))
    pgn, log_p, ri_p, cfg_p, res_p = gl.find_gate_files(d)
    out = {'gate': tag, 'dir': d}
    try:
        info = gl.load_run_info(ri_p)
    except gl.GateError:
        info = {}
    cfg = gl.load_config(cfg_p)
    s = {}
    for k in ('resign', 'draw', 'maxmoves', 'tb_adjudication'):
        v = cfg.get(k)
        if isinstance(v, dict):
            s[k] = {kk: vv for kk, vv in v.items() if kk != 'syzygy_dirs' or vv}
    op = cfg.get('opening') if isinstance(cfg.get('opening'), dict) else {}
    s['opening'] = {'file': os.path.basename(op.get('file', '')), 'format': op.get('format'), 'order': op.get('order'), 'plies': op.get('plies'), 'start': op.get('start')}
    argv = info.get('argv', '') if isinstance(info, dict) else ''
    m = re.search(r'tc=(\S+)', argv)
    s['tc'] = m.group(1) if m else None
    m = re.search(r'timemargin=(\d+)', argv)
    s['timemargin_ms'] = int(m.group(1)) if m else None
    m = re.search(r'option\.Threads=(\d+)', argv)
    s['threads'] = int(m.group(1)) if m else info.get('threads')
    m = re.search(r'option\.Hash=(\d+)', argv)
    s['hash_mb'] = int(m.group(1)) if m else None
    s['concurrency'] = info.get('concurrency') or cfg.get('concurrency')
    b = info.get('book') if isinstance(info.get('book'), dict) else {}
    s['book'] = {'key': b.get('key'), 'file': os.path.basename(b.get('file', '')), 'format': b.get('format'), 'sha256_8': (b.get('sha256') or '')[:8]}
    s['sprt'] = info.get('sprt') if isinstance(info.get('sprt'), str) else None
    s['cap_games'] = info.get('cap_games')
    s['adjudication_in_use'] = any(isinstance(cfg.get(k), dict) and cfg[k].get('enabled') for k in ('resign', 'draw', 'maxmoves', 'tb_adjudication'))
    out['settings'] = s
    reasons = {}
    if log_p:
        try:
            log = gl.parse_log(log_p)
            for f in log['finished']:
                r = f['reason']
                key = ('mate' if 'mates' in r else '3-fold' if '3-fold' in r else 'fifty' if 'fifty' in r else
                       'insufficient' if 'insufficient' in r else 'stalemate' if 'stalemate' in r else
                       'time' if 'time' in r else 'adjudication' if 'adjudicat' in r.lower() else 'other: ' + r[:40])
                reasons[key] = reasons.get(key, 0) + 1
        except (OSError, ValueError):
            pass
    out['endings_log'] = reasons
    if not pgn:
        out['note'] = 'no PGN: endings from the log only, no simulation'
        return out
    try:
        games = gl.parse_pgn_strict(pgn)
    except gl.GateError as e:
        out['error'] = str(e)
        return out
    term = {}
    for g in games:
        t = g['tags'].get('Termination', '?')
        term[t] = term.get(t, 0) + 1
    out['terminations_pgn'] = term
    plies = [len(g['plies']) for g in games]
    secs = [sum((c.get('sec') or 0.0) for _, c in g['plies'] if c and not c.get('book')) for g in games]
    out['games'] = len(games)
    out['plies'] = {'mean': round(statistics.mean(plies), 1), 'median': statistics.median(plies), 'p90': sorted(plies)[int(0.9 * len(plies))], 'max': max(plies), 'total': sum(plies)}
    out['engine_s'] = {'mean': round(statistics.mean(secs), 1), 'total_h': round(sum(secs) / 3600.0, 2)}
    book_plies = [sum(1 for _, c in g['plies'] if c and c.get('book')) for g in games]
    out['book_plies_mean'] = round(statistics.mean(book_plies), 1)
    sims = {}
    for name, rules in RULESETS.items():
        n_adj = plies_saved = 0
        sec_saved = 0.0
        kinds = {}
        disagree = []
        for gi, g in enumerate(games):
            cut, res, kind = simulate(g['plies'], rules, g['tags'])
            if cut is None:
                continue
            n_adj += 1
            kinds[kind] = kinds.get(kind, 0) + 1
            plies_saved += len(g['plies']) - cut
            sec_saved += sum((c.get('sec') or 0.0) for _, c in g['plies'][cut:] if c and not c.get('book'))
            if res != g['tags']['Result']:
                disagree.append({'game_index': gi + 1, 'round': g['tags']['Round'], 'adjudicated': res, 'played': g['tags']['Result'], 'at_ply': cut, 'kind': kind})
        sims[name] = {'games_adjudicated': n_adj, 'share_of_games': round(n_adj / len(games), 3), 'by_kind': kinds,
                      'plies_saved': plies_saved, 'share_of_plies': round(plies_saved / sum(plies), 3),
                      'engine_s_saved': round(sec_saved, 1), 'share_of_engine_s': round(sec_saved / max(sum(secs), 1e-9), 3),
                      'disagreements': len(disagree), 'disagreement_examples': disagree[:5]}
    out['simulation'] = sims
    return out


def md_rows(results):
    L = ['| gate | games | book (format, order, start) | TC / margin | threads / hash / conc | adjudication in config | endings (log) | plies mean / median / p90 / max | engine s per game |',
         '|---|---|---|---|---|---|---|---|---|']
    for o in results:
        s = o.get('settings', {})
        op = s.get('opening', {})
        adj = 'none' if not s.get('adjudication_in_use') else ', '.join(k for k in ('resign', 'draw', 'maxmoves', 'tb_adjudication') if s.get(k, {}).get('enabled'))
        p = o.get('plies', {})
        L.append(f"| {o['gate']} | {o.get('games', '')} | {op.get('file')} (fmt {op.get('format')}, order {op.get('order')}, start {op.get('start')}) | {s.get('tc')} / {s.get('timemargin_ms')} ms | "
                 f"{s.get('threads')} / {s.get('hash_mb')} / {s.get('concurrency')} | {adj} | {o.get('endings_log')} | "
                 f"{p.get('mean')} / {p.get('median')} / {p.get('p90')} / {p.get('max')} | {o.get('engine_s', {}).get('mean')} |")
    L.append('')
    L.append('| gate | rule set | games ended early | plies saved (share) | engine s saved (share) | disagreements (adjudicated result != played) |')
    L.append('|---|---|---|---|---|---|')
    for o in results:
        for name, sm in (o.get('simulation') or {}).items():
            L.append(f"| {o['gate']} | {name} | {sm['games_adjudicated']} ({sm['share_of_games'] * 100:.1f} %) {sm['by_kind']} | {sm['plies_saved']} ({sm['share_of_plies'] * 100:.1f} %) | "
                     f"{sm['engine_s_saved']} ({sm['share_of_engine_s'] * 100:.1f} %) | {sm['disagreements']} |")
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('gates', nargs='*')
    ap.add_argument('--all')
    ap.add_argument('--match', default='')
    ap.add_argument('--last', type=int, default=0)
    ap.add_argument('--json')
    ap.add_argument('--md')
    a = ap.parse_args()
    for p in (a.json, a.md):
        if p and os.path.exists(p):
            print(f'adjudication_audit: {p} exists (never overwritten)', file=sys.stderr)
            return 2
    dirs = list(a.gates)
    if a.all:
        dirs += sorted(os.path.join(a.all, n) for n in os.listdir(a.all) if os.path.isdir(os.path.join(a.all, n)) and a.match in n)
    if a.last:
        dirs = dirs[-a.last:]
    if not dirs:
        ap.print_usage()
        return 2
    results = []
    for d in dirs:
        try:
            o = audit_gate(d)
        except (OSError, ValueError) as e:
            o = {'gate': os.path.basename(d), 'error': str(e)}
        results.append(o)
        print(json.dumps({k: v for k, v in o.items() if k != 'simulation'}, default=str)[:600])
        for name, sm in (o.get('simulation') or {}).items():
            print(f"  {name:<45} early {sm['games_adjudicated']:5d} ({sm['share_of_games'] * 100:4.1f} %)  plies saved {sm['plies_saved']:7d} ({sm['share_of_plies'] * 100:4.1f} %)  "
                  f"engine s saved {sm['engine_s_saved']:8.1f} ({sm['share_of_engine_s'] * 100:4.1f} %)  disagreements {sm['disagreements']}")
    rows = md_rows(results)
    if a.md:
        with open(a.md, 'w', newline='\n', encoding='utf-8') as f:
            f.write('\n'.join(rows) + '\n')
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump({'generated_pc_clock': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'rulesets': {k: str(v) for k, v in RULESETS.items()}, 'gates': results}, f, indent=1, default=str)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
