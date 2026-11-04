#!/usr/bin/env python3
"""depth_probe_o30.py <pgn> <exe A> <exe B> [--opt-b N=V] [--n 200] [--movetime 200] [--rounds 2] [--mask 0x2]
Opus 30-h job: a minutes-long testbed for the in-game speed gap. Takes N positions from a match PGN (every 8th ply of the
games, after the opening), lets each engine search each position with `go movetime T` in one long-lived process (like a
game: hash and history persist), and records the depth of the last `info depth` line. Rounds alternate the order
A-B / B-A (both engines pinned to the same CPU at Idle, one at a time). Prints the mean depth of each engine and the
paired mean difference B - A with its standard error over positions. Own code (python-chess for the PGN)."""
import argparse
import ctypes
import math
import io
import queue
import re
import statistics
import subprocess
import sys
import threading
import time

import chess
import chess.pgn


def pin_self(mask):
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(mask)):
        sys.exit('cannot set Idle / CPU mask (fail closed)')


class Engine:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.send('uci')
        self.wait('uciok')
        for kv in opts:
            n, v = kv.split('=', 1)
            self.send(f'setoption name {n} value {v}')
        for kv in ('Threads=1', 'Hash=16', 'OwnBook=false'):
            n, v = kv.split('=', 1)
            self.send(f'setoption name {n} value {v}')
        self.send('ucinewgame')
        self.send('isready')
        self.wait('readyok')

    def _read(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip())

    def send(self, s):
        self.p.stdin.write(s + '\n')
        self.p.stdin.flush()

    def wait(self, token, timeout=60):
        lines, t0 = [], time.time()
        while time.time() - t0 < timeout:
            try:
                line = self.q.get(timeout=timeout)
            except queue.Empty:
                break
            lines.append(line)
            if line.startswith(token):
                return lines
        raise RuntimeError(f'no {token}')

    def depth(self, fen, movetime):
        self.send(f'position fen {fen}')
        self.send(f'go movetime {movetime}')
        lines = self.wait('bestmove', 30)
        d = [int(m.group(1)) for l in lines for m in [re.match(r'info depth (\d+)', l)] if m]
        nps = [int(m.group(1)) for l in lines for m in [re.search(r' nps (\d+)', l)] if m]
        return (d[-1] if d else 0, nps[-1] if nps else 0)

    def quit(self):
        self.send('quit')
        self.p.wait(timeout=10)


def positions(pgn_path, n):
    out = []
    with open(pgn_path, encoding='utf-8', errors='replace') as f:
        while len(out) < n:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            b = g.board()
            for i, mv in enumerate(g.mainline_moves()):
                b.push(mv)
                if i >= 16 and i % 8 == 0 and not b.is_game_over():
                    out.append(b.fen())
                    if len(out) >= n:
                        break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pgn')
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--opt-b', action='append', default=[])
    ap.add_argument('--n', type=int, default=200)
    ap.add_argument('--movetime', type=int, default=200)
    ap.add_argument('--rounds', type=int, default=2)
    ap.add_argument('--mask', default='0x2')
    a = ap.parse_args()
    pin_self(int(a.mask, 16))
    fens = positions(a.pgn, a.n)
    da, db = [0.0] * len(fens), [0.0] * len(fens)
    na, nb = [0.0] * len(fens), [0.0] * len(fens)
    for r in range(a.rounds):
        order = ('A', 'B') if r % 2 == 0 else ('B', 'A')
        for who in order:
            e = Engine(a.a, []) if who == 'A' else Engine(a.b, a.opt_b)
            for i, fen in enumerate(fens):
                d, nps = e.depth(fen, a.movetime)
                (da if who == 'A' else db)[i] += d / a.rounds
                (na if who == 'A' else nb)[i] += math.log(max(nps, 1)) / a.rounds
            e.quit()
        print(f'round {r + 1} ({"".join(order)}) done', flush=True)
    diff = [y - x for x, y in zip(da, db)]
    se = statistics.stdev(diff) / len(diff) ** 0.5
    print(f'positions {len(fens)}, movetime {a.movetime} ms, rounds {a.rounds}: mean depth A {statistics.mean(da):.3f}, '
          f'B {statistics.mean(db):.3f}, B - A {statistics.mean(diff):+.3f} (SE {se:.3f})')
    lr = [y - x for x, y in zip(na, nb)]
    lse = statistics.stdev(lr) / len(lr) ** 0.5
    m = statistics.mean(lr)
    print(f'nps B / A (geometric mean over positions) {math.exp(m):.4f} (95 % CI {math.exp(m - 1.96 * lse):.4f} .. '
          f'{math.exp(m + 1.96 * lse):.4f}) - the speed ratio when the trees are identical')


if __name__ == '__main__':
    main()
