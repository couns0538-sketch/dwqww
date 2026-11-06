"""qa_verdict.py - QA's WIN rule for one candidate ABBA run against the A/A run of the same block.

usage: python -I -B qa_verdict.py <candidate ABBA dir> <A/A dir>
QA rule (2026-11-05 23:0x, Couns-approved): WIN only if the candidate's 95 % interval lies fully above 1.000 (low end >
1.000) AND its median gain beats half the width of the A/A's 95 % interval (median - 1 > (hi - lo) / 2 of the A/A).
Applied to the wall metric (the verdict) and, the same way with the A/A's cpu width, to the CPU-time metric (a wall WIN
next to a cpu NO-WIN is a contradiction, not a lock-style WIN). Interval = exp(mean +- t975(n-1) * sd / sqrt(n)) of
the per-round log ratios (abba.ps1 / abba_recheck.py). Prints one line per metric; exit 0 always (it only reports).
(Speed hunt vs trial_w6, own code.)
"""
import collections
import csv
import math
import pathlib
import statistics
import sys

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def ratios(run_dir, col):
    rows = list(csv.DictReader(open(pathlib.Path(run_dir) / 'runs.csv', encoding='utf-8')))
    by = collections.defaultdict(lambda: {'A': [], 'B': []})
    for r in rows:
        by[int(r['round'])][r['order'].split(':')[1]].append(float(r[col]))
    return [sum(by[k]['B']) / sum(by[k]['A']) for k in sorted(by) if by[k]['A'] and by[k]['B']]


def stats(rs):
    logs = [math.log(r) for r in rs]
    n = len(logs)
    mean = sum(logs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in logs) / (n - 1))
    half = T975.get(n - 1, 1.96) * sd / math.sqrt(n)
    return statistics.median(rs), math.exp(mean - half), math.exp(mean + half), 100 * sd


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    cand, aa = sys.argv[1], sys.argv[2]
    out = {}
    for col, label in (('nps', 'wall'), ('cpu_nps', 'cpu')):
        cm, clo, chi, csd = stats(ratios(cand, col))
        am, alo, ahi, asd = stats(ratios(aa, col))
        need = 100 * (ahi - alo) / 2
        win = clo > 1.0 and 100 * (cm - 1) > need
        out[label] = win
        print('qa_verdict %s %s: median %.4f (%+.2f %%) [%.4f, %.4f] sd %.2f %%; A/A %s median %.4f width %.2f %% -> need '
              'low > 1.000 and gain > %.2f %% -> %s' % (pathlib.Path(cand).name, label, cm, 100 * (cm - 1), clo, chi, csd,
                                                       pathlib.Path(aa).name, am, 100 * (ahi - alo), need,
                                                       'WIN' if win else 'NO-WIN'))
    if out['wall'] and not out['cpu']:
        print('qa_verdict: wall WIN but cpu NO-WIN = contradiction, not a lock-style WIN')
    print('qa_verdict: VERDICT %s' % ('WIN' if out['wall'] and out['cpu'] else 'NO-WIN'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
