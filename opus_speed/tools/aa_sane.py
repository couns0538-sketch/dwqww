"""aa_sane.py - is an A/A run (abba.ps1 runs.csv, the lock against itself) sane by QA's rule?

usage: python -I -B aa_sane.py <runs.csv> [--median-pct 0.5] [--width-pct 4.0]
QA rule (2026-11-05 23:0x, Couns-approved): SANE = |median - 1| <= 0.5 % AND the width of the 95 % interval of the
round ratios <= 4.0 % ("range" in the brief = this width, not the per-round max - min). The interval is abba.ps1's:
exp(mean +- t975(n-1) * sd / sqrt(n)) of the per-round log ratios, ratio = (nps B1 + nps B2) / (nps A1 + nps A2). The
per-round spread (max - min of the ratios) is printed as information only. Exit 0 sane, 1 not sane, 2 unreadable.
(Speed hunt vs trial_w6, own code.)
"""
import collections
import csv
import math
import statistics
import sys

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def interval(ratios):
    logs = [math.log(r) for r in ratios]
    n = len(logs)
    mean = sum(logs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in logs) / (n - 1))
    half = T975.get(n - 1, 1.96) * sd / math.sqrt(n)
    return math.exp(mean - half), math.exp(mean + half), 100 * sd


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    med_lim = float(args[args.index('--median-pct') + 1]) if '--median-pct' in args else 0.5
    wid_lim = float(args[args.index('--width-pct') + 1]) if '--width-pct' in args else 4.0
    try:
        rows = list(csv.DictReader(open(path, encoding='utf-8')))
        by = collections.defaultdict(lambda: {'A': [], 'B': []})
        for r in rows:
            by[int(r['round'])][r['order'].split(':')[1]].append(float(r['nps']))
        ratios = [sum(by[k]['B']) / sum(by[k]['A']) for k in sorted(by) if by[k]['A'] and by[k]['B']]
    except (OSError, KeyError, ValueError, ZeroDivisionError) as e:
        print('aa_sane: unreadable %s (%s)' % (path, e))
        return 2
    if len(ratios) < 4:
        print('aa_sane: only %d rounds in %s' % (len(ratios), path))
        return 2
    med = statistics.median(ratios)
    lo, hi, sd = interval(ratios)
    width = 100 * (hi - lo)
    spread = 100 * (max(ratios) - min(ratios))
    sane = abs(med - 1.0) * 100 <= med_lim and width <= wid_lim
    print('aa_sane: %s rounds %d median %.4f (%+.2f %%) 95 %% [%.4f, %.4f] width %.2f %% sd %.2f %% -> %s '
          '(QA rule |median| <= %.1f %%, width <= %.1f %%; per-round spread %.2f %% = information)'
          % (path, len(ratios), med, (med - 1) * 100, lo, hi, width, sd, 'SANE' if sane else 'NOT SANE', med_lim, wid_lim,
             spread))
    return 0 if sane else 1


if __name__ == '__main__':
    sys.exit(main())
