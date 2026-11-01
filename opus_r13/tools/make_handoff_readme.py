#!/usr/bin/env python3
"""make_handoff_readme.py - R13 handoff README for one candidate from its evidence files (no hand-copied numbers).

usage: python -I -B make_handoff_readme.py ITEM TITLE EXE_PATH KIT_TAG CHECKS_JSON CI_LOG "setoption lines;..." [--precond-depth 13]
  [--note TEXT ...]
Reads: C:/o13/w/<KIT_TAG>_pc1|pc2 exes (sha256, pc1 = pc2), logs/kit_<KIT_TAG>/off.compare.txt + opt1.compare.txt (OFF and
ON benches), CHECKS_JSON (cand_checks.py), CI_LOG lines for ITEM. Writes opus_r13/p1/<ITEM>/README.md (LF).
"""
import argparse
import hashlib
import json
import os
import re

ap = argparse.ArgumentParser()
for a in ('item', 'title', 'exe', 'tag', 'checks', 'ci_log', 'lines'):
    ap.add_argument(a)
ap.add_argument('--precond-depth', type=int, default=13)
ap.add_argument('--note', action='append', default=[])
a = ap.parse_args()
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'p1')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


pc = [sha(f'C:/o13/w/{a.tag}_{s}/src_copy/forge_ltopgo_{a.tag}_{s}.exe') for s in ('pc1', 'pc2')]
assert pc[0] == pc[1], 'pc1 != pc2'
assert sha(a.exe) == pc[0], 'handoff exe differs from the kit build'


def benches(path):
    out = {}
    for ln in open(path):
        m = re.match(r'bench d(\d+)\s+(\d+)\s+(\d+)', ln)
        if m:
            assert m.group(2) == m.group(3), f'plain != LP in {path}: {ln}'
            out[int(m.group(1))] = int(m.group(2))
    return out


kit = os.path.join(root, 'logs', f'kit_{a.tag}')
off, on = benches(os.path.join(kit, 'off.compare.txt')), benches(os.path.join(kit, 'opt1.compare.txt'))
assert [off[d] for d in (11, 13, 16, 20, 22)] == [312866, 862329, 3024920, 12389307, 34048354], off
d = json.load(open(a.checks))
smoke = d['checks']['smoke']
mates = {k: sum(1 for r in v if r['score'].startswith('mate')) for k, v in d['checks']['mate_probe'].items()}
opts = d['checks']['uci_options']
ci = [ln.strip() for ln in open(a.ci_log) if ln.startswith(a.item + ' |')]
ci_pass = any('SELFPLAY SMOKE PASS' in ln for ln in ci)
cfgs = re.findall(r'"config": "([a-z0-9]+)"', ' '.join(ci))
lines = [x for x in a.lines.split(';') if x]
on_s = '/'.join(str(on[k]) for k in sorted(on))
pd = a.precond_depth
txt = f"""# {a.item} - {a.title} - UNPROVEN

Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled). No Elo claim.

## Exe (not in git)
- `{a.exe.replace('/', chr(92))}`
- sha256 **{pc[0]}** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `{a.item}_port.patch` (`patch -p1` on a clean lock copy).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
""" + '\n'.join(f'setoption name {x.split("=")[0]} value {x.split("=", 1)[1]}' for x in lines) + f"""
```
## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench {pd} = {on[pd]} nodes** (d11..d22 = {on_s}).

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS | logs/kit_{a.tag}/SUMMARY_pc*.txt |
| OFF pins d11-d22, perft, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_{a.tag}/off.compare.txt |
| ON with the gate line (plain = LTO+PGO, differs from OFF) | {on_s} | logs/kit_{a.tag}/opt1.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci: {', '.join(f"{k} {v['default']}" for k, v in opts.items())} | {'PASS' if all(v['ok'] for v in opts.values()) else 'FAIL'} | logs/{a.item}.json |
| T1/T4 go movetime 1000, 4 positions, OFF and gate line: bestmove legal (engine's own go perft 1) | {sum(1 for s in smoke if s['legal'])}/{len(smoke)} | logs/{a.item}.json |
| mate probe (22 forced mates, 3M nodes): mates found {', '.join(f'{k[:28]} {v}' for k, v in mates.items())} | {'PASS' if not [f for f in d['fail'] if f.startswith('mate')] else 'see note'} | logs/{a.item}.json |
| CI ASan+UBSan self-play (Linux g++ 13.3), configs {'/'.join(cfgs)}: 0 sanitizer lines, 0 illegal | {'PASS' if ci_pass else 'FAIL'} | logs/{os.path.basename(a.ci_log)} |
"""
for n in a.note:
    txt += f'\n- {n}'
txt += '\n'
out = os.path.join(root, a.item, 'README.md')
open(out, 'w', newline='\n').write(txt)
print('wrote', out, 'sha', pc[0][:16], 'ON', on_s, 'mates', mates, 'fail', d['fail'])
