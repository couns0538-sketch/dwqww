#!/usr/bin/env python3
"""forge_sol_S38_gate_time_audit_20261027.py: gate speed / time-loss / time-use audit (S38, opus 2026-10-27).

Reads, read-only, a fastchess PGN (-pgnout ... timeleft=true), optionally the fastchess stdout log (<tag>.log, what
the PC driver redirects) and one or more fastchess `-log engine=true` files (engine_io.log / .head.log / .tail.log).
Per engine it reports:
  * time used per move (PGN comment) against the engine's own allotment: the soft/hard limits recomputed from the
    clock before the move with the AL1 lock time manager (--tm, src/search.cpp: soft = avail/22 + 75% inc,
    hard = min(60% avail, 5 x soft), avail = remaining - 10 ms overhead); p50/p95/p99/max of used and used/soft;
    share of moves over the increment; moves over the hard limit; lowest clock;
  * median search depth (PGN) and median nps (engine log: last `info ... nps` line of each search with
    time >= --nps-min-ms) by game phase (ply bands --phase-plies);
  * TL / illegal / crash counts from the PGN, cross-checked against fastchess's own per-game lines in <tag>.log
    (the `Finished game ... {... loses on time}` lines that GATE_RESULTS.csv counts).
Flags: nps asymmetry > --asym (3%) between the two engines; p99 of used/soft > --p99-x (1.5) x the same role in a
reference gate (--ref = an earlier JSON of this tool); PGN-vs-log count mismatches.
Writes only --out-json / --out-md; refuses any output under a PC gate/queue/lock/training root or onto an input.
Stdlib only; deterministic (same inputs and options -> byte-identical outputs).
Exit: 0 clean, 1 flags raised, 3 PGN-vs-log cross-check mismatch, 2 usage error / refused path.
"""
import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys

VERSION = 'S38 gate_time_audit 2026-10-27 v1'
DENY_ROOTS = (r'C:\Users\Administrator\grok-pc', r'D:\grok-pc-data\forge_push', r'F:\forge_nnue_train', r'F:\forge_out')

HDR = re.compile(r'^\[(\w+)\s+"(.*)"\]\s*$')
TOKEN = re.compile(r'\{[^}]*\}|\$\d+|\d+\.(?:\.\.)?|1-0|0-1|1/2-1/2|\*|[^\s{}()]+')
MOVENUM = re.compile(r'^\d+\.(?:\.\.)?$')
CMT_HEAD = re.compile(r'^(?P<ev>[+-]?(?:M\d+|\d+(?:\.\d+)?))/(?P<d>\d+)\s+(?P<t>\d+(?:\.\d+)?)s$')
CMT_KV = re.compile(r'^(\w+)=(-?\d+(?:\.\d+)?)(s|ms)?$')
ELINE = re.compile(r'^\[Engine\] \[[\d:.]+\] <\s*(\d+)>\s+(\S+) (<---|--->) (.*?)\s*$')
I_DEPTH = re.compile(r'\bdepth (\d+)')
I_NODES = re.compile(r'\bnodes (\d+)')
I_NPS = re.compile(r'\bnps (\d+)')
I_TIME = re.compile(r'\btime (\d+)')
FIN = re.compile(r'^Finished game (\d+) \((\S+) vs (\S+)\): (\S+) \{(.*)\}\s*$')
RES = re.compile(r'Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)')
EV_TL = re.compile(r'loses on time', re.I)
EV_ILLEGAL = re.compile(r'illegal move', re.I)
EV_CRASH = re.compile(r'disconnects|connection stalls|crash', re.I)
AP_CRASH = re.compile(r'(?i)(disconnect|stalls|crash|illegal|abandon)')   # autopromote.ps1 Log-TLCrash, for comparison only


class Refused(Exception):
    pass


def norm(p):
    return os.path.normcase(os.path.abspath(p))


def under(path, root):
    p, r = norm(path), norm(root)
    return p == r or p.startswith(r.rstrip('\\/') + os.sep)


def file_meta(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return {'name': os.path.basename(path), 'bytes': os.path.getsize(path), 'sha256': h.hexdigest()}


def pct(sorted_vals, p):
    """nearest-rank percentile of an ascending list"""
    if not sorted_vals:
        return None
    return sorted_vals[max(1, math.ceil(p / 100.0 * len(sorted_vals))) - 1]


def med(vals):
    return round(float(statistics.median(vals)), 1) if vals else None


def dist(vals, nd=3):
    s = sorted(vals)
    if not s:
        return {'n': 0}
    return {'n': len(s), 'p50': round(pct(s, 50), nd), 'p95': round(pct(s, 95), nd), 'p99': round(pct(s, 99), nd),
            'max': round(s[-1], nd)}


class TimeModel:
    """AL1 lock time manager (src/search.cpp, no movestogo): integer ms like the engine."""

    def __init__(self, soft_div=22, inc_pct=75, hard_pct=60, hard_mult=5, overhead=10):
        self.soft_div, self.inc_pct, self.hard_pct, self.hard_mult, self.overhead = soft_div, inc_pct, hard_pct, hard_mult, overhead

    def limits(self, remaining_ms, inc_ms):
        available = max(1, remaining_ms - self.overhead)
        soft = available // self.soft_div + max(0, inc_ms) * self.inc_pct // 100
        hard = min(available * self.hard_pct // 100, soft * self.hard_mult)
        return max(1, min(soft, available)), max(1, min(hard, available))

    def as_dict(self):
        return {'soft_div': self.soft_div, 'inc_pct': self.inc_pct, 'hard_pct': self.hard_pct,
                'hard_mult': self.hard_mult, 'overhead_ms': self.overhead}


def parse_tc(tc):
    m = re.match(r'^(\d+(?:\.\d+)?)\+(\d+(?:\.\d+)?)$', tc.strip())
    if not m:
        return None, None
    return int(round(float(m.group(1)) * 1000)), int(round(float(m.group(2)) * 1000))


def parse_comment(c):
    if c is None:
        return {'kind': 'none'}
    c = ' '.join(c.split())
    if c == 'book':
        return {'kind': 'book'}
    parts = [p.strip() for p in c.split(',')]
    m = CMT_HEAD.match(parts[0])
    if not m:
        return {'kind': 'other', 'reason': c}
    d = {'kind': 'engine', 'depth': int(m.group('d')), 'used_ms': int(round(float(m.group('t')) * 1000))}
    reasons = []
    for p in parts[1:]:
        kv = CMT_KV.match(p)
        if kv and kv.group(1) == 'tl':
            v = float(kv.group(2))
            d['tl_ms'] = int(round(v)) if kv.group(3) == 'ms' else int(round(v * 1000))
        elif kv:
            continue
        else:
            reasons.append(p)
    if reasons:
        d['reason'] = ', '.join(reasons)
    return d


def phase_of(ply, bands):
    if ply is None:
        return 'unknown'
    for i, b in enumerate(bands):
        if ply < b:
            return f'P{i}_ply<{b}' if i == 0 else f'P{i}_ply{bands[i - 1]}-{b - 1}'
    return f'P{len(bands)}_ply>={bands[-1]}'


def iter_pgn(path):
    hdr, mv = {}, []
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            m = HDR.match(line)
            if m:
                if m.group(1) == 'Event' and (hdr or mv):
                    yield hdr, ' '.join(mv)
                    hdr, mv = {}, []
                hdr[m.group(1)] = m.group(2)
            elif line:
                mv.append(line)
    if hdr or mv:
        yield hdr, ' '.join(mv)


def parse_game(hdr, text):
    ply0, fen = 0, hdr.get('FEN')
    if fen:
        f = fen.split()
        if len(f) >= 6:
            ply0 = (int(f[5]) - 1) * 2 + (1 if f[1] == 'b' else 0)
    moves, ply = [], ply0
    for tok in TOKEN.findall(text):
        if tok.startswith('{'):
            if moves and 'c' not in moves[-1]:
                moves[-1]['c'] = tok[1:-1]
            continue
        if tok in ('1-0', '0-1', '1/2-1/2', '*') or tok.startswith('$') or MOVENUM.match(tok):
            continue
        moves.append({'ply': ply, 'color': 'w' if ply % 2 == 0 else 'b'})
        ply += 1
    for mvd in moves:
        mvd.update(parse_comment(mvd.pop('c', None)))
    return moves


def classify(term, reasons):
    txt = ' | '.join(reasons)
    t = term.strip().lower()
    if t == 'time forfeit' or EV_TL.search(txt):
        return 'tl'
    if t == 'illegal move' or EV_ILLEGAL.search(txt):
        return 'illegal'
    if t in ('abandoned', 'stalled connection', 'stalled', 'disconnect') or EV_CRASH.search(txt):
        return 'crash'
    return None


def loser_side(reasons, result):
    for r in reasons:
        m = re.match(r'^(White|Black)\b', r)
        if m:
            return 'w' if m.group(1) == 'White' else 'b'
    return {'1-0': 'b', '0-1': 'w'}.get(result)


def new_eng():
    return {'moves': 0, 'book': 0, 'unparsed': 0, 'depth': [], 'depth_phase': {}, 'used': [], 'ratio': [], 'over_inc': 0,
            'over_hard': 0, 'over_hard_ms': [], 'min_tl': None, 'acct_bad': 0, 'acct_n': 0,
            'events': {'tl': 0, 'illegal': 0, 'crash': 0}, 'nps': [], 'nps_phase': {}, 'nodes': 0, 'ntime': 0,
            'searches': 0, 'short': 0}


def audit_pgn(path, tm, bands, engines):
    games, terms, tcs, starts_unknown = 0, {}, {}, 0
    for hdr, text in iter_pgn(path):
        if not hdr:
            continue
        games += 1
        terms[hdr.get('Termination', '?')] = terms.get(hdr.get('Termination', '?'), 0) + 1
        tc = hdr.get('TimeControl', '?')
        tcs[tc] = tcs.get(tc, 0) + 1
        base_ms, inc_ms = parse_tc(tc)
        names = {'w': hdr.get('White', '?'), 'b': hdr.get('Black', '?')}
        for nm in names.values():
            engines.setdefault(nm, new_eng())
        moves = parse_game(hdr, text)
        last_tl = {'w': None, 'b': None}
        reasons = []
        for mv in moves:
            e = engines[names[mv['color']]]
            if mv.get('reason'):
                reasons.append(mv['reason'])
            if mv['kind'] == 'book':
                e['book'] += 1
                continue
            if mv['kind'] != 'engine':
                e['unparsed'] += 1
                continue
            e['moves'] += 1
            ph = phase_of(mv['ply'], bands)
            e['depth'].append(mv['depth'])
            e['depth_phase'].setdefault(ph, []).append(mv['depth'])
            used = mv['used_ms']
            e['used'].append(used)
            if inc_ms is not None and used > inc_ms:
                e['over_inc'] += 1
            rem = last_tl[mv['color']] if last_tl[mv['color']] is not None else (base_ms + inc_ms if base_ms is not None else None)
            if rem is None:
                starts_unknown += 1
            else:
                soft, hard = tm.limits(rem, inc_ms)
                e['ratio'].append(used / soft)
                if used > hard:
                    e['over_hard'] += 1
                    e['over_hard_ms'].append(used - hard)
                if 'tl_ms' in mv:
                    e['acct_n'] += 1
                    if abs(mv['tl_ms'] - (rem - used + inc_ms)) > 2:
                        e['acct_bad'] += 1
            if 'tl_ms' in mv:
                last_tl[mv['color']] = mv['tl_ms']
                e['min_tl'] = mv['tl_ms'] if e['min_tl'] is None else min(e['min_tl'], mv['tl_ms'])
        ev = classify(hdr.get('Termination', ''), reasons)
        if ev:
            side = loser_side(reasons, hdr.get('Result', '*'))
            if side:
                engines[names[side]]['events'][ev] += 1
    return {'games': games, 'terminations': dict(sorted(terms.items())), 'time_controls': dict(sorted(tcs.items())),
            'moves_without_clock_start': starts_unknown}


def ply_of_position(cmd):
    t = cmd.split()
    if len(t) >= 2 and t[1] == 'startpos':
        base, rest = 0, t[2:]
    elif len(t) >= 8 and t[1] == 'fen':
        try:
            base = (int(t[7]) - 1) * 2 + (1 if t[3] == 'b' else 0)
        except ValueError:
            return None
        rest = t[8:]
    else:
        return None
    return base + (len(rest) - 1 if rest and rest[0] == 'moves' else 0)


def audit_engine_logs(paths, bands, min_ms, engines, per_game_n):
    stats = {'lines': 0, 'unmatched_lines': 0, 'searches': 0}
    games_order, games = {}, {}
    for fi, path in enumerate(paths):
        state = {}
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                stats['lines'] += 1
                m = ELINE.match(line)
                if not m:
                    stats['unmatched_lines'] += 1
                    continue
                slot, name, arrow, rest = m.groups()
                st = state.setdefault((slot, name), {'ply': None, 'game': None, 'go': False, 'last': None, 'n': 0})
                if arrow == '<---':
                    if rest == 'ucinewgame':
                        st['n'] += 1
                        st['game'] = f'{fi}:{slot}:{st["n"]}'
                        games_order.setdefault(name, []).append(st['game'])
                        st['ply'], st['go'], st['last'] = None, False, None
                    elif rest.startswith('position '):
                        st['ply'] = ply_of_position(rest)
                    elif rest.startswith('go'):
                        st['go'], st['last'] = True, None
                    continue
                if rest.startswith('info ') and I_NPS.search(rest) and I_TIME.search(rest):
                    st['last'] = rest
                elif rest.startswith('bestmove'):
                    if st['go'] and st['last']:
                        info = st['last']
                        tms, nps = int(I_TIME.search(info).group(1)), int(I_NPS.search(info).group(1))
                        nm = I_NODES.search(info)
                        e = engines.setdefault(name, new_eng())
                        stats['searches'] += 1
                        e['searches'] += 1
                        if tms >= min_ms:
                            e['nps'].append(nps)
                            e['nps_phase'].setdefault(phase_of(st['ply'], bands), []).append(nps)
                            if nm:
                                e['nodes'] += int(nm.group(1))
                                e['ntime'] += tms
                            if st['game'] is not None:   # both engines share a slot: key games by engine too
                                games.setdefault((name, st['game']), []).append((nps, int(nm.group(1)) if nm else 0, tms))
                        else:
                            e['short'] += 1
                    st['go'], st['last'] = False, None
    per_game = {}
    if per_game_n:
        for name in sorted(games_order):
            rows = []
            for gid in games_order[name][:per_game_n]:
                recs = games.get((name, gid), [])
                rows.append({'game': gid, 'searches': len(recs),
                             'median_nps': f'{statistics.median([r[0] for r in recs]):.1f}' if recs else None,
                             'agg_nps': (sum(r[1] for r in recs) * 1000 // sum(r[2] for r in recs)) if recs else None})
            per_game[name] = rows
    return stats, per_game


def audit_log(path, names):
    out = {'finished_games': 0, 'events': {}, 'warning_lines': 0, 'started_cap': None, 'results_block': None,
           'autopromote_style_crash_matches': 0}
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('Warning;'):
            out['warning_lines'] += 1
        m = FIN.match(line)
        if m:
            out['finished_games'] += 1
            w, b, res, reason = m.group(2), m.group(3), m.group(4), m.group(5)
            ev = classify('', [reason])
            if ev:
                side = loser_side([reason], res)
                who = {'w': w, 'b': b}.get(side, '?')
                out['events'].setdefault(who, {'tl': 0, 'illegal': 0, 'crash': 0})[ev] += 1
        if out['started_cap'] is None:
            sm = re.match(r'^Started game \d+ of (\d+)', line)
            if sm:
                out['started_cap'] = int(sm.group(1))
    rb = list(RES.finditer(text))
    if rb:
        g = rb[-1]
        out['results_block'] = {'games': int(g.group(1)), 'wins': int(g.group(2)), 'losses': int(g.group(3)), 'draws': int(g.group(4))}
    out['autopromote_style_crash_matches'] = len(AP_CRASH.findall(text))
    for nm in names:
        out['events'].setdefault(nm, {'tl': 0, 'illegal': 0, 'crash': 0})
    out['events'] = dict(sorted(out['events'].items()))
    return out


def role_of(name):
    return 'cand' if name.startswith('cand') else 'base' if name.startswith('base') else name


def summarize(engines, bands):
    res = {}
    for name in sorted(engines):
        e = engines[name]
        d = {'role': role_of(name), 'engine_moves': e['moves'], 'book_moves': e['book'], 'unparsed_moves': e['unparsed'],
             'events': e['events']}
        d['depth'] = {'mean': round(statistics.fmean(e['depth']), 2) if e['depth'] else None, 'median': med(e['depth']),
                      'by_phase_median': {k: med(v) for k, v in sorted(e['depth_phase'].items())}}
        d['time_used_ms'] = dist(e['used'], 1)
        d['used_over_soft'] = dist(e['ratio'], 3)
        d['over_increment'] = {'n': e['over_inc'], 'share': round(e['over_inc'] / e['moves'], 4) if e['moves'] else None}
        d['over_hard_limit'] = {'n': e['over_hard'], 'share': round(e['over_hard'] / e['moves'], 5) if e['moves'] else None,
                                'max_over_ms': max(e['over_hard_ms']) if e['over_hard_ms'] else 0}
        d['lowest_clock_ms'] = e['min_tl']
        d['clock_accounting'] = {'checked': e['acct_n'], 'mismatch_gt_2ms': e['acct_bad']}
        d['nps'] = {'searches': e['searches'], 'searches_below_min_ms': e['short'], 'used': len(e['nps']),
                    'median': med(e['nps']), 'aggregate': (e['nodes'] * 1000 // e['ntime']) if e['ntime'] else None,
                    'by_phase_median': {k: med(v) for k, v in sorted(e['nps_phase'].items())}}
        res[name] = d
    return res


def check_out(path, inputs):
    if path is None:
        return
    for root in DENY_ROOTS:
        if under(path, root):
            raise Refused(f'refusing output {path}: under protected root {root}')
    for i in inputs:
        if norm(path) == norm(i):
            raise Refused(f'refusing output {path}: it is an input file')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--pgn', required=True)
    ap.add_argument('--log', help='fastchess stdout log (<tag>.log)')
    ap.add_argument('--engine-log', action='append', default=[], help='fastchess -log engine=true file (repeatable)')
    ap.add_argument('--ref', help='JSON of this tool for a reference gate (p99 flag)')
    ap.add_argument('--tm', default='22,75,60,5,10', help='soft_div,inc_pct,hard_pct,hard_mult,overhead_ms (AL1 lock)')
    ap.add_argument('--phase-plies', default='40,80')
    ap.add_argument('--nps-min-ms', type=int, default=100)
    ap.add_argument('--asym', type=float, default=0.03)
    ap.add_argument('--p99-x', type=float, default=1.5)
    ap.add_argument('--per-game-nps', type=int, default=0, help='list the first N engine-log games per engine')
    ap.add_argument('--label', default='')
    ap.add_argument('--out-json')
    ap.add_argument('--out-md')
    a = ap.parse_args(argv)
    inputs = [a.pgn] + ([a.log] if a.log else []) + a.engine_log + ([a.ref] if a.ref else [])
    try:
        for p in (a.out_json, a.out_md):
            check_out(p, inputs)
        for p in inputs:
            if not os.path.isfile(p):
                raise Refused(f'input not found: {p}')
        tmv = [int(x) for x in a.tm.split(',')]
        if len(tmv) != 5 or tmv[0] <= 0:
            raise Refused('--tm needs 5 integers soft_div,inc_pct,hard_pct,hard_mult,overhead_ms')
        bands = [int(x) for x in a.phase_plies.split(',')]
        if bands != sorted(bands) or not bands:
            raise Refused('--phase-plies must be ascending integers')
    except (Refused, ValueError) as ex:
        print(f'S38: {ex}', file=sys.stderr)
        return 2
    tm = TimeModel(*tmv)
    engines = {}
    pg = audit_pgn(a.pgn, tm, bands, engines)
    names = sorted(engines)
    est, per_game = audit_engine_logs(a.engine_log, bands, a.nps_min_ms, engines, a.per_game_nps) if a.engine_log else (None, {})
    lg = audit_log(a.log, names) if a.log else None
    eng = summarize(engines, bands)
    checks, flags = {}, []
    if lg:
        tl_p = {n: eng[n]['events']['tl'] for n in names}
        tl_l = {n: lg['events'].get(n, {}).get('tl', 0) for n in names}
        cr_p = {n: eng[n]['events']['crash'] + eng[n]['events']['illegal'] for n in names}
        cr_l = {n: lg['events'].get(n, {}).get('crash', 0) + lg['events'].get(n, {}).get('illegal', 0) for n in names}
        checks['tl_pgn_vs_fastchess_log'] = {'pgn': tl_p, 'log': tl_l, 'match': tl_p == tl_l}
        checks['illegal_crash_pgn_vs_fastchess_log'] = {'pgn': cr_p, 'log': cr_l, 'match': cr_p == cr_l}
        checks['games_pgn_vs_finished_lines'] = {'pgn': pg['games'], 'log': lg['finished_games'], 'match': pg['games'] == lg['finished_games']}
    meds = {n: eng[n]['nps']['median'] for n in names if eng[n]['nps']['median']}
    if len(meds) == 2:
        lo, hi = min(meds.values()), max(meds.values())
        asym = hi / lo - 1
        checks['nps_asymmetry'] = {'median_nps': meds, 'asymmetry': round(asym, 4), 'threshold': a.asym}
        if asym > a.asym:
            flags.append(f'NPS_ASYMMETRY {asym * 100:.2f}% > {a.asym * 100:.1f}% (median nps {meds})')
    if a.ref:
        with open(a.ref, 'r', encoding='utf-8') as f:
            ref = json.load(f)
        rr = {v['role']: v for v in ref.get('engines', {}).values()}
        cmp = {}
        for n in names:
            r = rr.get(eng[n]['role'])
            cur = eng[n]['used_over_soft'].get('p99')
            if r and cur is not None and r['used_over_soft'].get('p99'):
                x = cur / r['used_over_soft']['p99']
                cmp[n] = {'p99_used_over_soft': cur, 'ref_p99': r['used_over_soft']['p99'], 'ratio': round(x, 3)}
                if x > a.p99_x:
                    flags.append(f'P99_OVERSHOOT {n}: p99 used/soft {cur} = {x:.2f}x reference {r["used_over_soft"]["p99"]} (> {a.p99_x}x)')
        checks['p99_vs_reference'] = {'reference': ref.get('label') or ref.get('inputs', {}).get('pgn', {}).get('name'), 'engines': cmp}
    mism = [k for k, v in checks.items() if isinstance(v, dict) and v.get('match') is False]
    for k in mism:
        flags.append(f'CROSS_CHECK_MISMATCH {k}')
    for n in names:
        if eng[n]['clock_accounting']['mismatch_gt_2ms']:
            flags.append(f'CLOCK_ACCOUNTING {n}: {eng[n]["clock_accounting"]["mismatch_gt_2ms"]} moves where tl != before - used + inc')
    out = {'tool': VERSION, 'label': a.label,
           'inputs': {'pgn': file_meta(a.pgn), 'log': file_meta(a.log) if a.log else None,
                      'engine_logs': [file_meta(p) for p in a.engine_log], 'ref': file_meta(a.ref) if a.ref else None},
           'settings': {'time_model': tm.as_dict(), 'phase_plies': bands, 'nps_min_ms': a.nps_min_ms, 'asym': a.asym, 'p99_x': a.p99_x},
           'pgn': pg, 'engines': eng, 'fastchess_log': lg, 'engine_log_stats': est, 'per_game_nps': per_game,
           'cross_checks': checks, 'flags': flags}
    js = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=True) + '\n'
    if a.out_json:
        with open(a.out_json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(js)
    md = render_md(out)
    if a.out_md:
        with open(a.out_md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(md)
    print(md)
    if mism:
        return 3
    return 1 if flags else 0


def render_md(o):
    L = [f'# Gate time audit {o["label"]}'.rstrip(), '', f'Tool: {o["tool"]}. Inputs (read-only): ' +
         ', '.join(f'{v["name"]} ({v["bytes"]} B, sha256 {v["sha256"][:12]})' for v in
                   [o['inputs']['pgn'], o['inputs']['log']] + o['inputs']['engine_logs'] if v), '',
         f'PGN games {o["pgn"]["games"]}, terminations {o["pgn"]["terminations"]}, TC {o["pgn"]["time_controls"]}. '
         f'Time model {o["settings"]["time_model"]}; phases by ply {o["settings"]["phase_plies"]}; nps from searches >= {o["settings"]["nps_min_ms"]} ms.', '',
         '| engine | role | moves | TL | illegal | crash | depth mean / median | used ms p50/p95/p99/max | used/soft p50/p95/p99/max | over inc | over hard | lowest clock ms | median nps | agg nps |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for n, e in o['engines'].items():
        u, r = e['time_used_ms'], e['used_over_soft']
        q = lambda x: '/'.join(str(x.get(k)) for k in ('p50', 'p95', 'p99', 'max')) if x.get('n') else 'n/a'
        L.append(f'| {n} | {e["role"]} | {e["engine_moves"]} | {e["events"]["tl"]} | {e["events"]["illegal"]} | {e["events"]["crash"]} | '
                 f'{e["depth"]["mean"]} / {e["depth"]["median"]} | {q(u)} | {q(r)} | {e["over_increment"]["share"]} | '
                 f'{e["over_hard_limit"]["n"]} (max +{e["over_hard_limit"]["max_over_ms"]} ms) | {e["lowest_clock_ms"]} | {e["nps"]["median"]} | {e["nps"]["aggregate"]} |')
    L += ['', '| engine | phase | median depth | median nps |', '|---|---|---|---|']
    for n, e in o['engines'].items():
        for ph in sorted(set(e['depth']['by_phase_median']) | set(e['nps']['by_phase_median'])):
            L.append(f'| {n} | {ph} | {e["depth"]["by_phase_median"].get(ph)} | {e["nps"]["by_phase_median"].get(ph)} |')
    if o['fastchess_log']:
        lg = o['fastchess_log']
        L += ['', f'fastchess log: {lg["finished_games"]} Finished-game lines, events {lg["events"]}, "Warning;" lines '
                  f'{lg["warning_lines"]}, results block {lg["results_block"]}; autopromote-style crash-regex matches '
                  f'{lg["autopromote_style_crash_matches"]} (for comparison only).']
    L += ['', 'Cross-checks: ' + json.dumps(o['cross_checks'], sort_keys=True), '',
          'Flags: ' + ('; '.join(o['flags']) if o['flags'] else 'none'), '']
    if o['per_game_nps']:
        L += ['Per-game nps (first games per engine in the engine log):', '']
        for n, rows in o['per_game_nps'].items():
            for r in rows:
                L.append(f'- {n} game {r["game"]}: searches {r["searches"]}, median nps {r["median_nps"]}, aggregate nps {r["agg_nps"]}')
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    sys.exit(main())
