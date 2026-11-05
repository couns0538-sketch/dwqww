#!/usr/bin/env python3
"""tried_gates.py - compact "already gated" list from the crew's FORGE_RESULTS.csv (read-only).

usage: python -I -B tried_gates.py [--grep REGEX] [--csv PATH]
One line per gate: gate | tag | options | games | Elo | nElo | LLR | verdict (first words). Use it before proposing an
idea: grep the option or idea name (e.g. --grep 'corr|lmr').
"""
import argparse
import csv
import re
import sys

DEFAULT = 'C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv'


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('--grep')
    ap.add_argument('--csv', default=DEFAULT)
    a = ap.parse_args()
    rx = re.compile(a.grep, re.I) if a.grep else None
    with open(a.csv, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    shown = 0
    for r in rows:
        line = ' | '.join([r['gate'], r['tag'], r['cand_options'] or '-', r['games'], r['elo'], r['nelo'], r['llr'],
                           ' '.join((r['verdict'] or '').split()[:4])])
        if rx and not rx.search(line + ' ' + r['candidate'] + ' ' + r['cand_exe']):
            continue
        print(line)
        shown += 1
    print(f'# {shown} of {len(rows)} gates shown ({a.csv})')


if __name__ == '__main__':
    main()
