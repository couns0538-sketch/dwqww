#!/usr/bin/env python3
"""wi_tally.py - per-position tally of one warm_identity.py run (read-only on its ref.log / cand.log).

usage: python -I -B wi_tally.py <warm_identity out dir>

warm_identity.py (opus_speed/tools) is the method and its verdict decides; this only counts its own logs per
position and per net state. For every search (`> position fen ...` + `> go nodes ...` up to `bestmove`) it builds
the harness's own result row: the last `info depth` line without the `nps` / `time` fields, plus the bestmove line.
The net state of a search comes from the `> setoption name UseNNUE value ...` lines before it (engine default: true).
Per position it compares depth, score, nodes and bestmove (and, as a second count, the whole row). It prints the counts
for net on and net off, the net-off blocks (FEN index // 25), and the first mismatch.
Exit 0 = all identical, 3 = a mismatch, 1 = error (different scripts, no searches).
"""
import pathlib
import re
import sys

STRIP = re.compile(r' (nps|time) \d+')   # the same normalisation as warm_identity.py


def searches(path):
    net, out, cur = True, [], None
    for s in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        if s.startswith('> setoption name UseNNUE value '):
            net = s.rsplit(' ', 1)[1] == 'true'
        elif s.startswith('> position fen '):
            cur = {'fen': s[len('> position fen '):], 'net': net, 'info': None}
        elif cur is not None and s.startswith('info depth '):
            cur['info'] = s
        elif cur is not None and s.startswith('bestmove'):
            cur['row'] = (STRIP.sub('', cur['info']) + ' | ' + s) if cur['info'] else s
            out.append(cur)
            cur = None
    return out


def fields(row):
    pats = (r'\bdepth (\d+)', r'\bscore ((?:cp|mate) -?\d+)', r'\bnodes (\d+)', r'bestmove (\S+)')
    return tuple((m.group(1) if m else '-') for m in (re.search(p, row) for p in pats))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    d = pathlib.Path(sys.argv[1])
    r, c = searches(d / 'ref.log'), searches(d / 'cand.log')
    if not r or len(r) != len(c):
        print(f'ERROR: {len(r)} ref searches vs {len(c)} cand searches')
        return 1
    tot, same, full, first = {True: 0, False: 0}, {True: 0, False: 0}, {True: 0, False: 0}, None
    for i, (x, y) in enumerate(zip(r, c)):
        if x['fen'] != y['fen'] or x['net'] != y['net']:
            print(f'ERROR: the two scripts differ at search {i}')
            return 1
        k = x['net']
        tot[k] += 1
        ok = fields(x['row']) == fields(y['row'])
        same[k] += ok
        full[k] += x['row'] == y['row']
        if first is None and (not ok or x['row'] != y['row']):
            first = (i, x, y)
    for k, name in ((True, 'net on '), (False, 'net off')):
        print(f'{name}: {same[k]} / {tot[k]} identical (depth, score, nodes, bestmove); whole rows {full[k]} / {tot[k]}')
    print('net-off blocks (FEN index // 25):', sorted({i // 25 for i, x in enumerate(r) if not x['net']}))
    if first is None:
        print('first mismatch: none')
        return 0
    i, x, y = first
    print(f'first mismatch: search {i} (net {"on" if x["net"] else "off"}), fen {x["fen"]}')
    print(f'  ref : {x["row"]}\n  cand: {y["row"]}')
    return 3


if __name__ == '__main__':
    sys.exit(main())
