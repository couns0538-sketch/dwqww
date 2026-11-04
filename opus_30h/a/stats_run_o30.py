#!/usr/bin/env python3
"""stats_run_o30.py <exe> <pgn> [--opt N=V] [--n 100] [--depth 12] [--mask 0x2] - Opus 30-h job, speed hunt: one
long-lived engine process (hash and history persist, as in a game) searches N game positions (every 8th ply after the
opening) to a fixed depth, one `go` at a time (Forge stops a search when the next command arrives); prints the total
nodes and time and the engine's stderr at exit (the FORGE_NNUE_V2_STATS counters). Fixed depth keeps the trees
identical between the v1 and v2 paths when the evaluations are identical. Own code."""
import argparse
import ctypes
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from depth_probe_o30 import Engine, positions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('pgn')
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--n', type=int, default=100)
    ap.add_argument('--depth', type=int, default=12)
    ap.add_argument('--mask', default='0x2')
    a = ap.parse_args()
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(int(a.mask, 16))):
        sys.exit('cannot pin (fail closed)')
    fens = positions(a.pgn, a.n)
    e = Engine(a.exe, a.opt)
    nodes = 0
    t0 = time.perf_counter()
    for fen in fens:
        e.send(f'position fen {fen}')
        e.send(f'go depth {a.depth}')
        lines = e.wait('bestmove', 120)
        last = [l for l in lines if l.startswith('info depth')]
        n = re.search(r' nodes (\d+)', last[-1]) if last else None
        nodes += int(n.group(1)) if n else 0
    wall = time.perf_counter() - t0
    e.send('quit')
    e.p.wait(timeout=10)
    time.sleep(0.5)   # let the reader thread hand over the exit-time stats lines
    tail = []
    while not e.q.empty():
        tail.append(e.q.get())
    print(f'positions {len(fens)} depth {a.depth}: nodes {nodes} wall {wall:.2f} s nps {nodes / wall:.0f}')
    print('\n'.join(l for l in tail if l and 'v2stats' in l))


if __name__ == '__main__':
    main()
