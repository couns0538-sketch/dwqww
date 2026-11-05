#!/usr/bin/env python3
"""w2_tables.py - Opus 30-h job: the Markdown tables of GPU window 2 for the final report, from the evidence files only:
  1 runs: the final checkpoint of every window-2 run (C:/o30g/gpu/<run>_scores.tsv or D:/o30/gpu/...), its layout,
    superbatches, lr (from the guard log's trainer command), S31 / jobA paired vs the lock net, the offline rule;
  2 sanity matches: every <net>/sanity*/sanity.log under D:/o30/nets (latest fastchess summary, planned games, exe) plus
    the v2p4 control (D:/o30/control/lockkb4_v2p4) and any extra folder given with --extra name=path.
Read-only; prints Markdown (LF). Own code."""
import argparse
import csv
import glob
import json
import os
import re
import sys

RUNS = ['r6_kb8lr3', 'r7_kb16short', 'r8_kb32short', 'r9_kb16seed', 'r10_kb8seed2', 'r11_kb16long', 'r12_kb8long',
        'r13_kb16m400lr15', 'r14_kb8m400lr15', 'r15_kb8long2', 'r16_kb8s200lr1', 'r17_kb8m300', 'r18_kb8s200lr3',
        'r19_kb8m300b', 'r20_kb8s100']
LAYOUT = {'rank4': 'KB4', 'rank4x2': 'KB8', 'rank4x4': 'KB16', 'rank4x8': 'KB32', 'one': 'KB1'}


def run_row(run):
    for root in ('C:/o30g/gpu', 'D:/o30/gpu'):
        tsv = f'{root}/{run}_scores.tsv'
        if os.path.isfile(tsv):
            break
    else:
        return None
    rows = list(csv.DictReader(open(tsv, encoding='utf-8'), delimiter='\t'))
    if not rows:
        return f'| {run} | no scored checkpoint | | | | | |'
    r = rows[-1]
    cmd = ''
    glog = f'{root}/{run}.guard.log'
    if os.path.isfile(glog):
        cmd = next((l for l in open(glog, encoding='utf-8') if 'start trainer' in l), '')
    m = re.search(r' r \S+ \S+ (\S+) (\d) (\d+) (\d+) (\d+) (\d+) (\d+) ([\d.e-]+) ([\d.]+) (\d+)', cmd)
    kb, sb, lr = (LAYOUT.get(m.group(1), m.group(1)), m.group(4), m.group(8)) if m else ('?', '?', '?')
    end = 'ended' if os.path.isfile(glog) and ' end: ' in open(glog, encoding='utf-8').read() else 'RUNNING'
    ck = r['ckpt'].rsplit('-', 1)[1]
    ds, zs, dj, zj = (float(r[k]) for k in ('paired_s31', 'z_s31', 'paired_jobA', 'z_jobA'))
    rule = 'PASS' if ds <= -2e-5 and zj <= 2 else 'FAIL'
    return (f'| {run} | {kb} | {sb} / lr {float(lr):.1e} | {ck} ({end}) | {ds:+.2e} ({zs:+.1f}) | {dj:+.2e} ({zj:+.2f}) '
            f'| {rule} |')


def sanity(path):
    log = path
    if os.path.isdir(path):   # sanity.log, or the folder's own <name>.log (the v2p4 rematches: sanity_v2p4.log)
        logs = [os.path.join(path, 'sanity.log')] + sorted(glob.glob(os.path.join(path, '*.log')))
        log = next((l for l in logs if os.path.isfile(l)), '')
    if not os.path.isfile(log):
        return None
    games = elo = ''
    for line in open(log, encoding='utf-8', errors='replace'):
        if line.startswith('Games:'):
            games = line.strip()
        elif line.startswith('Elo:'):
            elo = line.strip().split(', nElo')[0]
    planned = '?'
    ri = os.path.join(os.path.dirname(log), 'RUN_INFO.json')
    if os.path.isfile(ri):
        planned = json.load(open(ri, encoding='utf-8-sig')).get('games', '?')
    return games, elo, planned


def main():
    sys.stdout.reconfigure(newline=chr(10))
    ap = argparse.ArgumentParser()
    ap.add_argument('--extra', action='append', default=[], help='name=folder with a sanity.log')
    a = ap.parse_args()
    print('| run | layout | superbatches / lr | final checkpoint | S31 vs lock (z) | jobA vs lock (z) | rule |')
    print('|---|---|---|---|---|---|---|')
    for run in RUNS:
        row = run_row(run)
        if row:
            print(row)
    print()
    print('| net | games (W / L / D, points) | Elo +/- (SANITY ONLY) | planned |')
    print('|---|---|---|---|')
    items = [('CONTROL: v2p4 + lock-as-KB4 (identity)', 'D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.log')]
    for d in sorted(glob.glob('D:/o30/nets/*/sanity*')):
        if not os.path.isdir(d) or os.path.basename(os.path.dirname(d)).startswith('test_'):
            continue
        items.append((os.path.basename(os.path.dirname(d)) + ('' if d.endswith('sanity') else ' (' + os.path.basename(d) + ')'), d))
    items += [tuple(e.split('=', 1)) for e in a.extra]
    for name, path in items:
        s = sanity(path)
        if s:
            print(f'| {name} | {s[0].replace("Games: ", "")} | {s[1].replace("Elo: ", "")} | {s[2]} |')


if __name__ == '__main__':
    main()
