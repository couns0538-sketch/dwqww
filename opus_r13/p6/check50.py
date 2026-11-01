#!/usr/bin/env python3
"""check50.py - R13 P6 (own code): 50-move handling of the ported prober over UCI.

usage: python -I -B check50.py <engine.exe> <tables dir> <prefix> [--depth 6]
Takes the positions of <prefix>.fens whose oracle WDL (<prefix>.oracle, from check_tb.py gen) is +-1: cursed wins (+1) and
blessed losses (-1), i.e. decided only beyond the fifty-move rule. For each one the engine searches with SyzygyPath set,
once with Syzygy50MoveRule true and once false, and the last `info ... score` is read (the engine waits for bestmove).
Pass: with the rule ON every such position scores as a draw-band value (|cp| <= 100, no mate score); with the rule OFF it
scores as a tablebase win / loss with the oracle's sign (|cp| >= 20000 or a mate score). Exit 1 on any failure.
"""
import argparse
import re
import subprocess
import sys


def score(engine, tables, fen, rule50, depth):
    p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    cmds = ['uci', f'setoption name SyzygyPath value {tables}', f'setoption name Syzygy50MoveRule value {"true" if rule50 else "false"}',
            'setoption name OwnBook value false', 'isready', f'position fen {fen}', f'go depth {depth}']
    p.stdin.write('\n'.join(cmds) + '\n')
    p.stdin.flush()
    last = None
    for line in p.stdout:
        m = re.search(r'score (cp|mate) (-?\d+)', line)
        if m:
            last = (m.group(1), int(m.group(2)))
        if line.startswith('bestmove'):
            break
    p.stdin.write('quit\n')
    p.stdin.flush()
    p.wait(timeout=30)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('engine')
    ap.add_argument('tables')
    ap.add_argument('prefix')
    ap.add_argument('--depth', type=int, default=6)
    a = ap.parse_args()
    fens = [l.strip() for l in open(a.prefix + '.fens')]
    oracle = [int(l.split()[0]) for l in open(a.prefix + '.oracle')]
    cases = [(f, w) for f, w in zip(fens, oracle) if abs(w) == 1]
    if not cases:
        print('FAIL: no cursed / blessed positions')
        sys.exit(1)
    bad = 0
    for fen, wdl in cases:
        on = score(a.engine, a.tables, fen, True, a.depth)
        off = score(a.engine, a.tables, fen, False, a.depth)
        on_ok = on is not None and on[0] == 'cp' and abs(on[1]) <= 100
        off_ok = off is not None and (off[0] == 'mate' and (off[1] > 0) == (wdl > 0) or
                                     off[0] == 'cp' and abs(off[1]) >= 20000 and (off[1] > 0) == (wdl > 0))
        bad += not (on_ok and off_ok)
        print(f'{"ok " if on_ok and off_ok else "BAD"} wdl {wdl:+d}  rule50 on {on}  off {off}  {fen}')
    print(f'{len(cases) - bad}/{len(cases)} cursed / blessed positions handled as expected')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
