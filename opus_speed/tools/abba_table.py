#!/usr/bin/env python3
"""abba_table.py - one markdown table from abba.ps1 result folders (speed job, own code).

usage: python -I -B abba_table.py <folder with <name>_d<depth> subfolders> [<more folders> ...] [--md out.md]
Reads every <name>_d<D>/summary.txt (abba.ps1 output) or IDENTICAL.txt (abba_queue: exe = lock file) and prints
name, depth, wall median + 95 % t-interval + sd/round, cpu median + interval + sd, the two verdicts, the runs.csv md5
and the order (ABBA every round / alternating). Reads the summaries, not the queue's results.tsv, so a run whose
summary was written is listed even if a later step of its runner failed. Sorted by the wall median (the protocol
metric), best first; the cpu column is advisory.
"""
import pathlib
import re
import sys

RX = re.compile(r'B/A median ([0-9.]+) \(([-+0-9.]+)%\), 95% t-interval \[([0-9.]+), ([0-9.]+)\], sd/round ([0-9.]+)%')


def parse(d):
    s = d / 'summary.txt'
    if (d / 'IDENTICAL.txt').exists() and not s.exists():
        return {'name': d.name, 'identical': True}
    if not s.exists():
        return None
    t = s.read_text(encoding='utf-8', errors='replace')
    row = {'name': d.name, 'identical': False}
    for key in ('wall', 'cpu'):
        line = next((l for l in t.splitlines() if l.startswith(key + ' ')), '')
        m = RX.search(line)
        row[key] = m.groups() if m else None
    v = re.search(r'VERDICT wall (\S+) / cpu (\S+)', t)
    row['verdict'] = v.groups() if v else ('?', '?')
    o = re.search(r'order ([^,]+),', t)
    row['order'] = o.group(1) if o else 'ABBA every round'
    md5 = re.search(r'runs\.csv md5 ([0-9a-f]{32})', t)
    row['md5'] = md5.group(1)[:8] if md5 else '?'
    return row


def main():
    args = [a for a in sys.argv[1:]]
    out = None
    if '--md' in args:
        i = args.index('--md')
        out = args[i + 1]
        del args[i:i + 2]
    rows = []
    for root in args:
        for d in sorted(pathlib.Path(root).iterdir()):
            if d.is_dir():
                r = parse(d)
                if r:
                    rows.append(r)

    def key(r):
        # sorted by the WALL median: the protocol metric is the engine's own nps; cpu is advisory (review SHOULD 4)
        if r['identical'] or not r.get('wall'):
            return 0.0
        return -float(r['wall'][0])
    rows.sort(key=key)
    lines = ['| run | wall B/A median [95 %] sd | cpu B/A median [95 %] sd | verdict wall / cpu | order | runs.csv md5 |',
             '|---|---|---|---|---|---|']
    for r in rows:
        if r['identical']:
            lines.append('| %s | = lock exe (identical file, not timed) | | | | |' % r['name'])
            continue
        w, c = r.get('wall'), r.get('cpu')
        ws = '%s (%s%%) [%s, %s] %s%%' % w if w else 'n/a'
        cs = '%s (%s%%) [%s, %s] %s%%' % c if c else 'n/a'
        lines.append('| %s | %s | %s | %s / %s | %s | %s |' % (r['name'], ws, cs, r['verdict'][0], r['verdict'][1], r['order'], r['md5']))
    text = '\n'.join(lines) + '\n'
    print(text)
    if out:
        p = pathlib.Path(out)
        if p.exists():
            sys.exit('refusing to overwrite ' + out)
        p.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
