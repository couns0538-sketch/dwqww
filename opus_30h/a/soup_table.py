#!/usr/bin/env python3
"""soup_table.py [soups dir] - Opus 30-h job: Markdown table of every weight soup scored by soup_score.sh: name,
members (from <name>.soup.txt: the run folder of each input, or the expanded copy's file name), S31 b0.6 paired
difference vs the lock net (z), jobA val paired difference (z), the offline rule. Read-only; own code."""
import glob
import os
import re
import sys


def members(soup_txt):
    out = []
    for line in open(soup_txt, encoding='utf-8', errors='replace'):
        if line.startswith('input '):
            path = line.split(' md5 ')[0][len('input '):].replace('/', '\\')
            parts = path.split('\\')
            run = next((p for p in parts if re.match(r'r\d+_', p)), None)
            out.append(run or os.path.splitext(parts[-1])[0])
    return out


def main():
    sys.stdout.reconfigure(newline=chr(10))   # LF also when redirected to a file on Windows (doc_lint)
    root = sys.argv[1] if len(sys.argv) > 1 else 'C:/o30g/gpu/soups'
    print('| soup | members | S31 b0.6 vs lock (z) | jobA val vs lock (z) | rule |')
    print('|---|---|---|---|---|')
    for tsv in sorted(glob.glob(os.path.join(root, '*_scores.tsv')), key=os.path.getmtime):
        name = os.path.basename(tsv)[:-len('_scores.tsv')]
        rows = [r.split('\t') for r in open(tsv, encoding='utf-8').read().splitlines()[1:] if r.strip()]
        if not rows:
            continue
        r = rows[-1]
        ds, zs, dj, zj = float(r[3]), float(r[4]), float(r[6]), float(r[7])
        st = os.path.join(root, name + '.soup.txt')
        mem = ' + '.join(members(st)) if os.path.isfile(st) else '?'
        rule = 'PASS' if ds <= -2e-5 and zj <= 2 else 'FAIL'
        print(f'| {name} | {mem} | {ds:+.3e} ({zs:+.1f}) | {dj:+.3e} ({zj:+.2f}) | {rule} |')


if __name__ == '__main__':
    main()
