#!/usr/bin/env python3
"""depth_probe_ab.py <pgn> <exe A> <exe B> [--opt-a N=V]... [--opt-b N=V]... [--n 200] [--movetime 200] [--rounds 2]
                    [--mask 0x1] [--json out.json] [--expect-load "info string EvalFileV2 loaded"]
Checks of the GPU-trained v2 nets (2026-11-04): a copy of D:/o30/wt/opus_30h/a/depth_probe_o30.py (Opus 30-h job)
with two additions, so that BOTH engines can carry a v2 net on the same exe (net vs its control):
  --opt-a   options for engine A (the control), like --opt-b for engine B (the net);
  load check: an engine given options must answer setoption + isready with a line containing --expect-load and no
              line containing ERROR, else the probe stops (exit 3) - a figure for an unloaded net would be worthless;
  --json    all per-position depths and nps (log) of both engines, the summary numbers and the load lines.
Method unchanged: N positions from a match PGN (every 8th ply of the games, after the opening), each engine searches
each position with `go movetime T` in one long-lived process (hash and history persist, as in a game), rounds
alternate A-B / B-A, both engines pinned to the same CPU at Idle, one at a time. Prints the mean depth of each engine,
the paired mean difference B - A with its standard error, and the nodes-per-second ratio B / A (geometric mean over
positions) with its 95 % CI. Own code (python-chess for the PGN)."""
import argparse
import ctypes
import json
import math
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
    def __init__(self, exe, opts, expect_load):
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
        lines = self.wait('readyok')
        self.load_lines = [l for l in lines if expect_load and expect_load in l]
        self.error_lines = [l for l in lines if 'ERROR' in l.upper()]
        if opts and (not self.load_lines or self.error_lines):
            print(f'engine {exe} with options {opts}: load line {self.load_lines!r}, error lines '
                  f'{self.error_lines!r} (fail closed, exit 3)', flush=True)
            try:
                self.quit()
            except Exception:
                pass
            sys.exit(3)

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
    ap.add_argument('--opt-a', action='append', default=[])
    ap.add_argument('--opt-b', action='append', default=[])
    ap.add_argument('--n', type=int, default=200)
    ap.add_argument('--movetime', type=int, default=200)
    ap.add_argument('--rounds', type=int, default=2)
    ap.add_argument('--mask', default='0x1')
    ap.add_argument('--json', default='')
    ap.add_argument('--expect-load', default='info string EvalFileV2 loaded')
    ap.add_argument('--dry-run', action='store_true', help='only read the positions and print their count')
    a = ap.parse_args()
    pin_self(int(a.mask, 16))
    fens = positions(a.pgn, a.n)
    print(f'{len(fens)} positions from {a.pgn}', flush=True)
    if a.dry_run:
        return
    if len(fens) < 2:
        sys.exit('fewer than 2 positions (fail closed)')
    da, db = [0.0] * len(fens), [0.0] * len(fens)
    na, nb = [0.0] * len(fens), [0.0] * len(fens)
    loads = {'A': [], 'B': []}
    t_start = time.time()
    for r in range(a.rounds):
        order = ('A', 'B') if r % 2 == 0 else ('B', 'A')
        for who in order:
            e = Engine(a.a, a.opt_a, a.expect_load) if who == 'A' else Engine(a.b, a.opt_b, a.expect_load)
            loads[who].append({'round': r + 1, 'load': e.load_lines, 'errors': e.error_lines})
            for i, fen in enumerate(fens):
                d, nps = e.depth(fen, a.movetime)
                (da if who == 'A' else db)[i] += d / a.rounds
                (na if who == 'A' else nb)[i] += math.log(max(nps, 1)) / a.rounds
            e.quit()
        print(f'round {r + 1} ({"".join(order)}) done', flush=True)
    diff = [y - x for x, y in zip(da, db)]
    se = statistics.stdev(diff) / len(diff) ** 0.5
    line1 = (f'positions {len(fens)}, movetime {a.movetime} ms, rounds {a.rounds}: mean depth A {statistics.mean(da):.3f}, '
             f'B {statistics.mean(db):.3f}, B - A {statistics.mean(diff):+.3f} (SE {se:.3f})')
    print(line1)
    lr = [y - x for x, y in zip(na, nb)]
    lse = statistics.stdev(lr) / len(lr) ** 0.5
    m = statistics.mean(lr)
    lo, hi = math.exp(m - 1.96 * lse), math.exp(m + 1.96 * lse)
    line2 = (f'nps B / A (geometric mean over positions) {math.exp(m):.4f} (95 % CI {lo:.4f} .. {hi:.4f}) - the speed '
             f'ratio when the trees are identical')
    print(line2)
    print(f'mean nps A {math.exp(statistics.mean(na)):.0f}, B {math.exp(statistics.mean(nb)):.0f} (geometric means)')
    if a.json:
        rec = {'tool': 'depth_probe_ab.py', 'pgn': a.pgn, 'a': a.a, 'b': a.b, 'opt_a': a.opt_a, 'opt_b': a.opt_b,
               'n': len(fens), 'movetime': a.movetime, 'rounds': a.rounds, 'mask': a.mask, 'seconds': round(time.time() - t_start, 1),
               'mean_depth_a': statistics.mean(da), 'mean_depth_b': statistics.mean(db),
               'depth_b_minus_a': statistics.mean(diff), 'depth_se': se,
               'nps_ratio_b_over_a': math.exp(m), 'nps_ratio_ci95': [lo, hi], 'nps_log_se': lse,
               'geo_mean_nps_a': math.exp(statistics.mean(na)), 'geo_mean_nps_b': math.exp(statistics.mean(nb)),
               'loads': loads, 'summary_lines': [line1, line2],
               'per_position': {'fen': fens, 'depth_a': da, 'depth_b': db, 'log_nps_a': na, 'log_nps_b': nb}}
        with open(a.json, 'x', encoding='utf-8', newline='\n') as f:
            json.dump(rec, f, indent=1)
            f.write('\n')


if __name__ == '__main__':
    main()
