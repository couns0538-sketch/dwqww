#!/usr/bin/env python3
"""fake_fastchess.py - Opus 30-h job, SPSA simulation test only: answers the tuner's fastchess command line with a PGN of
simulated games (own code). Strength model with a KNOWN optimum: Elo(engine) = -K * sum(((v - opt) / scale) ** 2) over
the options in OPT; per game the expected score of `plus` comes from the Elo difference (logistic, 400 scale) and a
fixed draw share; outcomes are drawn from a generator seeded by the command line (repeatable). Writes the -pgnout file
in fastchess's tag layout ([Event], [White], [Black], [Result], [Termination]) and exits 0.
"""
import hashlib
import json
import os
import random
import sys

OPT = json.loads(os.environ.get('SIM_OPT', '{"A": [160, 40], "B": [20, 10]}'))   # name: [optimum, scale]
K = float(os.environ.get('SIM_K', '60'))
DRAW = 0.4


def elo(vals):
    return -K * sum(((vals[n] - o) / s) ** 2 for n, (o, s) in OPT.items() if n in vals)


def main():
    a = sys.argv[1:]
    engines, cur = {}, None
    rounds, pgn = 1, None
    i = 0
    while i < len(a):
        x = a[i]
        if x == '-engine':
            cur = {}
            engines[len(engines)] = cur
        elif x.startswith('name=') and cur is not None:
            cur['name'] = x[5:]
        elif x.startswith('option.') and cur is not None and x[7:].split('=', 1)[0] in OPT:
            k, v = x[7:].split('=', 1)
            cur.setdefault('vals', {})[k] = int(v)
        elif x == '-each':
            cur = None
        elif x == '-rounds':
            rounds = int(a[i + 1])
        elif x.startswith('file=') and i > 0 and a[i - 1] == '-pgnout':
            pgn = x[5:]
        i += 1
    plus = next(e for e in engines.values() if e.get('name') == 'plus')
    minus = next(e for e in engines.values() if e.get('name') == 'minus')
    diff = elo(plus.get('vals', {})) - elo(minus.get('vals', {}))
    s = 1.0 / (1.0 + 10 ** (-diff / 400.0))
    p_win = min(max(s - DRAW / 2, 0.0), 1.0)
    p_loss = min(max(1.0 - s - DRAW / 2, 0.0), 1.0)
    rng = random.Random(hashlib.sha256(' '.join(a).encode()).hexdigest())
    games = []
    for g in range(2 * rounds):
        u = rng.random()
        plus_res = 1 if u < p_win else (-1 if u < p_win + p_loss else 0)
        white = 'plus' if g % 2 == 0 else 'minus'
        if plus_res == 0:
            res = '1/2-1/2'
        else:
            res = '1-0' if (plus_res == 1) == (white == 'plus') else '0-1'
        black = 'minus' if white == 'plus' else 'plus'
        games.append(f'[Event "sim"]\n[Round "{g // 2 + 1}"]\n[White "{white}"]\n[Black "{black}"]\n[Result "{res}"]\n'
                     f'[Termination "normal"]\n\n1. e4 {res}\n\n')
    with open(pgn, 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(games))
    print(f'fake fastchess: {2 * rounds} games, plus {plus.get("vals")} minus {minus.get("vals")} diff {diff:+.1f} Elo')
    return 0


if __name__ == '__main__':
    sys.exit(main())
