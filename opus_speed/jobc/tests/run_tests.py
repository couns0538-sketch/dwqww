#!/usr/bin/env python3
"""run_tests.py - tests of the Job C gate tools (read-only on the gate folders; copies go to a scratch folder).

usage: python -I -B run_tests.py [--tmp F:/ospd/jobc/tmp] [--out F:/ospd/jobc/out] [--gates-root F:/forge_push]
                                 [--results-csv D:/grok-pc-data/forge_push/FORGE_RESULTS.csv] [--quick]

(a) replay: gate_replay.py on finished gates listed in FORGE_RESULTS.csv (all three bound sets, cap / H1 / H0,
    a 6000-game gate, a NOT CLEAN row, a TRIAL-ONLY row, a gate with in-flight singles) -> the replay verdict
    must equal the recorded one and the LLR must agree within 0.006 (exit 0 of gate_replay.py).
(b) deliberate failures: copies of a small gate's PGN made truncated / corrupt / unpaired in several ways ->
    gate_replay.py must exit 2 with an error line and print NO verdict.
(c) --verify-moves on a small gate (python-chess replay of every move) must still reproduce the verdict.
(d) the library's LLR against the printed blocks of every row of FORGE_RESULTS.csv that has a Ptnml (no PGN
    needed: pure formula check).
Writes <out>/tests_<stamp>.json and <out>/tests_<stamp>.md (markdown rows for RESULTS.md); never overwrites.
Exit 0 = every test passed, 1 = a failure.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), 'tools')
sys.path.insert(0, TOOLS)
import gatelib as gl  # noqa: E402

PY = sys.executable
REPLAY = os.path.join(TOOLS, 'gate_replay.py')
REPLAY_GATES = [
    # tag, why
    ('gate_sf26bundle14_vs_AL1', '[0,10] cap 1500, LLR -1.68'),
    ('gate72_B4_bundleint_vs_h256e12_confirm', '[0,10] H1 at 2108 games'),
    ('gate68_bundle_g43g33g49_vs_h256e12', '[0,10] H1 with 2 in-flight singles'),
    ('gate71_B3_bundleint_vs_h256e12', '[0,10] H0 at 2160 games'),
    ('gate_stB_lmrttcapall1_vs_AL1', '[0,10] cap 3000 at LLR -2.88 (near the bound)'),
    ('gate69_B1_bundleint_vs_h256e12_confirm', '[0,10] cap 3000 at LLR 2.77 (near the bound)'),
    ('gateR7_ttexclusive_nonreg_vs_r7off', '[-10,0] non-regression H1'),
    ('uhoO30U8soup_v2p4_v2net_vs_AL1lp', '[0,5] H1, net gate with early-stop rule, UHO book'),
    ('uhoE3a_evalmatscale12_r6k_vs_AL1lp', '[0,10] cap 6000 (largest PGN, 36 MB)'),
    ('uhoE3b_evaloptimism40_r6k_vs_AL1lp', '[0,10] H0 at 2360 games, UHO'),
    ('gateR5A_2_corrext1_vs_r5aoff', '[0,10] cap, recorded NOT CLEAN (3 time losses)'),
    ('uhoT2_sf26b14', '[0,10] cap, recorded TRIAL-ONLY'),
    ('gate_npts3_ep06_vs_AL1', '[0,10] early H0 (net far below), 288 games; also used with --verify-moves'),
]
QUICK = ['gate_sf26bundle14_vs_AL1', 'gate68_bundle_g43g33g49_vs_h256e12', 'gate71_B3_bundleint_vs_h256e12',
         'gateR7_ttexclusive_nonreg_vs_r7off', 'uhoO30U8soup_v2p4_v2net_vs_AL1lp', 'gate_npts3_ep06_vs_AL1']


def run_replay(args):
    t0 = time.time()
    p = subprocess.run([PY, '-I', '-B', REPLAY] + args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr, time.time() - t0


def fresh(path):
    """A path that does not exist yet (never overwrite anyone's file)."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f'{base}_{i}{ext}'):
        i += 1
    return f'{base}_{i}{ext}'


def make_failure_inputs(pgn_src, tmp, tag):
    """Copies of a PGN made invalid in several ways. Returns [(name, path, what)]."""
    text = open(pgn_src, encoding='utf-8', errors='replace').read()
    games = text.split('\n\n[Event ')
    out = []

    def write(name, content, what, binary=False):
        p = fresh(os.path.join(tmp, f'{tag}_{name}.pgn'))
        with open(p, 'wb' if binary else 'w', **({} if binary else {'encoding': 'utf-8', 'newline': '\n'})) as f:
            f.write(content)
        out.append((name, p, what))

    # 1 truncated in the middle of a game's movetext (append-mode file cut while a game was being written)
    cut = int(len(text) * 0.61)
    cut = text.find(' ', cut)
    write('truncated', text[:cut], f'file cut at byte {cut} inside a movetext')
    # 2 truncated right after a header block (headers written, movetext not yet)
    i = text.find('\n\n1. ', int(len(text) * 0.5))
    write('truncated_headers', text[:i + 1], 'file ends after a header block')
    # 3 corrupt move token
    g = games[10]
    g2 = re.sub(r'(\d+\. )([KQRBN]?[a-h][1-8]) ', r'\1Zz9 ', g, count=1)
    assert g2 != g
    write('corrupt_move', '\n\n[Event '.join(games[:10] + [g2] + games[11:]), 'game 11: one SAN token replaced by Zz9')
    # 4 result token differs from the Result tag
    g = games[20]
    for a, b in (('1/2-1/2', '1-0'), ('1-0', '0-1'), ('0-1', '1-0')):
        if g.rstrip().endswith(a):
            g2 = g.rstrip()[:-len(a)] + b + '\n'
            break
    write('corrupt_result', '\n\n[Event '.join(games[:20] + [g2] + games[21:]), 'game 21: result token changed, Result tag kept')
    # 5 a move dropped (PlyCount no longer matches)
    g = games[30]
    m = list(re.finditer(r' [KQRBN]?[a-h]?x?[a-h][1-8][+#]? \{[^}]*\}', g))
    mm = m[len(m) // 2]
    g2 = g[:mm.start()] + g[mm.end():]
    write('corrupt_plycount', '\n\n[Event '.join(games[:30] + [g2] + games[31:]), 'game 31: one move with its comment deleted')
    # 6 binary garbage inside the file
    raw = text.encode('utf-8')
    k = len(raw) // 3
    write('corrupt_binary', raw[:k] + b'\x00\x00\xff\xfe\x00' + raw[k + 5:], 'NUL / 0xFF bytes written over the middle', binary=True)
    # 7 unpaired: one whole game removed from the middle (its partner stays)
    write('unpaired', '\n\n[Event '.join(games[:40] + games[41:]), 'game 41 removed, its pair partner kept')
    # 8 a duplicated game (a round with 3 games)
    write('duplicated', '\n\n[Event '.join(games[:50] + [games[50]] + games[50:]), 'game 51 written twice')
    # 9 malformed tag line
    write('corrupt_tag', text.replace('[Round "7"]', '[Round "7"', 1), 'a tag line without its closing bracket')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tmp', default='F:/ospd/jobc/tmp')
    ap.add_argument('--out', default='F:/ospd/jobc/out')
    ap.add_argument('--gates-root', default='F:/forge_push')
    ap.add_argument('--results-csv', default='D:/grok-pc-data/forge_push/FORGE_RESULTS.csv')
    ap.add_argument('--quick', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.tmp, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report = {'stamp_pc_clock': stamp, 'replay': [], 'failures': [], 'verify_moves': None, 'csv_formula': None}
    ok_all = True
    md = []

    # (a) replay
    gates = [g for g in REPLAY_GATES if not a.quick or g[0] in QUICK]
    md.append('| gate | why | recorded | replay | decided at pair (games) | LLR recorded / replay(printed pairs) | singles | exit | s |')
    md.append('|---|---|---|---|---|---|---|---|---|')
    for tag, why in gates:
        d = os.path.join(a.gates_root, tag)
        jp = fresh(os.path.join(a.out, f'replay_{tag}.json'))
        rc, so, se, dt = run_replay([d, '--results-csv', a.results_csv, '--json', jp])
        row = {'gate': tag, 'why': why, 'exit': rc, 'seconds': round(dt, 1), 'json': jp}
        try:
            j = json.load(open(jp))
            row.update({'recorded': (j.get('recorded') or {}).get('verdict'), 'replay': j['replay_verdict'],
                        'pair': j.get('decided_at_pair'), 'games': j.get('decided_at_games'),
                        'llr_rec': (j.get('recorded') or {}).get('llr'), 'llr_replay': j.get('llr_printed_pairs'),
                        'printed_pairs': j.get('printed_pairs'), 'singles': len(j.get('singles') or []), 'mismatches': j.get('mismatches')})
        except (OSError, ValueError) as e:
            row['error'] = f'{e}; stdout tail: {so[-300:]}; stderr: {se[-300:]}'
        row['pass'] = rc == 0 and row.get('replay') == row.get('recorded')
        ok_all &= row['pass']
        report['replay'].append(row)
        md.append(f"| {tag} | {why} | {row.get('recorded')} | {row.get('replay')} | {row.get('pair')} ({row.get('games')}) | "
                  f"{row.get('llr_rec')} / {row.get('llr_replay')} at {row.get('printed_pairs')} | {row.get('singles')} | {rc} {'PASS' if row['pass'] else 'FAIL'} | {row['seconds']} |")
        print(md[-1], flush=True)

    # (b) deliberate failures on a small gate
    small = 'gate_npts3_ep06_vs_AL1'
    d = os.path.join(a.gates_root, small)
    pgn, log, ri, cfg, res = gl.find_gate_files(d)
    md.append('')
    md.append(f'Deliberate failures (copies of {small}/{os.path.basename(pgn)} under {a.tmp}):')
    md.append('')
    md.append('| copy | what was done | with log | exit | error line (stderr) | verdict printed? | result |')
    md.append('|---|---|---|---|---|---|---|')
    for name, path, what in make_failure_inputs(pgn, a.tmp, small):
        for with_log in (True, False):
            args = ['--pgn', path, '--run-info', ri, '--config', cfg] + (['--log', log] if with_log else [])
            rc, so, se, dt = run_replay(args)
            err = [l for l in se.splitlines() if 'ERROR' in l]
            verdict_printed = 'REPLAY VERDICT' in so or 'CHECK:' in so
            passed = rc == 2 and bool(err) and not verdict_printed and 'INVALID INPUT - no verdict' in so
            ok_all &= passed
            report['failures'].append({'copy': name, 'path': path, 'what': what, 'with_log': with_log, 'exit': rc,
                                       'error': err[0] if err else '', 'verdict_printed': verdict_printed, 'pass': passed})
            md.append(f"| {name} | {what} | {'yes' if with_log else 'no'} | {rc} | {(err[0] if err else '(none)')[:150].replace('|', '/')} | "
                      f"{'YES' if verdict_printed else 'no'} | {'PASS' if passed else 'FAIL'} |")
            print(md[-1], flush=True)

    # (c) --verify-moves on the small gate
    jp = fresh(os.path.join(a.out, f'replay_{small}_verify.json'))
    rc, so, se, dt = run_replay([d, '--results-csv', a.results_csv, '--verify-moves', '--json', jp])
    try:
        j = json.load(open(jp))
        vm = {'gate': small, 'exit': rc, 'seconds': round(dt, 1), 'replay': j['replay_verdict'], 'recorded': (j.get('recorded') or {}).get('verdict'),
              'games': j['games_in_pgn'], 'pass': rc == 0}
    except (OSError, ValueError) as e:
        vm = {'gate': small, 'exit': rc, 'pass': False, 'error': str(e)}
    ok_all &= vm['pass']
    report['verify_moves'] = vm
    md.append('')
    md.append(f"--verify-moves on {small}: exit {rc}, {vm.get('games')} games replayed move by move with python-chess in {vm.get('seconds')} s, "
              f"verdict {vm.get('replay')} vs recorded {vm.get('recorded')}: {'PASS' if vm['pass'] else 'FAIL'}")
    print(md[-1], flush=True)

    # (d) formula check against every FORGE_RESULTS.csv row with a Ptnml
    rows = gl.load_results_csv(a.results_csv)
    n = bad = 0
    worst = 0.0
    bad_rows = []
    for tag, r in rows.items():
        if not r.get('ptnml', '').strip():
            continue
        pt = [int(x) for x in r['ptnml'].split()]
        # the csv does not state the nElo bounds: take them from the gate folder (config.json / RUN_INFO), else the
        # verdict text, else assume [0,10] (the queue default) and say so
        e0 = e1 = None
        for root in (a.gates_root, 'D:/grok-pc-data/forge_push'):
            d = os.path.join(root, tag)
            if os.path.isdir(d):
                _, _, ri, cfg, _ = gl.find_gate_files(d)
                try:
                    b = gl.gate_bounds(gl.load_run_info(ri), gl.load_config(cfg), None)
                except gl.GateError:
                    b = None
                if b:
                    e0, e1 = b[0], b[1]
                    break
        txt = r.get('verdict', '')
        m = re.search(r'SPRT \[(-?[\d.]+),\s*(-?[\d.]+)\]', txt)
        if e0 is None and m:
            e0, e1 = float(m.group(1)), float(m.group(2))
        elif e0 is None:
            e0, e1 = 0.0, 10.0
        llr = gl.exact_llr(pt, e0, e1)
        st = gl.ptnml_stats(pt)
        n += 1
        d_llr = abs(llr - float(r['llr'])) if llr is not None else 9
        d_elo = abs(st['elo'] - float(r['elo'])) if st else 9
        d_nelo = abs(st['nelo'] - float(r['nelo'])) if st else 9
        worst = max(worst, d_llr)
        if d_llr > 0.006 or d_elo > 0.006 or d_nelo > 0.006:
            bad += 1
            bad_rows.append({'tag': tag, 'bounds': [e0, e1], 'llr_csv': r['llr'], 'llr_lib': round(llr, 4) if llr is not None else None,
                             'elo_csv': r['elo'], 'elo_lib': round(st['elo'], 4) if st else None})
    report['csv_formula'] = {'rows': n, 'bad': bad, 'worst_llr_diff': round(worst, 4), 'bad_rows': bad_rows}
    md.append('')
    md.append(f'Formula check on FORGE_RESULTS.csv: {n} rows with a Ptnml, LLR / Elo / nElo recomputed from the Ptnml: {bad} differ by more than 0.006 '
              f'(worst LLR difference {worst:.4f}){": " + str(bad_rows) if bad_rows else ""}')
    print(md[-1], flush=True)
    ok_all &= bad == 0

    jp = fresh(os.path.join(a.out, f'tests_{stamp}.json'))
    with open(jp, 'w', newline='\n') as f:
        json.dump(report, f, indent=1)
        f.write('\n')
    mp = fresh(os.path.join(a.out, f'tests_{stamp}.md'))
    with open(mp, 'w', newline='\n', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print(f'\nrun_tests: {"ALL PASS" if ok_all else "FAILURES"}; report {jp}; markdown {mp}')
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
