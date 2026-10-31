#!/usr/bin/env python3
"""lineset_diff.py - compare the +/- line sets of two unified diffs (R13 port proof).

usage: python -I -B lineset_diff.py ORIGINAL.patch PORT.patch [--exclude-path REGEX ...] [--json OUT]

Collects every added (+) and removed (-) line of each patch (file headers '+++'/'---' and 'diff --git'/'index' lines
are skipped), normalises whitespace (strip, collapse runs of blanks; CRLF -> LF), and compares the two multisets.
Prints the counts and the lines only in ORIGINAL / only in PORT with their file names, so each difference can be
listed and explained (context-only differences do not show: context lines are not compared).
Exit 0 when both multisets are equal, 1 otherwise.
"""
import argparse
import collections
import json
import re
import sys


def collect(path, excludes):
    lines = collections.Counter()
    where = collections.defaultdict(set)
    cur = None
    with open(path, 'rb') as fh:
        for raw in fh:
            s = raw.decode('utf-8', 'replace').rstrip('\r\n')
            if s.startswith('diff --git ') or s.startswith('index ') or s.startswith('new file mode') \
                    or s.startswith('deleted file mode') or s.startswith('similarity') or s.startswith('rename '):
                continue
            if s.startswith('+++ '):
                p = s[4:].split('\t')[0]
                cur = p[2:] if p.startswith(('a/', 'b/')) else p
                continue
            if s.startswith('--- '):
                continue
            if s.startswith('\\ No newline'):
                continue
            if cur is None or any(re.search(x, cur) for x in excludes):
                continue
            if s[:1] in '+-' and not s.startswith('@@'):
                key = s[0] + ' ' + ' '.join(s[1:].split())
                lines[key] += 1
                where[key].add(cur)
    return lines, where


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('original')
    ap.add_argument('port')
    ap.add_argument('--exclude-path', action='append', default=[], help='regex of file paths to ignore (both sides)')
    ap.add_argument('--json')
    a = ap.parse_args()
    lo, wo = collect(a.original, a.exclude_path)
    lp, wp = collect(a.port, a.exclude_path)
    only_o = lo - lp
    only_p = lp - lo
    print(f'original: {sum(lo.values())} +/- lines; port: {sum(lp.values())} +/- lines')
    print(f'only in original: {sum(only_o.values())}; only in port: {sum(only_p.values())}')
    for title, c, w in (('ONLY IN ORIGINAL', only_o, wo), ('ONLY IN PORT', only_p, wp)):
        if c:
            print(f'--- {title}')
            for k in sorted(c):
                print(f'{c[k]}x [{",".join(sorted(w[k]))}] {k}')
    if a.json:
        with open(a.json, 'w', newline='\n') as fh:
            json.dump({'original': a.original, 'port': a.port, 'only_in_original': dict(only_o),
                       'only_in_port': dict(only_p), 'equal': not only_o and not only_p}, fh, indent=1)
    print('LINESET EQUAL' if not only_o and not only_p else 'LINESET DIFFERS')
    return 0 if not only_o and not only_p else 1


if __name__ == '__main__':
    sys.exit(main())
