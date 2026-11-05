#!/usr/bin/env python3
"""combine_sanity.py <fastchess log> [<fastchess log> ...] - Opus 30-h job: pool the game pairs of several sanity matches
of ONE net (e.g. the first match + extra games on other openings) from the last "Ptnml(0-2): [...]" line of each log and
print the pooled pentanomial, score, Elo and its 95 % interval (normal approximation on the pair scores, as fastchess
prints it) - SANITY ONLY. With one log it must reproduce that log's own "Elo:" line (self-check printed). Own code."""
import math
import re
import sys


def ptnml(path):
    last = None
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'Ptnml\(0-2\): \[(\d+), (\d+), (\d+), (\d+), (\d+)\]', line)
        if m:
            last = [int(x) for x in m.groups()]
    if last is None:
        sys.exit(f'{path}: no Ptnml(0-2) line')
    return last


def elo(score):
    return -400.0 * math.log10(1.0 / score - 1.0)


def summary(p):
    n = sum(p)
    vals = [0.0, 0.25, 0.5, 0.75, 1.0]
    mean = sum(v * k for v, k in zip(vals, p)) / n
    var = sum(k * (v - mean) ** 2 for v, k in zip(vals, p)) / n
    se = math.sqrt(var / n)
    lo, hi = elo(mean - 1.959964 * se), elo(mean + 1.959964 * se)
    return n, mean, elo(mean), (hi - lo) / 2


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    total = [0] * 5
    for path in sys.argv[1:]:
        p = ptnml(path)
        n, mean, e, pm = summary(p)
        own = ''
        for line in open(path, encoding='utf-8', errors='replace'):
            if line.startswith('Elo:'):
                own = line.strip().split(', nElo')[0]
        print(f'{path}: Ptnml {p} pairs {n} score {mean * 100:.2f} % Elo {e:+.2f} +/- {pm:.2f} (fastchess: {own})')
        total = [a + b for a, b in zip(total, p)]
    n, mean, e, pm = summary(total)
    print(f'POOLED: Ptnml {total} pairs {n} games {2 * n} score {mean * 100:.2f} % Elo {e:+.2f} +/- {pm:.2f} (SANITY ONLY)')


if __name__ == '__main__':
    main()
