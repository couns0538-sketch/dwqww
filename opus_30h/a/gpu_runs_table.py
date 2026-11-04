#!/usr/bin/env python3
"""gpu_runs_table.py <run> [<run> ...] - Opus 30-h job, GPU window: Markdown table of every scored checkpoint of the
named runs (D:\\o30\\gpu\\<run>_scores.tsv from gpu_ckpt_watch.sh): positions trained (superbatch x 1024 x 16384),
S31 b0.6 and its paired difference / z vs the lock net, jobA val b0.6 and its paired difference / z, and the offline
rule written before any result (S31 at least 2e-5 below the lock AND paired jobA z <= +2). Read-only; own code."""
import csv
import sys

POS_PER_SB = 1024 * 16384


def main():
    print('| run | checkpoint | positions | S31 b0.6 | S31 vs lock | z | jobA b0.6 | jobA vs lock | z | rule |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for run in sys.argv[1:]:
        with open(f'D:/o30/gpu/{run}_scores.tsv', encoding='utf-8') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                sb = int(r['ckpt'].rsplit('-', 1)[1])
                ds, zs, dj, zj = (float(r[k]) for k in ('paired_s31', 'z_s31', 'paired_jobA', 'z_jobA'))
                rule = 'PASS' if ds <= -2e-5 and zj <= 2 else 'FAIL'
                print(f"| {run} | {sb} | {sb * POS_PER_SB / 1e9:.2f}G | {float(r['s31_b06']):.6f} | {ds:+.2e} | {zs:+.1f} "
                      f"| {float(r['jobA_b06']):.6f} | {dj:+.2e} | {zj:+.2f} | {rule} |")


if __name__ == '__main__':
    main()
