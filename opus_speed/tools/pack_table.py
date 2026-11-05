#!/usr/bin/env python3
"""pack_table.py - one markdown table of speed packs (speed job, own code).

usage: python -I -B pack_table.py [F:/ospd/packs] [--only name1,name2] [--md out.md]
Per pack folder: switches flipped (pack.log 'kit default flipped'), exe sha256 prefix and pc1 = pc2 (REPRO line),
bit-exact verdict (bitexact/bitexact.log, also bitexact_full12k/ if present), ABBA wall / cpu medians with the 95 %
t-intervals and the verdicts (abba_d20/summary.txt), and the runs.csv md5. Packs marked SUPERSEDED in their candidate
file are listed with that word. Reads files only; refuses to overwrite --md.
"""
import pathlib
import re
import sys

RX = re.compile(r'B/A median ([0-9.]+) \(([-+0-9.]+)%\), 95% t-interval \[([0-9.]+), ([0-9.]+)\]')


def read(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def main():
    args = sys.argv[1:]
    out = None
    only = None
    if '--md' in args:
        i = args.index('--md'); out = args[i + 1]; del args[i:i + 2]
    if '--only' in args:
        i = args.index('--only'); only = set(args[i + 1].split(',')); del args[i:i + 2]
    root = pathlib.Path(args[0] if args else 'F:/ospd/packs')
    cand_dir = pathlib.Path(__file__).resolve().parent.parent / 'candidates'
    rows = ['| pack | switches | exe (pc1 = pc2) | bit-exact | wall B/A [95 %] | cpu B/A [95 %] | verdict wall / cpu | runs.csv md5 |',
            '|---|---|---|---|---|---|---|---|']
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if only and d.name not in only:
            continue
        log = read(d / 'pack.log')
        if not log:
            continue
        sw = ', '.join(re.findall(r'kit default flipped: (\S+ = \S+)', log)) or '-'
        rep = re.search(r'REPRO \S+ pc1 = pc2 sha256 ([0-9a-f]{8})', log)
        exe = (rep.group(1) + ' (pc1 = pc2)') if rep else 'no REPRO'
        bx = re.search(r'VERDICT ([^\n]+)', read(d / 'bitexact' / 'bitexact.log'))
        bxt = bx.group(1) if bx else ('check error' if 'CHECK ERROR' in log or 'ERROR' in read(d / 'bitexact' / 'bitexact.log') else 'n/a')
        full = re.search(r'VERDICT ([^\n]+)', read(d / 'bitexact_full12k' / 'bitexact.log'))
        if full:
            bxt += '; full 12k: ' + full.group(1)
        s = read(d / 'abba_d20' / 'summary.txt')
        w = c = None
        for line in s.splitlines():
            if line.startswith('wall '):
                w = RX.search(line)
            elif line.startswith('cpu '):
                c = RX.search(line)
        v = re.search(r'VERDICT wall (\S+) / cpu (\S+)', s)
        md5 = re.search(r'runs\.csv md5 ([0-9a-f]{32})', s)
        ws = '%s (%s%%) [%s, %s]' % w.groups() if w else '-'
        cs = '%s (%s%%) [%s, %s]' % c.groups() if c else '-'
        vs = '%s / %s' % v.groups() if v else '-'
        name = d.name
        if 'SUPERSEDED' in read(cand_dir / (d.name + '.md')):
            name += ' (SUPERSEDED)'
        rows.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (name, sw, exe, bxt, ws, cs, vs, md5.group(1)[:8] if md5 else '-'))
    text = '\n'.join(rows) + '\n'
    print(text)
    if out:
        p = pathlib.Path(out)
        if p.exists():
            sys.exit('refusing to overwrite ' + out)
        p.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
