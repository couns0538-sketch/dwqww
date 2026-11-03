#!/usr/bin/env python3
"""mate_reprobe.py - Opus R15: re-probe the mate-probe flips of R13's cand_checks.py at a bigger node budget.

usage: python -I -B mate_reprobe.py CAND_DIR [CAND_DIR ...] [--nodes 30000000] [--mask 0x3]

R13's mate probe (22 KRK / KQK / mate-in-1 positions, `go nodes 3000000`, OFF vs the ON line) calls a position where
OFF reports a mate and the line does not "mate lost" and FAILs - but deep KRK mates (M11-M17) flip at the 3M horizon in
both directions (forge-candidate-checks skill). For every flip in CAND_DIR/cand_checks.json (OFF mate -> ON cp
"lost", OFF cp -> ON mate "gained") this writes a one-position EPD file and runs cand_checks.py again with
--skip-smoke --mate-nodes N on the same exe and line, and records OFF / ON at 3M and at N in CAND_DIR/mate_reprobe.json.
A lost mate that the line still misses at N while OFF finds it at N is a REAL loss (exit 1); else exit 0.
The process lowers itself to Idle on --mask first (children inherit). Reads RESULT.json for the exe and the line.
"""
import argparse
import json
import os
import re
import subprocess
import sys

CC = r'D:\grok-pc-data\dwqww\.claude\worktrees\o13-p1\opus_r13\tools\cand_checks.py'


def set_low(mask):
    if os.name != 'nt':
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(int(mask, 16))):
        sys.exit('mate_reprobe: cannot set Idle / CPU mask')


def is_mate(s):
    return isinstance(s, str) and s.startswith('mate ') and not s.startswith('mate -')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dirs', nargs='+')
    ap.add_argument('--nodes', type=int, default=30000000)
    ap.add_argument('--mask', default='0x3')
    a = ap.parse_args()
    set_low(a.mask)
    real = 0
    for d in a.dirs:
        res = json.load(open(os.path.join(d, 'RESULT.json'), encoding='utf-8-sig'))
        line = f"{res['option']}={res['on']}"
        cc = json.load(open(os.path.join(d, 'cand_checks.json'), encoding='utf-8-sig'))
        mp = cc['checks']['mate_probe']
        off = {e['fen']: e for e in mp['OFF']}
        on = {e['fen']: e for e in mp[line]}
        flips = []
        for fen, e in off.items():
            o, n = e['score'], on.get(fen, {}).get('score')
            if is_mate(o) and not is_mate(n):
                flips.append(('lost', fen, o, n))
            elif not is_mate(o) and is_mate(n):
                flips.append(('gained', fen, o, n))
        out = {'tool': 'mate_reprobe.py', 'dir': d, 'line': line, 'nodes': a.nodes, 'mates_3M': cc.get('summary'),
               'flips': []}
        for i, (kind, fen, o3, n3) in enumerate(flips):
            epd = os.path.join(d, f'reprobe_{i}.epd')
            with open(epd, 'w', newline='\n') as f:
                f.write(fen + '\n')
            js = os.path.join(d, f'reprobe_{i}.json')
            p = subprocess.run([sys.executable, '-I', '-B', CC, res['exe'], js, '--line', line, '--new-opt', res['option'],
                                '--skip-smoke', '--mate-epd', epd, '--mate-nodes', str(a.nodes)], capture_output=True, text=True)
            r2 = json.load(open(js, encoding='utf-8-sig')) if os.path.exists(js) else {}
            mp2 = (r2.get('checks') or {}).get('mate_probe') or {}
            o30 = (mp2.get('OFF') or [{}])[0].get('score')
            n30 = (mp2.get(line) or [{}])[0].get('score')
            verdict = ('REAL LOSS' if kind == 'lost' and is_mate(o30) and not is_mate(n30) else
                       'horizon flip (both find it at N)' if is_mate(o30) and is_mate(n30) else
                       'horizon flip (neither at N)' if not is_mate(o30) and not is_mate(n30) else
                       'ON finds it, OFF does not at N' if is_mate(n30) else 'OFF finds it, ON does not at N')
            if verdict == 'REAL LOSS':
                real += 1
            out['flips'].append({'kind': kind, 'fen': fen, 'off_3M': o3, 'on_3M': n3, 'off_N': o30, 'on_N': n30,
                                 'verdict': verdict, 'exit': p.returncode})
            print(f"{os.path.basename(d)} {kind:6} {fen}: 3M OFF {o3} / ON {n3}; {a.nodes // 1000000}M OFF {o30} / ON {n30} -> {verdict}")
        if not flips:
            print(f"{os.path.basename(d)}: no flips ({cc.get('summary')})")
        with open(os.path.join(d, 'mate_reprobe.json'), 'w', newline='\n') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    print(f'mate_reprobe: {real} real loss(es)')
    return 1 if real else 0


if __name__ == '__main__':
    sys.exit(main())
