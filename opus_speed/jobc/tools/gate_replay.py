#!/usr/bin/env python3
"""gate_replay.py - replay a finished fastchess SPRT gate from its PGN (+ RUN_INFO / config / log) and check the
recorded verdict (Job C, Forge speed job).

usage: python -I -B gate_replay.py GATE_DIR [options]
       python -I -B gate_replay.py --pgn FILE.pgn [--log FILE.log] [--run-info RUN_INFO.json] [--config config.json]
                                   [--result-md RESULT.md] [options]
options: --results-csv FORGE_RESULTS.csv   also compare with the crew table row of this gate tag
         --verify-moves                    replay every SAN move with python-chess (slower; catches corrupt moves)
         --json OUT.json                   machine-readable report (never overwritten)
         --series OUT.csv                  LLR after every completed pair (never overwritten)
         --candidate NAME                  override the candidate name (default: RUN_INFO / log / first White)
         --concurrency N                   override the concurrency (max legitimate in-flight singles)

What it does: pentanomial counts over the game pairs in their completion order (the log's "Finished game" lines;
without a log the PGN GameEndTime, 1 s resolution), Elo / nElo, the exact fastchess 1.8.2 GSPRT LLR after
EVERY completed pair, the verdict (H1 / H0 at the first pair whose LLR crosses a bound, else CAP = no decision)
and the pair count where it was reached; the runner's net early-stop rule when RUN_INFO carries one; then a
comparison with the recorded verdict and numbers (RESULT.md, FORGE_RESULTS.csv) at the PRINTED pair count
(the pairs completed before the log's last result block; pairs still in flight at an SPRT stop finish later).

Exit codes: 0 = replay reproduces the recorded verdict and LLR (within 0.006); 1 = a mismatch (the replay
verdict is still printed, flagged MISMATCH); 2 = invalid input (truncated / corrupt / unpaired PGN, unreadable
files): an error message, NO verdict. Planning / audit only - never a stop rule for a running gate.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as gl  # noqa: E402

LLR_TOL = 0.006
ELO_TOL = 0.006


def replay(a):
    pgn, log_p, ri_p, cfg_p, res_p = (None,) * 5
    if a.gate:
        if not os.path.isdir(a.gate):
            raise gl.GateError(f'not a folder: {a.gate}')
        pgn, log_p, ri_p, cfg_p, res_p = gl.find_gate_files(a.gate)
    pgn = a.pgn or pgn
    log_p = a.log or log_p
    ri_p = a.run_info or ri_p
    cfg_p = a.config or cfg_p
    res_p = a.result_md or res_p
    if not pgn or not os.path.exists(pgn):
        raise gl.GateError('no PGN found (give a gate folder with <tag>.pgn or --pgn FILE)')
    info = gl.load_run_info(ri_p)
    cfg = gl.load_config(cfg_p)
    log = gl.parse_log(log_p) if log_p and os.path.exists(log_p) else None
    block = log['block'] if log else None
    bounds = gl.gate_bounds(info, cfg, block)
    if not bounds:
        raise gl.GateError('no SPRT bounds found (config.json sprt, RUN_INFO sprt or a printed result block)')
    e0, e1, alpha, beta, bsrc = bounds
    lo, hi = gl.sprt_bounds(alpha, beta)
    games = gl.parse_pgn_strict(pgn, verify_moves=a.verify_moves)
    cand = a.candidate or gl.candidate_name(info, block, games)
    conc = a.concurrency or info.get('concurrency') or cfg.get('concurrency') or None
    pairs, pinfo = gl.build_pairs(games, cand, log=log, concurrency=conc)
    if not pairs:
        raise gl.GateError('no complete game pair in the PGN')
    # ---- LLR after every completed pair, first crossing
    pt = [0, 0, 0, 0, 0]
    series, cross = [], None
    for p in pairs:
        pt[p['cell']] += 1
        llr = gl.exact_llr(pt, e0, e1)
        series.append((p['k'], p['round'], p['cell'], list(pt), llr))
        if llr is None:
            continue
        if cross is None and llr >= hi:
            cross = ('H1', p['k'], llr)
        elif cross is None and llr <= lo:
            cross = ('H0', p['k'], llr)
    n = len(pairs)
    final = series[-1]
    verdict = cross[0] if cross else 'CAP'
    out = {
        'gate': os.path.basename(os.path.normpath(a.gate)) if a.gate else os.path.basename(pgn),
        'pgn': pgn, 'log': log_p if log else None, 'run_info': ri_p, 'config': cfg_p, 'result_md': res_p,
        'candidate': cand, 'opponent': next(iter(({g['tags']['White'] for g in games} | {g['tags']['Black'] for g in games}) - {cand})),
        'bounds_nelo': [e0, e1], 'bounds_source': bsrc, 'alpha': alpha, 'beta': beta, 'llr_bounds': [round(lo, 4), round(hi, 4)],
        'games_in_pgn': len(games), 'pairs': n, 'singles': pinfo['singles'], 'order_source': pinfo['order_source'],
        'ptnml_all_pairs': final[3], 'llr_all_pairs': round(final[4], 4) if final[4] is not None else None,
        'replay_verdict': verdict, 'decided_at_pair': cross[1] if cross else None, 'decided_at_games': 2 * cross[1] if cross else None,
        'llr_at_decision': round(cross[2], 4) if cross else None,
        'mismatches': [], 'notes': [],
    }
    w, d, l = gl.tally_wdl(games, cand)
    out['wdl_all_games'] = [w, d, l]
    st = gl.ptnml_stats(final[3])
    if st:
        out.update({k: round(v, 4) for k, v in st.items() if k != 'var'})
    # ---- the printed count: pairs completed before the log's last result block
    m = sum(1 for p in pairs if p['before_block']) if log else n
    ptm = [0, 0, 0, 0, 0]
    for p in pairs[:m]:
        ptm[p['cell']] += 1
    llr_m = gl.exact_llr(ptm, e0, e1)
    stm = gl.ptnml_stats(ptm)
    out['printed_pairs'] = m
    out['ptnml_printed'] = ptm
    out['llr_printed_pairs'] = round(llr_m, 4) if llr_m is not None else None
    out['elo_printed_pairs'] = round(stm['elo'], 4) if stm else None
    out['nelo_printed_pairs'] = round(stm['nelo'], 4) if stm else None
    if n > m:
        out['notes'].append(f'{n - m} pair(s) completed after the printed block (in flight at the stop); the recorded numbers cover {m} pairs')
    # ---- runner early-stop rule (net gates): first printed block with Games >= rule games
    es = info.get('early_stop') if isinstance(info, dict) else None
    if isinstance(es, dict) and es.get('games') and log:
        done_rounds, fin_count, hit = set(), 0, None
        half = {}
        for f in log['finished']:
            fin_count += 1
            r = (f['no'] + 1) // 2
            half[r] = half.get(r, 0) + 1
            if half[r] == 2:
                done_rounds.add(r)
            if fin_count % 10 == 0 and 2 * len(done_rounds) >= es['games']:
                pt_e = [0, 0, 0, 0, 0]
                for p in pairs:
                    if p['round'] in done_rounds:
                        pt_e[p['cell']] += 1
                st_e = gl.ptnml_stats(pt_e)
                llr_e = gl.exact_llr(pt_e, e0, e1)
                fires = bool(st_e and llr_e is not None and st_e['elo'] < es.get('elo_max', -8) and llr_e < es.get('llr_max', -1.5))
                hit = {'block_games': 2 * len(done_rounds), 'elo': round(st_e['elo'], 2) if st_e else None,
                       'llr': round(llr_e, 2) if llr_e is not None else None, 'fires': fires, 'rule': {k: es[k] for k in ('games', 'elo_max', 'llr_max') if k in es}}
                break
        out['early_stop_rule'] = hit or {'rule': es, 'note': 'no printed block reached the rule games'}
        if hit and hit['fires'] and cross is None:
            out['replay_verdict'] = verdict = 'H0-early'
            out['decided_at_games'] = hit['block_games']
    # ---- recorded verdict / numbers
    rec = gl.parse_result_md(res_p) if res_p else {}
    csv_row = gl.load_results_csv(a.results_csv).get(out['gate']) if a.results_csv else None
    recorded = {}
    if rec.get('verdict_text'):
        recorded = {'source': 'RESULT.md', 'verdict': rec['verdict'], 'verdict_text': rec['verdict_text'][:140], 'llr': rec.get('llr'),
                    'games': rec.get('games'), 'ptnml': rec.get('ptnml'), 'elo': rec.get('elo'), 'nelo': rec.get('nelo'), 'clean': rec.get('clean')}
    elif csv_row:
        recorded = {'source': 'FORGE_RESULTS.csv', 'verdict': gl.classify_verdict(csv_row.get('verdict', '')), 'verdict_text': csv_row.get('verdict', '')[:140],
                    'llr': float(csv_row['llr']) if csv_row.get('llr') else None, 'games': int(csv_row['games']) if csv_row.get('games') else None,
                    'ptnml': [int(x) for x in csv_row['ptnml'].split()] if csv_row.get('ptnml') else None,
                    'elo': float(csv_row['elo']) if csv_row.get('elo') else None, 'nelo': float(csv_row['nelo']) if csv_row.get('nelo') else None,
                    'clean': csv_row.get('clean') == 'CLEAN'}
    elif block and block.get('finished'):
        v = block.get('sprt_completed') or ('CAP' if block.get('llr') is not None and lo < block['llr'] < hi else 'UNKNOWN')
        recorded = {'source': 'log block', 'verdict': v, 'verdict_text': f'log: SPRT completed {block.get("sprt_completed")}', 'llr': block.get('llr'),
                    'games': block.get('games'), 'ptnml': block.get('ptnml'), 'elo': block.get('elo'), 'nelo': block.get('nelo'), 'clean': None}
    out['recorded'] = recorded
    out['running'] = bool(log and not (log['block'] and log['block'].get('finished')))
    if csv_row:
        out['csv_row'] = {'verdict': gl.classify_verdict(csv_row.get('verdict', '')), 'llr': csv_row.get('llr'), 'games': csv_row.get('games'), 'clean': csv_row.get('clean')}
        if rec.get('verdict') and gl.classify_verdict(csv_row.get('verdict', '')) != rec['verdict']:
            out['mismatches'].append(f'FORGE_RESULTS.csv verdict {gl.classify_verdict(csv_row.get("verdict", ""))} differs from RESULT.md {rec["verdict"]}')
        if rec.get('llr') is not None and csv_row.get('llr') and abs(float(csv_row['llr']) - rec['llr']) > LLR_TOL:
            out['mismatches'].append(f'FORGE_RESULTS.csv LLR {csv_row["llr"]} differs from RESULT.md {rec["llr"]}')
    if recorded:
        rv = recorded['verdict']
        if rv != verdict and not (rv == 'UNKNOWN'):
            out['mismatches'].append(f'verdict: replay {verdict} vs recorded {rv} ({recorded["source"]})')
        if recorded.get('games') is not None and recorded['games'] != 2 * m:
            out['mismatches'].append(f'games: recorded {recorded["games"]} vs {2 * m} (= 2 x pairs completed before the printed block)')
        if recorded.get('ptnml') and recorded['ptnml'] != ptm:
            out['mismatches'].append(f'Ptnml: recorded {recorded["ptnml"]} vs replay {ptm} at the printed count')
        if recorded.get('llr') is not None and llr_m is not None and abs(recorded['llr'] - llr_m) > LLR_TOL:
            out['mismatches'].append(f'LLR: recorded {recorded["llr"]} vs replay {llr_m:.4f} at {m} pairs')
        if recorded.get('elo') is not None and stm and abs(recorded['elo'] - stm['elo']) > ELO_TOL:
            out['mismatches'].append(f'Elo: recorded {recorded["elo"]} vs replay {stm["elo"]:.4f}')
        if recorded.get('nelo') is not None and stm and abs(recorded['nelo'] - stm['nelo']) > ELO_TOL:
            out['mismatches'].append(f'nElo: recorded {recorded["nelo"]} vs replay {stm["nelo"]:.4f}')
        if recorded.get('clean') is False:
            out['notes'].append('recorded run is NOT CLEAN: the statistical verdict is compared, the flag is carried')
    else:
        out['notes'].append('no recorded verdict found (running gate or no RESULT.md / csv row): nothing to compare')
    if cross and n > cross[1] + (conc or 8):
        out['notes'].append(f'LLR crossed at pair {cross[1]} but {n - cross[1]} more pairs completed: more than one concurrency slot of in-flight pairs')
    out['series'] = series
    return out


def fmt(o):
    L = [f"== {o['gate']}: {o['candidate']} vs {o['opponent']}",
         f"bounds [{o['bounds_nelo'][0]:g}, {o['bounds_nelo'][1]:g}] nElo ({o['bounds_source']}), alpha {o['alpha']} beta {o['beta']}, LLR bounds {o['llr_bounds']}",
         f"PGN games {o['games_in_pgn']}, complete pairs {o['pairs']}, singles {len(o['singles'])} (aborted partners: {[s['partner_aborted'] for s in o['singles']]}), order from {o['order_source']}",
         f"W/D/L {o['wdl_all_games']}  Ptnml(all pairs) {o['ptnml_all_pairs']}  Elo {o.get('elo')} +/- {o.get('elo_err')}  nElo {o.get('nelo')} +/- {o.get('nelo_err')}  LLR {o['llr_all_pairs']}",
         f"printed count: {o['printed_pairs']} pairs  Ptnml {o['ptnml_printed']}  Elo {o['elo_printed_pairs']}  nElo {o['nelo_printed_pairs']}  LLR {o['llr_printed_pairs']}"]
    if o['replay_verdict'] in ('H1', 'H0'):
        L.append(f"REPLAY VERDICT: {o['replay_verdict']} at pair {o['decided_at_pair']} (game {o['decided_at_games']}), LLR {o['llr_at_decision']}")
    elif o['replay_verdict'] == 'H0-early':
        L.append(f"REPLAY VERDICT: H0-early (runner rule) at printed block {o['decided_at_games']} games: {o['early_stop_rule']}")
    else:
        L.append(f"REPLAY VERDICT: CAP - no decision in {o['pairs']} pairs ({2 * o['pairs']} games); UNPROVEN")
    if o.get('early_stop_rule') and o['replay_verdict'] != 'H0-early':
        L.append(f"early-stop rule: {o['early_stop_rule']}")
    r = o.get('recorded')
    if r:
        L.append(f"recorded ({r['source']}): {r['verdict']}  LLR {r.get('llr')}  games {r.get('games')}  Ptnml {r.get('ptnml')}  Elo {r.get('elo')}  nElo {r.get('nelo')}  clean {r.get('clean')}")
        L.append(f"  verdict text: {r.get('verdict_text')}")
    for n_ in o['notes']:
        L.append(f"note: {n_}")
    for m_ in o['mismatches']:
        L.append(f"MISMATCH: {m_}")
    L.append('CHECK: ' + ('OK - replay reproduces the recorded verdict and numbers' if not o['mismatches'] and r else
                          'MISMATCH' if o['mismatches'] else 'no recorded result to compare'))
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('gate', nargs='?')
    ap.add_argument('--pgn')
    ap.add_argument('--log')
    ap.add_argument('--run-info')
    ap.add_argument('--config')
    ap.add_argument('--result-md')
    ap.add_argument('--results-csv')
    ap.add_argument('--candidate')
    ap.add_argument('--concurrency', type=int)
    ap.add_argument('--verify-moves', action='store_true')
    ap.add_argument('--json')
    ap.add_argument('--series')
    a = ap.parse_args()
    if not a.gate and not a.pgn:
        ap.print_usage()
        return 2
    for p in (a.json, a.series):
        if p and os.path.exists(p):
            print(f'gate_replay: {p} exists (never overwritten)', file=sys.stderr)
            return 2
    try:
        o = replay(a)
    except gl.GateError as e:
        print(f'gate_replay: ERROR: {e}', file=sys.stderr)
        print('gate_replay: INVALID INPUT - no verdict')
        return 2
    except (OSError, ValueError) as e:
        print(f'gate_replay: ERROR: unreadable input: {e}', file=sys.stderr)
        print('gate_replay: INVALID INPUT - no verdict')
        return 2
    series = o.pop('series')
    print(fmt(o))
    if a.series:
        with open(a.series, 'w', newline='\n') as f:
            f.write('pair,round,cell,ptnml0,ptnml1,ptnml2,ptnml3,ptnml4,llr\n')
            for k, r, c, pt, llr in series:
                f.write(f'{k},{r},{c},{",".join(str(x) for x in pt)},{"" if llr is None else f"{llr:.5f}"}\n')
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(o, f, indent=1)
            f.write('\n')
    return 1 if o['mismatches'] else 0


if __name__ == '__main__':
    sys.exit(main())
