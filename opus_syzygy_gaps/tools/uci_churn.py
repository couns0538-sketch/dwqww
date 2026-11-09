#!/usr/bin/env python3
"""uci_churn.py - random option and table changes between searches, for the sanitizer engines and the plain engine. Own code, python-chess only for legality. Run under pinned.ps1.

usage: <venv python> -I -B uci_churn.py <exe> <out.json> --seed N --ops 3000 --pool f1.fens,f2.fens --tables D1,D2,.. [--threads 1] [--bench-expect 862329] [--check-every 150] [--limit-s 300]

One engine, one script from the seed. An op is one of: position + go (depth, nodes, movetime, mate, infinite + stop, sometimes searchmoves; sometimes the game goes on with the engine's move, so
clocks cross the boundary), SyzygyTbBounds / SyzygyRootExact / SyzygyRule50 (also out of range and junk values), Syzygy50MoveRule, SyzygyPath (the folders given, or off), SyzygyProbeDepth, Clear Hash,
Hash, UseNNUE, ucinewgame. Hand-made roots are added to the pool: no legal move, bare kings and minor pieces, clocks 99 to 255, castling rights.
Checks, each fails the run (exit 1):
  bestmove legal, inside searchmoves when given, `(none)` or 0000 only without a legal move; the engine stays alive and answers within --limit-s.
  State check every --check-every ops: fixed options (all switches on, first folder, rule on, Hash 32), ucinewgame, five fixed roots at depth 6: nodes, score, move must equal the first time, so no option or
  table change leaks through ucinewgame. Timed searches are compared for legality only.
  At the end: everything back to the defaults, tables off, `bench 13` = --bench-expect.
The engine is never killed: a search that does not answer stops the run with exit 3 and is reported.
"""
import argparse
import json
import os
import random
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_tb import Engine, check_self_pin, parse_search  # noqa: E402

HAND = [
    '7k/6Q1/6K1/8/8/8/8/8 b - - 0 1',           # checkmated
    '7k/5Q2/6K1/8/8/8/8/8 b - - 0 1',           # stalemated
    '8/8/8/4k3/8/4K3/8/8 w - - 0 1',            # bare kings
    '8/8/8/4k3/8/4K3/4N3/8 b - - 40 60',        # KNvK
    '8/8/8/4k3/8/4K3/4B3/8 w - - 99 90',        # KBvK
    '8/8/4b3/4k3/8/4K3/4B3/8 w - - 100 90',     # KBvKB
    '8/8/4k3/8/8/4K3/4Q3/8 w - - 99 90',        # KQvK, one move from the rule
    '8/8/4k3/8/8/4K3/4Q3/8 w - - 100 90',
    '8/8/4k3/8/8/4K3/4Q3/8 w - - 101 90',
    '8/8/4k3/8/8/4K3/4Q3/8 w - - 150 120',
    '8/8/4k3/8/8/4K3/4Q3/8 w - - 255 200',
    '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1',         # castling rights with few pieces
    'r3k2r/8/8/8/8/8/8/4K3 b kq - 95 60',
    '8/8/8/8/k2Pp3/8/8/4K3 b - d3 0 1',         # en passant with few pieces
    '8/P6k/8/8/8/8/p6K/8 w - - 98 70',          # promotions at the clock's end
]
FIXED = ['8/8/8/8/8/4k3/4p3/4K3 w - - 0 1', '8/8/2k5/8/8/3QK3/8/4r3 w - - 30 50', '8/8/8/3k4/2R5/3K4/2N4N/8 b - - 87 90', '8/q7/8/8/8/3Q1RK1/k7/8 b - - 87 44', '8/8/1K2k3/8/8/3B4/3Q4/4B3 w - - 95 48']


class Churn:
    def __init__(self, a):
        self.a = a
        self.rnd = random.Random(a.seed)
        self.e = Engine(os.path.abspath(a.exe), a.limit_s)
        self.pool = list(HAND)
        for name in a.pool.split(','):
            lines = [l.strip() for l in open(name, encoding='utf-8') if l.strip() and not l.startswith('#')]
            self.rnd.shuffle(lines)
            self.pool += [l for l in lines[:4000] if ' moves ' not in l]
        self.tables = a.tables.split(',')
        self.counts = {}
        self.fen = None
        self.moves = []
        self.fixed_rows = None
        self.searches = 0
        self.none_moves = 0

    def count(self, what):
        self.counts[what] = self.counts.get(what, 0) + 1

    def ready(self):
        self.e.send('isready')
        self.e.read_until(lambda l: l == 'readyok')

    def setopt(self, name, value):
        self.e.send(f'setoption name {name} value {value}')

    def board(self):
        b = chess.Board(self.fen)
        for m in self.moves:
            b.push_uci(m)
        return b

    def new_position(self):
        self.fen = self.rnd.choice(self.pool)
        self.moves = []

    def search(self):
        r = self.rnd
        if self.fen is None or r.random() < 0.7:
            self.new_position()
        elif self.board().is_game_over(claim_draw=False) or len(self.moves) > 200:
            self.new_position()
        b = self.board()
        pos = f'position fen {self.fen}' + (' moves ' + ' '.join(self.moves) if self.moves else '')
        self.e.send(pos)
        legal = [m.uci() for m in b.legal_moves]
        given = None
        spec = ''
        if legal and r.random() < 0.12:
            given = r.sample(legal, r.randint(1, len(legal)))
            spec = ' searchmoves ' + ' '.join(given)
        kind = r.random()
        if kind < 0.45:
            cmd = f'go depth {r.randint(1, 8)}'
        elif kind < 0.75:
            cmd = f'go nodes {r.choice([1, 2, 10, 100, 1000, 5000, 20000])}'
        elif kind < 0.88:
            cmd = f'go movetime {r.randint(1, 30)}'
        elif kind < 0.94:
            cmd = f'go mate {r.randint(1, 3)}'
        else:
            cmd = 'go infinite'
        self.e.send(cmd + spec)
        if cmd.startswith('go mate') or cmd == 'go infinite':
            time.sleep(r.random() * 0.05)
            self.e.send('stop')
        lines = self.e.read_until(lambda l: l.startswith('bestmove'))
        row = parse_search(lines)
        self.searches += 1
        bad = [l for l in row.get('invalid', []) if 'invalid value' not in l]  # a junk option value is answered with "invalid value", that answer is right
        if bad:
            raise AssertionError(f'invalid answer {bad[:2]} to {pos}')
        best = row['bestmove']
        if best in ('(none)', '0000', None):
            self.none_moves += 1
            if legal:
                raise AssertionError(f'no move with legal moves on the board: {pos} {cmd}{spec}')
            self.new_position()
            return
        if best not in legal:
            raise AssertionError(f'illegal bestmove {best}: {pos} {cmd}{spec}')
        if given is not None and best not in given:
            raise AssertionError(f'bestmove {best} outside searchmoves: {pos} {cmd}{spec}')
        if r.random() < 0.5:
            self.moves.append(best)

    def option_op(self):
        r = self.rnd
        x = r.random()
        if x < 0.25:
            self.setopt('SyzygyTbBounds', r.choice([0, 1, 2, 3, 4, 5, 6, 7, 7, 7, -1, 8, 99, 'x']))
        elif x < 0.50:
            self.setopt('SyzygyRootExact', r.choice([0, 1, 2, 3, 3, 3, -1, 4, 'x']))
        elif x < 0.75:
            self.setopt('SyzygyRule50', r.choice([0, 1, 2, 3, 3, 3, -1, 4, 'x']))
        elif x < 0.83:
            self.setopt('Syzygy50MoveRule', r.choice(['true', 'false', 'true', 'false', 'junk']))
        elif x < 0.89:
            self.setopt('SyzygyPath', r.choice(self.tables + ['<empty>']))
            self.ready()
        elif x < 0.92:
            self.setopt('SyzygyProbeDepth', r.randint(1, 10))
        elif x < 0.95:
            self.e.send('setoption name Clear Hash')
        elif x < 0.97:
            self.setopt('Hash', r.choice([1, 4, 16, 32]))
            self.ready()
        elif x < 0.985:
            self.setopt('UseNNUE', r.choice(['true', 'false']))
        else:
            self.e.send('ucinewgame')

    def fixed_config(self):
        for name, v in (('SyzygyTbBounds', 7), ('SyzygyRootExact', 3), ('SyzygyRule50', 3), ('Syzygy50MoveRule', 'true'), ('SyzygyProbeDepth', 1), ('UseNNUE', 'true'), ('Hash', 32), ('Threads', 1)):
            self.setopt(name, v)
        self.setopt('SyzygyPath', self.tables[0])
        self.ready()

    def state_check(self):
        self.fixed_config()
        rows = []
        for fen in FIXED:
            self.e.send('ucinewgame')
            self.e.send('position fen ' + fen)
            self.e.send('go depth 6')
            row = parse_search(self.e.read_until(lambda l: l.startswith('bestmove')))
            rows.append((row['score_type'], row['score'], row['nodes'], row['bestmove']))
        self.count('state_checks')
        if self.fixed_rows is None:
            self.fixed_rows = rows
        elif rows != self.fixed_rows:
            raise AssertionError(f'state leak: first {self.fixed_rows} now {rows}')
        self.setopt('Threads', self.a.threads)
        self.ready()

    def run(self):
        e = self.e
        e.send('uci')
        names = [l for l in e.read_until(lambda l: l == 'uciok') if l.startswith('option name')]
        for k in ('SyzygyTbBounds', 'SyzygyRootExact', 'SyzygyRule50'):
            if not any(n.startswith(f'option name {k} ') for n in names):
                raise RuntimeError(f'engine does not advertise option {k}')
        self.setopt('OwnBook', 'false')
        self.setopt('Threads', self.a.threads)
        self.ready()
        self.state_check()
        for op in range(self.a.ops):
            if self.rnd.random() < 0.55:
                self.search()
                self.count('searches')
            else:
                self.option_op()
                self.count('options')
            if (op + 1) % self.a.check_every == 0:
                self.state_check()
        self.state_check()
        for name, v in (('SyzygyTbBounds', 0), ('SyzygyRootExact', 0), ('SyzygyRule50', 0), ('Syzygy50MoveRule', 'true'), ('SyzygyProbeDepth', 1), ('UseNNUE', 'true'), ('Threads', 1), ('Hash', 32)):
            self.setopt(name, v)
        self.setopt('SyzygyPath', '<empty>')
        self.ready()
        e.send('ucinewgame')
        e.send('bench 13')
        line = e.read_until(lambda l: 'bench depth' in l)[-1]
        self.counts['bench13'] = line
        if self.a.bench_expect and f'nodes {self.a.bench_expect}' not in line:
            raise AssertionError(f'bench 13 after the churn: {line}')
        self.ready()
        e.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('out')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--ops', type=int, default=3000)
    ap.add_argument('--pool', required=True)
    ap.add_argument('--tables', required=True)
    ap.add_argument('--threads', type=int, default=1)
    ap.add_argument('--bench-expect', type=int, default=0)
    ap.add_argument('--check-every', type=int, default=150)
    ap.add_argument('--limit-s', type=float, default=300.0)
    a = ap.parse_args()
    check_self_pin()
    if os.path.exists(a.out):
        print(f'refusing: {a.out} exists')
        return 2
    c = Churn(a)
    res = {'exe': a.exe, 'seed': a.seed, 'ops': a.ops, 'threads': a.threads}
    code = 0
    try:
        c.run()
        res['result'] = 'PASS'
    except TimeoutError as ex:
        res['result'] = f'TIMEOUT {ex}; engine pid {c.e.p.pid} left running'
        code = 3
    except Exception as ex:
        res['result'] = f'FAIL {type(ex).__name__} {ex}'
        code = 1
    res.update(c.counts)
    res['searches'] = c.searches
    res['none_moves'] = c.none_moves
    res['last_position'] = (c.fen, c.moves)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ('result', 'searches', 'none_moves', 'state_checks') if k in res}))
    return code


if __name__ == '__main__':
    sys.exit(main())
