#!/usr/bin/env python3
"""oracle_exact.py - exact root move classes at the 50-move boundary, independent of the engine and of any rounded flag. python-chess as a
separate program (test oracle only). Solver as in review R1 (own code): the clock is counted by hand; a table value decides a child only when
its result does not depend on rounding (sum <= 99 decided, sum > 100 no win or loss), sum = 100 is searched move by move; WDL is used only
after a zeroing move. Repetition is not modelled inside the solver.

usage: python -I -B oracle_exact.py <tables dir> <in.fens> <out.jsonl> [--budget 2000000] [--max-seconds-per-root 60] [--first N]
One JSON line per FEN: fen, clock, wdl, dtz, moves: uci -> class (win cursed draw blessed loss, or None when the budget ran out), best, unresolved count.
Classes: win / loss hold with the 50-move rule. cursed / blessed: table win / loss that the 50-move rule makes a draw for best play.
"""
import argparse
import json
import os
import sys
import time

import chess
import chess.syzygy

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


class Budget(Exception):
    pass


class Solver:
    def __init__(self, tb, budget, seconds):
        self.tb = tb
        self.budget = budget
        self.seconds = seconds
        self.memo = {}

    def reset(self):
        self.left = self.budget
        self.deadline = time.perf_counter() + self.seconds

    def tick(self):
        self.left -= 1
        if self.left < 0 or (self.left % 4096 == 0 and time.perf_counter() > self.deadline):
            raise Budget()

    def val(self, b):
        """1 win, 0 draw, -1 loss for the side to move, clock b.halfmove_clock, 50-move rule on."""
        c = b.halfmove_clock
        key = (b.board_fen(), b.turn, b.ep_square, c)
        got = self.memo.get(key)
        if got is not None:
            return got
        best = -1
        any_move = False
        for m in list(b.legal_moves):
            any_move = True
            self.tick()
            z = b.is_zeroing(m)
            b.push(m)
            try:
                if b.is_checkmate():
                    v = 1
                elif b.is_stalemate():
                    v = 0
                elif z:
                    w = self.tb.probe_wdl(b)
                    v = 1 if w == -2 else (-1 if w == 2 else 0)
                elif c + 1 >= 100:
                    v = 0
                else:
                    d = self.tb.probe_dtz(b)
                    s = abs(d) + c + 1
                    if d == 0 or s > 100:
                        v = 0
                    elif s < 100:
                        v = -1 if d > 0 else 1
                    else:
                        v = -self.val(b)
            finally:
                b.pop()
            best = max(best, v)
            if best == 1:
                break
        if not any_move:
            best = -1 if b.is_check() else 0
        self.memo[key] = best
        return best

    def move_class(self, b, m):
        """Class of root move m from board b."""
        c = b.halfmove_clock
        z = b.is_zeroing(m)
        b.push(m)
        try:
            if b.is_checkmate():
                return 'win'
            if b.is_stalemate():
                return 'draw'
            if z:
                w = self.tb.probe_wdl(b)
                return {2: 'loss', 1: 'blessed', 0: 'draw', -1: 'cursed', -2: 'win'}[w]
            if c + 1 >= 100:
                return 'draw'
            if b.is_repetition(3):
                return 'draw'
            d = self.tb.probe_dtz(b)
            if d == 0:
                return 'draw'
            s = abs(d) + c + 1
            if s > 100:
                return 'cursed' if d < 0 else 'blessed'
            if s < 100:
                return 'win' if d < 0 else 'loss'
            v = self.val(b)
            if d < 0:
                return 'win' if v == -1 else 'cursed'
            return 'loss' if v == 1 else 'blessed'
        finally:
            b.pop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('infile')
    ap.add_argument('out')
    ap.add_argument('--budget', type=int, default=2000000)
    ap.add_argument('--max-seconds-per-root', type=float, default=60.0)
    ap.add_argument('--first', type=int, default=0)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    tb = chess.syzygy.open_tablebase(a.tables)
    solver = Solver(tb, a.budget, a.max_seconds_per_root)
    n = unresolved_roots = 0
    t0 = time.perf_counter()
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        for line in open(a.infile, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if a.first and n >= a.first:
                break
            parts = line.split(' moves ')
            b = chess.Board(parts[0])
            if len(parts) > 1:
                for u in parts[1].split():
                    b.push_uci(u)
            n += 1
            solver.memo.clear()
            solver.reset()
            row = {'fen': line, 'clock': b.halfmove_clock, 'root_threefold': b.is_repetition(3), 'moves': {}, 'unresolved': 0}
            if b.castling_rights:
                row['castling'] = True
            else:
                try:
                    row['wdl'] = tb.probe_wdl(b)
                    row['dtz'] = tb.probe_dtz(b)
                except (chess.syzygy.MissingTableError, KeyError):
                    row['wdl'] = None
                    row['dtz'] = None
                for m in list(b.legal_moves):
                    try:
                        row['moves'][m.uci()] = solver.move_class(b, m)
                    except Budget:
                        row['moves'][m.uci()] = None
                        row['unresolved'] += 1
                    except (chess.syzygy.MissingTableError, KeyError):
                        row['moves'][m.uci()] = None
                        row['unresolved'] += 1
                known = [RANK[v] for v in row['moves'].values() if v is not None]
                row['best'] = max(known) if known and not row['unresolved'] else None
                unresolved_roots += bool(row['unresolved'])
            f.write(json.dumps(row) + '\n')
    print(f'exact oracle rows {n}, roots with unresolved moves {unresolved_roots}, secs {time.perf_counter() - t0:.0f}')


if __name__ == '__main__':
    main()
