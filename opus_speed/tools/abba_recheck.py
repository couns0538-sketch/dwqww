#!/usr/bin/env python3
"""abba_recheck.py - recompute abba.ps1 summaries from their runs.csv, independently (speed job, own code).

usage: python -I -B abba_recheck.py <abba dir> [<abba dir> ...]
       python -I -B abba_recheck.py --pool <abba dir> <abba dir> [...]   (same two exes in every run)
Per folder: reads runs.csv (columns round, order, md5, nodes, nps, cpu_nps), checks that every A row has one md5 and
one node count and every B row another, forms the per-round ratio (B1 + B2) / (A1 + A2) for wall (nps) and cpu
(cpu_nps) exactly as abba.ps1 does, and recomputes the median and the 95 % two-sided Student-t interval of the mean
log ratio with an exact t quantile (numeric integration of the t density; abba.ps1 uses a short series). Applies the
WIN rule (interval low end > 1.000 and median >= 1.010) and compares with summary.txt in the same folder.
Prints one line per folder and metric; exit 1 on any value that differs by more than 0.0001 or a verdict that
changes. --pool joins the per-round ratios of several runs of the same pair (a borderline result and its re-time)
and reports the pooled median, interval and verdict, so a re-time is never read on its own. Reads files only.
"""
import csv
import math
import pathlib
import re
import statistics
import sys

RX = re.compile(r'^(wall|cpu) \(.*?\): B/A median ([0-9.]+) \([-+0-9.]+%\), 95% t-interval \[([0-9.]+), ([0-9.]+)\]')
RXV = re.compile(r'VERDICT wall (WIN|NO-WIN) / cpu (WIN|NO-WIN)')


def t_pdf(x, df):
    c = math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
    return math.exp(c - (df + 1) / 2 * math.log1p(x * x / df))


def t_cdf(x, df, steps=4000):
    # Simpson's rule on [0, x]; the density is symmetric, so cdf = 0.5 + integral
    h = x / steps
    s = t_pdf(0.0, df) + t_pdf(x, df)
    for i in range(1, steps):
        s += (4 if i % 2 else 2) * t_pdf(i * h, df)
    return 0.5 + s * h / 3


def t975(df):
    lo, hi = 0.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < 0.975:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def stats(ratios):
    n = len(ratios)
    logs = [math.log(r) for r in ratios]
    mean = sum(logs) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in logs) / (n - 1))
    half = t975(n - 1) * sd / math.sqrt(n)
    return statistics.median(ratios), math.exp(mean - half), math.exp(mean + half), 100 * sd


def check(folder):
    folder = pathlib.Path(folder)
    with open(folder / 'runs.csv', newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    label = f'{folder.parent.name}/{folder.name}'
    bad = 0
    ids = {}
    for r in rows:
        arm = r['order'].split(':')[1]
        ids.setdefault(arm, set()).add((r['md5'], r['nodes']))
    for arm, s in sorted(ids.items()):
        if len(s) != 1:
            print(f'{label}: DIFF arm {arm} has {len(s)} (md5, nodes) pairs: {sorted(s)}')
            bad += 1
    summary = (folder / 'summary.txt').read_text(encoding='utf-8', errors='replace').splitlines()
    want = {}
    verdict = None
    for line in summary:
        m = RX.match(line)
        if m:
            want[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
        v = RXV.search(line)
        if v:
            verdict = {'wall': v.group(1), 'cpu': v.group(2)}
    for metric, col in (('wall', 'nps'), ('cpu', 'cpu_nps')):
        by = {}
        for r in rows:
            arm = r['order'].split(':')[1]
            d = by.setdefault(int(r['round']), {'A': [], 'B': []})
            d[arm].append(float(r[col]))
        ratios = [sum(d['B']) / sum(d['A']) for _, d in sorted(by.items()) if len(d['A']) == 2 and len(d['B']) == 2]
        med, lo, hi, sdp = stats(ratios)
        mine = 'WIN' if (lo > 1.0 and med >= 1.010) else 'NO-WIN'
        if metric not in want or verdict is None:
            print(f'{label} {metric}: summary line missing')
            bad += 1
            continue
        w = want[metric]
        diffs = [abs(a - b) for a, b in zip((med, lo, hi), w)]
        ok = max(diffs) <= 0.0001 and mine == verdict[metric]
        bad += 0 if ok else 1
        print(f'{label} {metric}: n={len(ratios)} median {med:.4f} [{lo:.4f}, {hi:.4f}] sd {sdp:.2f}% -> {mine}; '
              f'summary {w[0]:.4f} [{w[1]:.4f}, {w[2]:.4f}] -> {verdict[metric]}; '
              f'max diff {max(diffs):.5f} {"OK" if ok else "DIFF"}')
    return bad


def pool(folders):
    """Pool the per-round ratios of several runs of the SAME pair (same A md5 and B md5 in every run)."""
    allrows = []
    for f in folders:
        with open(pathlib.Path(f) / 'runs.csv', newline='', encoding='utf-8') as fh:
            allrows.append((f, list(csv.DictReader(fh))))
    pairs = set()
    for f, rows in allrows:
        a = {r['md5'] for r in rows if r['order'].endswith(':A')}
        b = {r['md5'] for r in rows if r['order'].endswith(':B')}
        pairs.add((tuple(sorted(a)), tuple(sorted(b))))
    if len(pairs) != 1:
        print('POOL refused: the runs do not time the same two exes:', sorted(pairs))
        return 1
    for metric, col in (('wall', 'nps'), ('cpu', 'cpu_nps')):
        ratios = []
        for f, rows in allrows:
            by = {}
            for r in rows:
                arm = r['order'].split(':')[1]
                d = by.setdefault(int(r['round']), {'A': [], 'B': []})
                d[arm].append(float(r[col]))
            ratios += [sum(d['B']) / sum(d['A']) for _, d in sorted(by.items()) if len(d['A']) == 2 and len(d['B']) == 2]
        med, lo, hi, sdp = stats(ratios)
        mine = 'WIN' if (lo > 1.0 and med >= 1.010) else 'NO-WIN'
        print(f'POOL {metric}: n={len(ratios)} rounds from {len(folders)} runs, median {med:.4f} ({100 * (med - 1):+.2f}%) '
              f'95% t-interval [{lo:.4f}, {hi:.4f}] sd/round {sdp:.2f}% -> {mine}')
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == '--pool':
        return pool(args[1:])
    for df in (9, 15):
        print(f't975(df={df}) = {t975(df):.4f}')
    bad = sum(check(f) for f in args)
    print('RESULT', 'PASS' if bad == 0 else f'FAIL ({bad})')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
