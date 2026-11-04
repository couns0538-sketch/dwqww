#!/usr/bin/env python3
"""o30_runs.py - Opus 30-h job: one table of every CPU fine-tune run under D:\\o30\\runs (read only).
usage: python -I -B o30_runs.py [--root D:\\o30\\runs] [--all]   (--all: every checkpoint row, not only the last)
Per run: config (init, king map, output buckets, lr / output-lr multiplier, positions planned), last checkpoint
(time, positions, S31 b0.6 / b1.0, jobA b0.6) and the deltas against the lock net (0.014310027 / 0.004572428 /
0.013272058), best S31 b0.6, last training rate (positions/s from train.csv).
"""
import argparse
import csv
import json
import os

LOCK = {'s16_b06': 0.014310027, 's16_b10': 0.004572428, 'joba_b06': 0.013272058}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'D:\o30\runs')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    print('| run | init / kb / ob | lr (out x) | positions | S31 b0.6 (vs lock) | S31 b1.0 (vs lock) | jobA b0.6 (vs lock) | best S31 b0.6 | pos/s | last |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for name in sorted(os.listdir(a.root)):
        run = os.path.join(a.root, name)
        cfgp, valp = os.path.join(run, 'config.json'), os.path.join(run, 'val.csv')
        if not (os.path.isfile(cfgp) and os.path.isfile(valp)):
            continue
        cfg = json.load(open(cfgp))
        rows = list(csv.DictReader(open(valp)))
        if not rows:
            continue
        rate = ''
        tp = os.path.join(run, 'train.csv')
        if os.path.isfile(tp):
            t = list(csv.DictReader(open(tp)))
            if t:
                rate = t[-1]['pos_per_s']
        best = min(float(r['s16_b06']) for r in rows)
        for r in (rows if a.all else rows[-1:]):
            d = lambda k: f"{float(r[k]):.7f} ({float(r[k]) - LOCK[k]:+.1e})"
            print(f"| {name} | {cfg['init'] if len(cfg['init']) < 12 else 'file'} / {cfg['kb_map']}{'m' if cfg.get('mirror') else ''} / {cfg['ob']} "
                  f"| {cfg['lr']:g} (x{cfg.get('lr_out_mult', 1.0):g}) | {float(r['positions']):.3g} / {float(cfg['positions']):.3g} "
                  f"| {d('s16_b06')} | {d('s16_b10')} | {d('joba_b06')} | {best:.7f} ({best - LOCK['s16_b06']:+.1e}) | {rate} | {r['time']} {r['tag']} |")


if __name__ == '__main__':
    main()
