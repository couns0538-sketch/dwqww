#!/usr/bin/env python3
"""gate_summary.py - Opus R15: summary of fastchess gates from their own log and PGN (standard library only).

usage: python -I -B gate_summary.py GATE_DIR [GATE_DIR ...] [--json OUT] [--watch] [--last-min 60]
       python -I -B gate_summary.py --all ROOT [--match TEXT] [--json OUT]

Per gate folder (the crew's layout: <tag>.log = fastchess stdout, <tag>.pgn, optional RUN_INFO.json / RESULT.md):
  - from the PGN: games, W / D / L of the candidate (the first engine of fastchess's "Results of A vs B" line, else
    RUN_INFO's candidate), the pentanomial Ptnml(0-2) from the game pairs (both games of a Round), Elo +/- (95 %) and
    nElo +/- from the pentanomial, the exact fastchess 1.8.2 GSPRT LLR (normalized model, MLE under the t-value
    constraint, as the reference SPRT code LLRcalc) for the gate's own bounds, problem games by PGN Termination (time forfeit,
    illegal move, abandoned / stalled connection = disconnect or crash, other), games per hour;
  - from the log: the last printed result block and every "loses on time" / illegal / disconnect reason line;
  - a check that the PGN numbers reproduce the printed ones (W/D/L and Ptnml exactly, Elo / nElo / LLR to the
    printed rounding); a running gate is compared with its latest printed block (games may differ by the games in
    flight; then the check says so instead of failing).
--watch adds, for a running gate, games per 10 minutes over the last --last-min minutes and the mean depth and time
per move of each engine (from the PGN move comments), to see whether the gate still plays at its normal speed.
Exit 0 = every gate summarised and every finished gate reproduced its printed numbers; 1 = a mismatch or an
unreadable gate; 2 = usage.
"""
import argparse
import datetime
import glob
import json
import math
import os
import re
import sys

NT = 800.0 / math.log(10.0)
SC = (0.0, 0.25, 0.5, 0.75, 1.0)
Z95 = 1.959963984540054


def elo_of_score(s):
    s = min(max(s, 1e-12), 1.0 - 1e-12)
    return -400.0 * math.log10(1.0 / s - 1.0)


def ptnml_stats(pt):
    n = float(sum(pt))
    if n == 0:
        return None
    p = [c / n for c in pt]
    a = sum(pi * si for pi, si in zip(p, SC))
    var = sum(pi * si * si for pi, si in zip(p, SC)) - a * a
    if var <= 0:
        return None
    se = math.sqrt(var / n)
    elo = elo_of_score(a)
    err = (elo_of_score(a + Z95 * se) - elo_of_score(a - Z95 * se)) / 2.0
    nelo = (a - 0.5) / math.sqrt(2.0 * var) * NT
    nelo_err = Z95 * se / math.sqrt(2.0 * var) * NT
    return {'score': a, 'elo': elo, 'elo_err': err, 'nelo': nelo, 'nelo_err': nelo_err}


def _secular(phat, a):
    """Root x of sum_i p_i a_i / (1 + x a_i) = 0 over the occupied cells (bisection-safeguarded Newton)."""
    cells = [(p, ai) for p, ai in zip(phat, a) if p > 0]
    amax = max(ai for _, ai in cells)
    amin = min(ai for _, ai in cells)
    if not (amax > 0 > amin):
        return None
    lo, hi = -1.0 / amax, -1.0 / amin
    x = 0.0
    for _ in range(200):
        f = sum(p * ai / (1.0 + x * ai) for p, ai in cells)
        fp = -sum(p * ai * ai / (1.0 + x * ai) ** 2 for p, ai in cells)
        if f > 0:
            lo = x
        else:
            hi = x
        xn = x - f / fp if fp != 0 else 0.5 * (lo + hi)
        if not (lo < xn < hi):
            xn = 0.5 * (lo + hi)
        if abs(xn - x) <= 1e-15 * (1.0 + abs(x)):
            return xn
        x = xn
    return x


def _mle_tvalue(phat, s):
    """Cell probabilities of maximum likelihood under (mu - 0.5) / sigma = s, as the reference SPRT code (LLRcalc.MLE_tvalue, which
    fastchess follows): start from the uniform pdf, at most 10 fixed-point steps, stop when no cell moves by 1e-9.
    With a converged solution this equals the exact MLE; in extreme gates (an early H0 at Elo -86) the 10-step value
    is what the gate printed, so that is what is reproduced."""
    pdf = [1.0 / len(phat)] * len(phat)
    for _ in range(10):
        mu = sum(p * si for p, si in zip(pdf, SC))
        var = max(sum(p * si * si for p, si in zip(pdf, SC)) - mu * mu, 1e-300)
        sigma = math.sqrt(var)
        a = [si - 0.5 - s * sigma * (1.0 + ((mu - si) / sigma) ** 2) / 2.0 for si in SC]
        x = _secular(phat, a)
        if x is None:
            return None
        new = [p / (1.0 + x * ai) for p, ai in zip(phat, a)]
        done = max(abs(u - v) for u, v in zip(new, pdf)) < 1e-9
        pdf = new
        if done:
            break
    return pdf


def exact_llr(pt, e0, e1):
    """fastchess normalized-model pentanomial LLR. Empty cells count 1e-3 (reference SPRT code, results_to_pdf)."""
    reg = [max(1e-3, float(c)) for c in pt]
    n = sum(reg)
    if sum(pt) == 0:
        return None
    phat = [c / n for c in reg]
    p0 = _mle_tvalue(phat, e0 / NT * math.sqrt(2.0))
    p1 = _mle_tvalue(phat, e1 / NT * math.sqrt(2.0))
    if p0 is None or p1 is None:
        return None
    return n * sum(p * math.log(q1 / q0) for p, q0, q1 in zip(phat, p0, p1) if p > 0)


TAG_RX = re.compile(r'\[(\w+) "([^"]*)"\]')
COMMENT_RX = re.compile(r'\{([+-]?(?:\d+\.\d+|M\d+|-M\d+|#?-?\d+))/(\d+) ([\d.]+)s')


def read_pgn(path):
    games, cur, moves = [], None, []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('['):
                m = TAG_RX.match(line)
                if m:
                    if cur is None or cur.get('_body'):
                        if cur is not None:
                            cur['moves'] = moves
                            games.append(cur)
                        cur, moves = {}, []
                    cur[m.group(1)] = m.group(2)
                continue
            if cur is not None and line.strip():
                cur['_body'] = True
                moves.extend(COMMENT_RX.findall(line))
    if cur is not None:
        cur['moves'] = moves
        games.append(cur)
    return games


def parse_time(s):
    try:
        return datetime.datetime.strptime(s[:19], '%Y-%m-%dT%H:%M:%S')
    except (TypeError, ValueError):
        return None


def last_block(log_text):
    """The last fastchess result block of the log, or None."""
    i = log_text.rfind('Results of ')
    if i < 0:
        return None
    t = log_text[i:i + 2000]
    b = {}
    m = re.match(r'Results of (.+?) vs (.+?) \(([^)]*)\):', t)
    if m:
        b['a'], b['b'], b['settings'] = m.group(1), m.group(2), m.group(3)
    m = re.search(r'Elo: (-?[\d.]+|inf|-inf|nan) \+/- ([\d.]+|nan|inf), nElo: (-?[\d.]+|nan|inf) \+/- ([\d.]+|nan|inf)', t)
    if m:
        b['elo'], b['elo_err'], b['nelo'], b['nelo_err'] = (float(x) for x in m.groups())
    m = re.search(r'Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)', t)
    if m:
        b['games'], b['w'], b['l'], b['d'] = (int(x) for x in m.groups())
    m = re.search(r'Ptnml\(0-2\): \[([\d, ]+)\]', t)
    if m:
        b['ptnml'] = [int(x) for x in m.group(1).split(',')]
    m = re.search(r'LLR: (-?[\d.]+) \([^)]*\) \((-?[\d.]+), (-?[\d.]+)\) \[(-?[\d.]+), (-?[\d.]+)\]', t)
    if m:
        b['llr'], b['llr_lo'], b['llr_hi'], b['elo0'], b['elo1'] = (float(x) for x in m.groups())
    b['finished'] = 'Finished match' in log_text[i:]
    return b


def find_files(d):
    base = os.path.basename(os.path.normpath(d))
    pgn = os.path.join(d, base + '.pgn')
    log = os.path.join(d, base + '.log')
    if not os.path.exists(pgn):
        cands = [p for p in glob.glob(os.path.join(d, '*.pgn')) if 'engine_io' not in os.path.basename(p)]
        pgn = cands[0] if len(cands) == 1 else None
    if not os.path.exists(log):
        cands = [p for p in glob.glob(os.path.join(d, '*.log')) if 'engine_io' not in os.path.basename(p)]
        log = cands[0] if len(cands) == 1 else None
    return pgn, log


def run_info(d):
    p = os.path.join(d, 'RUN_INFO.json')
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def tally(games, cand):
    """W / D / L of `cand` and the pentanomial over complete Round pairs (both games of a round), in file order."""
    w = d_ = l = 0
    rounds = {}
    for g in games:
        res = g.get('Result', '*')
        if res == '1-0':
            pts = 1.0 if g.get('White') == cand else 0.0
        elif res == '0-1':
            pts = 0.0 if g.get('White') == cand else 1.0
        elif res == '1/2-1/2':
            pts = 0.5
        else:
            continue
        if pts == 1.0:
            w += 1
        elif pts == 0.0:
            l += 1
        else:
            d_ += 1
        rounds.setdefault(g.get('Round', '?'), []).append(pts)
    pt = [0, 0, 0, 0, 0]
    open_pairs = 0
    for v in rounds.values():
        if len(v) == 2:
            pt[int(round((v[0] + v[1]) * 2))] += 1
        else:
            open_pairs += 1
    return w, d_, l, pt, open_pairs


def summarise(d, watch=False, last_min=60):
    pgn, log = find_files(d)
    out = {'gate': os.path.basename(os.path.normpath(d)), 'dir': os.path.abspath(d), 'pgn': pgn, 'log': log,
           'problems': [], 'checks': {}}
    if not pgn:
        out['skipped'] = 'no PGN in the folder (older gate layout or not started)'
        return out
    log_text = open(log, encoding='utf-8', errors='replace').read() if log else ''
    block = last_block(log_text) if log_text else None
    info = run_info(d)
    cand = (block or {}).get('a')
    if not cand and isinstance(info.get('candidate'), dict):
        cand = info['candidate'].get('name')
    games = read_pgn(pgn)
    if not cand and games:
        cand = games[0].get('White')
    out['candidate'] = cand
    out['opponent'] = (block or {}).get('b')
    term = {}
    for g in games:
        t = g.get('Termination', '?')
        term[t] = term.get(t, 0) + 1
    w, d_, l, pt, open_pairs = tally(games, cand)
    out.update(games=w + d_ + l, w=w, d=d_, l=l, ptnml=pt, open_pairs=open_pairs, terminations=term)
    st = ptnml_stats(pt)
    if st:
        out.update({k: round(v, 4) for k, v in st.items()})
    e0 = (block or {}).get('elo0')
    e1 = (block or {}).get('elo1')
    if e0 is None:
        sp = (info.get('config') or {}).get('sprt') if isinstance(info.get('config'), dict) else None
        if isinstance(sp, dict):
            e0, e1 = sp.get('elo0'), sp.get('elo1')
    if e0 is not None and e1 is not None:
        llr = exact_llr(pt, float(e0), float(e1))
        out['bounds'] = [e0, e1]
        out['llr'] = round(llr, 4) if llr is not None else None
    out['time_forfeits'] = term.get('time forfeit', 0)
    out['illegal_moves'] = term.get('illegal move', 0)
    out['disconnects'] = term.get('abandoned', 0) + term.get('stalled connection', 0)
    out['other_terminations'] = {k: v for k, v in term.items() if k not in ('normal', 'adjudication', 'time forfeit',
                                                                            'illegal move', 'abandoned', 'stalled connection')}
    reasons = re.findall(r'Finished game \d+ \([^)]*\): \S+ \{([^}]*)\}', log_text)
    out['log_time_losses'] = sum('loses on time' in r for r in reasons)
    out['log_illegal'] = sum('illegal' in r.lower() for r in reasons)
    out['log_disconnects'] = sum(('disconnect' in r.lower()) or ('crash' in r.lower()) or ('stall' in r.lower()) for r in reasons)
    ends = [t for t in (parse_time(g.get('GameEndTime')) for g in games) if t]
    starts = [t for t in (parse_time(g.get('GameStartTime')) for g in games) if t]
    if ends and starts:
        span_h = (max(ends) - min(starts)).total_seconds() / 3600.0
        out['first_start'] = min(starts).strftime('%Y-%m-%d %H:%M:%S')
        out['last_end'] = max(ends).strftime('%Y-%m-%d %H:%M:%S')
        out['games_per_hour'] = round(len(ends) / span_h, 1) if span_h > 0 else None
    out['finished'] = bool(block and block.get('finished'))
    # Reproduce the printed block from the log's own "Finished game K (A vs B): result" lines written before it: that
    # is exactly the set of games fastchess counted (games still in flight at an SPRT stop reach the PGN later; the
    # PGN's write order is not the printing order). Pairs are games 2r-1 and 2r (round r).
    if block and 'games' in block:
        n = block['games']
        chk = {}
        cut = log_text.rfind('Results of ')
        logged = re.findall(r'Finished game (\d+) \((.+?) vs (.+?)\): (1-0|0-1|1/2-1/2) \{', log_text[:cut])
        if logged:
            # fastchess (pentanomial mode) prints W / D / L and Games over COMPLETE pairs only (checked on gate68:
            # 1392 logged games, 2 of them singles of unfinished pairs, printed 1390 = the 695 complete pairs)
            per_round = {}
            for k, _, _, _ in logged:
                per_round[(int(k) + 1) // 2] = per_round.get((int(k) + 1) // 2, 0) + 1
            lg = [{'Round': str((int(k) + 1) // 2), 'White': wt, 'Black': bk, 'Result': r}
                  for k, wt, bk, r in logged if per_round[(int(k) + 1) // 2] == 2]
            bw, bd, bl, bpt, _ = tally(lg, cand)
            bst = ptnml_stats(bpt)
            chk['wdl'] = [block['w'], block['d'], block['l']] == [bw, bd, bl]
            chk['ptnml'] = block.get('ptnml') == bpt
            if bst and 'elo' in block:
                chk['elo'] = abs(block['elo'] - bst['elo']) <= 0.006 and abs(block['nelo'] - bst['nelo']) <= 0.006
                chk['elo_err'] = abs(block['elo_err'] - bst['elo_err']) <= 0.006
            if e0 is not None and 'llr' in block:
                bl_llr = exact_llr(bpt, float(e0), float(e1))
                chk['llr'] = bl_llr is not None and abs(block['llr'] - bl_llr) <= 0.006
            chk['games'] = (bw + bd + bl) == n
            if out['games'] > n:
                chk['note'] = f"{out['games'] - n} game(s) in the PGN finished after the printed block (in flight)"
            for k, v in chk.items():
                if v is False:
                    out['problems'].append(f'{k}: the log games before the printed block do not give its {k}')
        else:
            chk['note'] = 'no "Finished game" lines in the log: printed block not reproduced'
            out['problems'].append(chk['note'])
        out['checks'] = chk
        out['printed'] = block
    if watch and ends:
        last = max(ends)
        since = last - datetime.timedelta(minutes=last_min)
        bins = {}
        for t in ends:
            if t >= since:
                k = t.replace(minute=t.minute - t.minute % 10, second=0)
                bins[k.strftime('%H:%M')] = bins.get(k.strftime('%H:%M'), 0) + 1
        out['games_per_10min'] = dict(sorted(bins.items()))
        per = {}
        recent = [g for g in games if (parse_time(g.get('GameEndTime')) or last) >= since]
        for g in recent:
            mv = g.get('moves', [])
            for i, (_, depth, secs) in enumerate(mv):
                side = g.get('White') if i % 2 == 0 else g.get('Black')
                e = per.setdefault(side, [0, 0.0, 0.0])
                e[0] += 1
                e[1] += int(depth)
                e[2] += float(secs)
        out['per_engine_recent'] = {k: {'moves': v[0], 'mean_depth': round(v[1] / v[0], 2), 'mean_sec': round(v[2] / v[0], 3)}
                                    for k, v in per.items() if v[0]}
    return out


def html_page(results):
    """One self-contained page: a sortable table of every summarised gate (click a header to sort)."""
    import html as h
    cols = ['gate', 'candidate', 'opponent', 'state', 'games', 'W/D/L', 'Ptnml', 'Elo', '+/-', 'nElo', 'LLR', 'bounds',
            'time forfeits', 'illegal', 'disconnects', 'games/h', 'printed block', 'problems']
    rows = []
    for o in results:
        if o.get('skipped'):
            continue
        b = o.get('bounds') or ['', '']
        llr = o.get('llr')
        state = 'finished' if o.get('finished') else 'running / unknown'
        if o.get('finished') and llr is not None:
            state = 'H1' if llr >= 2.94 else ('H0' if llr <= -2.94 else 'cap / no decision')
        chk = o.get('checks') or {}
        rep = 'reproduced' if chk and all(v is True for k, v in chk.items() if k != 'note') else ('-' if not chk else 'DIFF')
        vals = [o.get('gate'), o.get('candidate'), o.get('opponent'), state, o.get('games'),
                f"{o.get('w')}/{o.get('d')}/{o.get('l')}", str(o.get('ptnml')), o.get('elo'), o.get('elo_err'),
                o.get('nelo'), llr, f'[{b[0]}, {b[1]}]', o.get('time_forfeits'), o.get('illegal_moves'),
                o.get('disconnects'), o.get('games_per_hour'), rep, '; '.join(o.get('problems', []))]
        rows.append('<tr>' + ''.join(f'<td>{h.escape("" if v is None else str(v))}</td>' for v in vals) + '</tr>')
    gen = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>Forge gates</title><style>body{font:13px system-ui,sans-serif;margin:16px;background:#fff;color:#111}'
            'table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;text-align:right;white-space:nowrap}'
            'td:nth-child(-n+4),th:nth-child(-n+4){text-align:left}th{cursor:pointer;background:#eee;position:sticky;top:0}'
            '@media (prefers-color-scheme:dark){body{background:#111;color:#eee}th{background:#333}td,th{border-color:#444}}'
            '</style></head><body>'
            f'<h1>Forge gates ({len(rows)})</h1><p>gate_summary.py, {h.escape(gen)} (PC clock). Numbers are recomputed '
            'from each gate\'s own log and PGN; "reproduced" = the log games give the printed block exactly. Click a '
            'header to sort.</p><table id="t"><thead><tr>' + ''.join(f'<th>{h.escape(c)}</th>' for c in cols) +
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table><script>'
            'document.querySelectorAll("th").forEach((th,i)=>th.onclick=()=>{const tb=document.querySelector("#t tbody");'
            'const r=[...tb.rows];const dir=th.dataset.d=th.dataset.d==="1"?"-1":"1";'
            'r.sort((a,b)=>{const x=a.cells[i].textContent,y=b.cells[i].textContent,nx=parseFloat(x),ny=parseFloat(y);'
            'return (isNaN(nx)||isNaN(ny)?x.localeCompare(y):nx-ny)*dir;});r.forEach(x=>tb.appendChild(x));});'
            '</script></body></html>\n')


def fmt(o):
    if o.get('skipped'):
        return f"== {o['gate']}  SKIPPED: {o['skipped']}"
    lines = [f"== {o['gate']}  candidate {o.get('candidate')}  vs {o.get('opponent')}  "
             f"{'finished' if o.get('finished') else 'running/unknown'}"]
    if 'games' in o:
        lines.append(f"games {o['games']}  W/D/L {o['w']}/{o['d']}/{o['l']}  Ptnml {o['ptnml']}  open pairs {o['open_pairs']}")
    if 'elo' in o:
        lines.append(f"Elo {o['elo']:+.2f} +/- {o['elo_err']:.2f}  nElo {o['nelo']:+.2f} +/- {o['nelo_err']:.2f}  "
                     f"LLR {o.get('llr')} bounds {o.get('bounds')}")
    lines.append(f"time forfeits {o.get('time_forfeits')} (log {o.get('log_time_losses')})  illegal {o.get('illegal_moves')} "
                 f"(log {o.get('log_illegal')})  disconnects/crashes {o.get('disconnects')} (log {o.get('log_disconnects')})  "
                 f"other {o.get('other_terminations')}  games/h {o.get('games_per_hour')}")
    if o.get('checks'):
        lines.append(f"reproduces the printed block: {o['checks']}")
    if o.get('games_per_10min'):
        lines.append(f"games per 10 min: {o['games_per_10min']}")
    if o.get('per_engine_recent'):
        for k, v in o['per_engine_recent'].items():
            lines.append(f"  {k}: {v['moves']} moves, mean depth {v['mean_depth']}, mean {v['mean_sec']} s/move")
    for p in o.get('problems', []):
        lines.append(f"PROBLEM {p}")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gates', nargs='*')
    ap.add_argument('--all', default='')
    ap.add_argument('--match', default='')
    ap.add_argument('--json', default='')
    ap.add_argument('--watch', action='store_true')
    ap.add_argument('--last-min', type=int, default=60)
    ap.add_argument('--html', default='', help='also write one self-contained HTML page (sortable table, no network)')
    a = ap.parse_args()
    if a.html and os.path.exists(a.html):
        print(f'gate_summary: {a.html} exists (never overwritten)', file=sys.stderr)
        return 2
    dirs = list(a.gates)
    if a.all:
        dirs += sorted(p for p in glob.glob(os.path.join(a.all, '*')) if os.path.isdir(p) and a.match in os.path.basename(p))
    if not dirs:
        print('gate_summary: no gate folder given', file=sys.stderr)
        return 2
    if a.json and os.path.exists(a.json):
        print(f'gate_summary: {a.json} exists (never overwritten)', file=sys.stderr)
        return 2
    results, bad = [], 0
    for d in dirs:
        if not os.path.isdir(d):
            print(f'gate_summary: not a folder: {d}', file=sys.stderr)
            bad += 1
            continue
        try:
            o = summarise(d, a.watch, a.last_min)
        except (OSError, ValueError) as e:
            o = {'gate': os.path.basename(d), 'problems': [f'unreadable: {e}']}
        results.append(o)
        print(fmt(o))
        if o.get('problems'):
            bad += 1
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(results, f, indent=1)
            f.write('\n')
    if a.html:
        with open(a.html, 'w', newline='\n', encoding='utf-8') as f:
            f.write(html_page(results))
        print(f'gate_summary: wrote {a.html}')
    skipped = sum(1 for o in results if o.get('skipped'))
    print(f'gate_summary: {len(results)} gate folder(s), {skipped} skipped (no PGN), {bad} with problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
