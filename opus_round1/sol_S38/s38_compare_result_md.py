#!/usr/bin/env python3
"""s38_compare_result_md.py (S38, opus 2026-10-27): compare the audit tool's JSON for real gates with two independent
producers: the PC driver's RESULT.md (forge_queue.ps1: time losses, crashes/illegal, 'Warning;' lines, avg PGN depth
and move count per engine, games) and GATE_RESULTS.csv (gate_results.ps1: time_losses, crashes).
Games: the tool's PGN count must equal fastchess's 'Finished game' lines; RESULT.md quotes the last 'Results of' block,
which counts complete pairs only, so after an early SPRT stop it may be lower by the orphan games still in flight
(at most concurrency - 1 = 7 on the PC); that difference is printed, not treated as a mismatch.
Usage: s38_compare_result_md.py --csv GATE_RESULTS.csv  TAG=REPORT.json=RESULT.md [...]   (read-only; prints a table)"""
import argparse
import csv
import json
import re
import sys


def parse_result_md(path):
    t = open(path, encoding='utf-8-sig', errors='replace').read()
    out = {}
    m = re.search(r"Time losses: (\d+)\s+Crashes/disconnects/stalls/illegal: (\d+)\s+fastchess 'Warning;' lines: (\d+)", t)
    if m:
        out['tl'], out['crash'], out['warn'] = (int(x) for x in m.groups())
    m = re.search(r'Games: (\d+)', t)
    if m:
        out['games'] = int(m.group(1))
    m = re.search(r'Avg search depth \(PGN comments, non-book moves\): (.*)', t)
    if m:
        out['depth'] = {n: (float(d), int(c)) for n, d, c in re.findall(r'(\S+): avg depth ([\d.]+) over (\d+) moves', m.group(1))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv')
    ap.add_argument('items', nargs='+')
    a = ap.parse_args()
    rows = {}
    if a.csv:
        for r in csv.DictReader(open(a.csv, encoding='utf-8-sig')):
            rows.setdefault(r['tag'], r)
    allok = True
    print('| gate | games PGN / Finished lines / RESULT block (orphans) | TL tool/RESULT/CSV | crash+illegal tool/RESULT/CSV | Warning; tool/RESULT | depth mean, moves: tool vs RESULT | all equal |')
    print('|---|---|---|---|---|---|---|')
    for it in a.items:
        tag, rep, res = it.split('=', 2)
        j = json.load(open(rep, encoding='utf-8'))
        r = parse_result_md(res)
        eng = j['engines']
        tl = sum(e['events']['tl'] for e in eng.values())
        cr = sum(e['events']['crash'] + e['events']['illegal'] for e in eng.values())
        warn = j['fastchess_log']['warning_lines'] if j.get('fastchess_log') else None
        c = rows.get(tag, {})
        ctl, ccr = c.get('time_losses', 'n/a'), c.get('crashes', 'n/a')
        dep_ok, dep_txt = True, []
        for n, (d, cnt) in sorted(r.get('depth', {}).items()):
            te = eng.get(n)
            ok = te is not None and te['depth']['mean'] == d and te['engine_moves'] == cnt
            dep_ok &= ok
            dep_txt.append(f'{n}: {te["depth"]["mean"] if te else None}/{te["engine_moves"] if te else None} vs {d}/{cnt}')
        fin = j['fastchess_log']['finished_games'] if j.get('fastchess_log') else None
        orphans = j['pgn']['games'] - r['games'] if 'games' in r else None
        games_ok = fin == j['pgn']['games'] and orphans is not None and 0 <= orphans <= 7
        ok = (games_ok and tl == r.get('tl') and cr == r.get('crash') and warn == r.get('warn') and dep_ok
              and bool(r.get('depth')) and (ctl == 'n/a' or int(ctl) == tl) and (ccr == 'n/a' or int(ccr) == cr))
        allok &= ok
        print(f'| {tag} | {j["pgn"]["games"]} / {fin} / {r.get("games")} ({orphans}) | {tl}/{r.get("tl")}/{ctl} | {cr}/{r.get("crash")}/{ccr} | '
              f'{warn}/{r.get("warn")} | {"; ".join(dep_txt)} | {"yes" if ok else "NO"} |')
    print(f'\nall gates equal: {allok}')
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
