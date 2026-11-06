"""aa_sane.py - is an A/A run (abba.ps1 runs.csv, the lock against itself) sane by the hunt brief's rule?

usage: python -I -B aa_sane.py <runs.csv> [--median-pct 1.0] [--range-pct 4.0]
Per round: ratio = (nps B1 + nps B2) / (nps A1 + nps A2), as abba.ps1 computes it. Sane = the median of the round
ratios within +-median-pct of 1 and the per-round range (max - min of the round ratios) at most range-pct.
Prints the numbers; exit 0 sane, 1 not sane, 2 unreadable input. (Speed hunt vs trial_w6, own code.)
"""
import collections
import csv
import statistics
import sys


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    med_lim = float(args[args.index('--median-pct') + 1]) if '--median-pct' in args else 1.0
    rng_lim = float(args[args.index('--range-pct') + 1]) if '--range-pct' in args else 4.0
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
    rng = max(ratios) - min(ratios)
    sane = abs(med - 1.0) * 100 <= med_lim and rng * 100 <= rng_lim
    print('aa_sane: %s rounds %d median %.4f (%+.2f %%) per-round range %.2f %% -> %s (limits +-%.1f %%, %.1f %%)'
          % (path, len(ratios), med, (med - 1) * 100, rng * 100, 'SANE' if sane else 'NOT SANE', med_lim, rng_lim))
    return 0 if sane else 1


if __name__ == '__main__':
    sys.exit(main())
