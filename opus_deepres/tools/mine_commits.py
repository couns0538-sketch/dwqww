#!/usr/bin/env python3
"""mine_commits.py - commit titles plus logged test results (SPRT) of a GitHub repo, without reading whole histories.

usage: python -I -B mine_commits.py OWNER/REPO [--since 2024-01-01] [--until YYYY-MM-DD] [--branch B]
                                    [--top N] [--grep REGEX] [--show SHA ...] [--refresh] [--max-pages 30]

Default output: one line per commit, newest first:  sha7 date | title | STC <elo>+-<err> <tc> n=<games> | LTC ...
  --top N      only the N commits with the largest logged Elo (best block of each commit), sorted descending
  --grep RX    only commits whose title or message matches RX (case-insensitive); prints titles + parsed results
  --show SHA   print the full message of the named commit(s), at most 60 lines each (use only for top gainers)
Elo parsing: OpenBench blocks ("Elo | x +- y", "SPRT | tc", "LLR | ...", "Games | N: ..."), fishtest blocks
("Passed STC/LTC", "LLR:", "Total: N W: L: D:" -> Elo computed from W/L/D, marked ~), and free text "+x elo".
Cache: F:/odr/cache/commits/<owner>__<repo>.json (refresh with --refresh). Reads only the GitHub commits API via gh.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

CACHE = 'F:/odr/cache/commits'


def gh_json(args):
    r = subprocess.run(['gh', 'api'] + args, capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        sys.exit(f'mine_commits: gh api {" ".join(args)} failed: {r.stderr.strip()[:300]}')
    return json.loads(r.stdout) if r.stdout.strip() else []


def fetch(repo, since, until, branch, max_pages):
    out = []
    for page in range(1, max_pages + 1):
        q = ['-X', 'GET', f'repos/{repo}/commits', '-f', 'per_page=100', '-f', f'page={page}']
        if since:
            q += ['-f', f'since={since}T00:00:00Z']
        if until:
            q += ['-f', f'until={until}T23:59:59Z']
        if branch:
            q += ['-f', f'sha={branch}']
        items = gh_json(q)
        if not items:
            break
        for c in items:
            out.append({'sha': c['sha'], 'date': c['commit']['committer']['date'][:10],
                        'msg': c['commit']['message']})
        if len(items) < 100:
            break
    else:
        print(f'mine_commits: stopped at --max-pages {max_pages}; older commits NOT listed', file=sys.stderr)
    return out


def elo_from_wld(w, l, d):
    n = w + l + d
    if n == 0:
        return None
    s = (w + 0.5 * d) / n
    if s <= 0 or s >= 1:
        return None
    return -400 * math.log10(1 / s - 1)


OB_ELO = re.compile(r'^\s*Elo\s*\|\s*([-+]?\d+(?:\.\d+)?)\s*\+-\s*(\d+(?:\.\d+)?)', re.I)
OB_TC = re.compile(r'^\s*(?:SPRT|Conf|Bounds?)\s*\|\s*(\S+)', re.I)
OB_GAMES = re.compile(r'^\s*Games\s*\|\s*N:\s*(\d+)', re.I)
OB_LLR = re.compile(r'^\s*LLR\s*\|\s*([-+]?\d+(?:\.\d+)?)', re.I)
FT_HEAD = re.compile(r'(passed|failed)?\s*\b(STC|LTC|VLTC|SMP\s*STC|SMP\s*LTC)\b', re.I)
FT_TOTAL = re.compile(r'Total:\s*(\d+)\s*W:\s*(\d+)\s*L:\s*(\d+)\s*D:\s*(\d+)', re.I)
FT_ELO = re.compile(r'\bElo:?\s*([-+]?\d+(?:\.\d+)?)\s*(?:\+-|±|\+/-)\s*(\d+(?:\.\d+)?)', re.I)
FREE = re.compile(r'([-+]\d+(?:\.\d+)?)\s*(?:elo|Elo|ELO)\b')


def parse(msg):
    """Return a list of result blocks: dict(kind, elo, err, tc, n, approx)."""
    blocks, cur, label = [], None, None
    for line in msg.splitlines():
        h = FT_HEAD.search(line)
        if h and len(line) < 60:
            label = h.group(2).upper().replace(' ', '')
        m = OB_ELO.match(line)
        if m:
            cur = {'kind': label, 'elo': float(m.group(1)), 'err': float(m.group(2)), 'tc': None, 'n': None,
                   'approx': False}
            blocks.append(cur)
            continue
        m = FT_ELO.search(line)
        if m and not OB_ELO.match(line):
            cur = {'kind': label, 'elo': float(m.group(1)), 'err': float(m.group(2)), 'tc': None, 'n': None,
                   'approx': False}
            blocks.append(cur)
            continue
        if cur is not None:
            m = OB_TC.match(line)
            if m and cur['tc'] is None:
                cur['tc'] = m.group(1)
            m = OB_GAMES.match(line)
            if m and cur['n'] is None:
                cur['n'] = int(m.group(1))
        m = FT_TOTAL.search(line)
        if m:
            n, w, l, d = (int(x) for x in m.groups())
            if cur is not None and cur['n'] is None and cur['kind'] == label:
                cur['n'] = n
            else:
                e = elo_from_wld(w, l, d)
                if e is not None:
                    cur = {'kind': label, 'elo': round(e, 2), 'err': None, 'tc': None, 'n': n, 'approx': True}
                    blocks.append(cur)
    if not blocks:
        for m in FREE.finditer(msg):
            blocks.append({'kind': 'text', 'elo': float(m.group(1)), 'err': None, 'tc': None, 'n': None,
                           'approx': True})
    # unlabelled blocks: name them by their time control (smallest base time = STC, largest = LTC), never by order
    def base(tc):
        m = re.match(r'(\d+(?:\.\d+)?)\+', tc or '')
        return float(m.group(1)) if m else None
    timed = sorted({base(b['tc']) for b in blocks if b['kind'] is None and base(b['tc']) is not None})
    for b in blocks:
        if b['kind'] is not None:
            continue
        t = base(b['tc'])
        if t is None:
            b['kind'] = 'nodes' if (b['tc'] or '').upper().startswith('N=') else 'test'
        elif len(timed) >= 2 and t == timed[0]:
            b['kind'] = 'STC'
        elif len(timed) >= 2 and t == timed[-1]:
            b['kind'] = 'LTC'
        else:
            b['kind'] = 'test'
    return blocks


def fmt_block(b):
    e = f"{b['elo']:+.2f}"
    if b['err'] is not None:
        e += f"+-{b['err']:.2f}"
    if b['approx']:
        e = '~' + e
    parts = [b['kind'] or '?', e]
    if b['tc']:
        parts.append(b['tc'])
    if b['n']:
        parts.append(f"n={b['n']}")
    return ' '.join(parts)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('repo')
    ap.add_argument('--since', default='2024-01-01')
    ap.add_argument('--until')
    ap.add_argument('--branch')
    ap.add_argument('--top', type=int)
    ap.add_argument('--grep')
    ap.add_argument('--show', nargs='*')
    ap.add_argument('--refresh', action='store_true')
    ap.add_argument('--max-pages', type=int, default=30)
    a = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    key = f"{a.repo.replace('/', '__')}__{a.since}__{a.until or 'now'}__{a.branch or 'default'}.json"
    path = os.path.join(CACHE, key)
    if os.path.exists(path) and not a.refresh:
        commits = json.load(open(path, encoding='utf-8'))
    else:
        commits = fetch(a.repo, a.since, a.until, a.branch, a.max_pages)
        tmp = path + '.part'
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(commits, f)
        os.replace(tmp, path)
    if a.show:
        for s in a.show:
            hit = [c for c in commits if c['sha'].startswith(s)]
            if not hit:
                print(f'== {s}: not in the cached range (use gh api repos/{a.repo}/commits/{s})')
                continue
            c = hit[0]
            lines = c['msg'].splitlines()
            print(f"== {c['sha'][:10]} {c['date']}")
            print('\n'.join(lines[:60]))
            if len(lines) > 60:
                print(f'... ({len(lines) - 60} more lines cut)')
        return
    rows = []
    rx = re.compile(a.grep, re.I) if a.grep else None
    for c in commits:
        if rx and not rx.search(c['msg']):
            continue
        blocks = parse(c['msg'])
        title = c['msg'].splitlines()[0][:100] if c['msg'] else ''
        best = max((b['elo'] for b in blocks), default=None)
        rows.append((best, c, title, blocks))
    if a.top:
        rows = sorted([r for r in rows if r[0] is not None], key=lambda r: -r[0])[:a.top]
    print(f'# {a.repo} since {a.since}: {len(commits)} commits cached, {len(rows)} shown')
    for best, c, title, blocks in rows:
        res = ' | '.join(fmt_block(b) for b in blocks[:3])
        print(f"{c['sha'][:7]} {c['date']} | {title}" + (f' | {res}' if res else ''))


if __name__ == '__main__':
    main()
