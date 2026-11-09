#!/usr/bin/env python3
"""uci_misc_checks.py - protocol fixtures with tables loaded. Own code, python-chess only for legality. Run under pinned.ps1.

usage: python -I -B uci_misc_checks.py <exe> <tables> <exact.jsonl> <castle.fens> <roots.fens> <out.json> [--opt N=V ...] [--soak-rows 60]
Checks (each counted, exit 1 on any failure):
  searchmoves: on tablebase roots, a list with only non-best moves is searched as given; a list with a best move and others plays a best move.
  castling: roots with castling rights: legal move, no crash, 6-man roots with rights too.
  protocol: go infinite / stop, go ponder / stop, go ponder / ponderhit, go mate 2, go nodes 0, setoption SyzygyPath off and on between searches.
  soak: Threads 2, 3, 4 (CPUs 12-15), go movetime 200 over mixed roots, Hash changes, every bestmove legal; then Threads 1, bench 13 answers.
Timed searches are compared only for legality, never for nodes.
"""
import argparse
import json
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_tb import Engine, check_self_pin, parse_search  # noqa: E402

RANK = {'win': 2, 'cursed': 1, 'draw': 0, 'blessed': -1, 'loss': -2}


def setup(e, a, threads=1):
    e.send('uci')
    names = [l for l in e.read_until(lambda l: l == 'uciok') if l.startswith('option name')]
    e.send(f'setoption name Threads value {threads}')
    e.send('setoption name Hash value 32')
    e.send('setoption name OwnBook value false')
    for o in a.opt:
        k, v = o.split('=', 1)
        if not any(n.startswith(f'option name {k} ') for n in names):
            raise RuntimeError(f'engine does not advertise option {k}')
        e.send(f'setoption name {k} value {v}')
    e.send(f'setoption name SyzygyPath value {a.tables}')
    e.send('isready')
    e.read_until(lambda l: l == 'readyok')


def go(e, fen, spec):
    e.send('position fen ' + fen)
    e.send('go ' + spec)
    return parse_search(e.read_until(lambda l: l.startswith('bestmove')))


def legal(fen, move):
    return chess.Move.from_uci(move) in chess.Board(fen).legal_moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('tables')
    ap.add_argument('exact')
    ap.add_argument('castle')
    ap.add_argument('roots')
    ap.add_argument('out')
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--soak-rows', type=int, default=60)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    check_self_pin()
    a.exe = os.path.abspath(a.exe)
    res = {'searchmoves_given': 0, 'searchmoves_best': 0, 'castling': 0, 'protocol': 0, 'soak': {}, 'failures': []}
    fail = res['failures']
    rng = random.Random(3)

    e = Engine(a.exe, 300.0)
    setup(e, a)
    rows = [json.loads(l) for l in open(a.exact, encoding='utf-8')]
    rows = [r for r in rows if not r.get('unresolved') and r.get('best') is not None and r['clock'] < 100 and ' moves ' not in r['fen'] and len(r['moves']) >= 3]
    rng.shuffle(rows)
    for r in rows[:300]:
        good = [u for u, v in r['moves'].items() if RANK[v] == r['best']]
        others = [u for u, v in r['moves'].items() if RANK[v] != r['best']]
        if not good or not others:
            continue
        s = go(e, r['fen'], 'depth 5 searchmoves ' + ' '.join(others))
        res['searchmoves_given'] += 1
        if s['bestmove'] not in others:
            fail.append(('searchmoves_given', r['fen'], s['bestmove']))
        pick = rng.choice(good)
        mix = [pick] + others[:3]
        s = go(e, r['fen'], 'depth 5 searchmoves ' + ' '.join(mix))
        res['searchmoves_best'] += 1
        if s['bestmove'] != pick:
            fail.append(('searchmoves_best', r['fen'], s['bestmove'], pick))
    for line in list(open(a.castle, encoding='ascii'))[:400]:
        fen = line.strip()
        s = go(e, fen, 'depth 6')
        res['castling'] += 1
        if not legal(fen, s['bestmove']):
            fail.append(('castling', fen, s['bestmove']))

    fens = [l.strip() for l in open(a.roots, encoding='ascii')][:12]
    for fen in fens:
        for script in ('infinite', 'ponder', 'hit', 'mate', 'zero'):
            e.send('position fen ' + fen)
            if script == 'infinite':
                e.send('go infinite')
                e.send('stop')
            elif script == 'ponder':
                e.send('go ponder wtime 1000 btime 1000')
                e.send('stop')
            elif script == 'hit':
                e.send('go ponder wtime 200 btime 200')
                e.send('ponderhit')
            elif script == 'mate':
                e.send('go mate 2')
            else:
                e.send('go nodes 0')
            r = parse_search(e.read_until(lambda l: l.startswith('bestmove')))
            res['protocol'] += 1
            if r['bestmove'] != '0000' and not legal(fen, r['bestmove']):
                fail.append(('protocol', script, fen, r['bestmove']))
        e.send('setoption name SyzygyPath value <empty>')
        off = go(e, fen, 'depth 4')
        e.send(f'setoption name SyzygyPath value {a.tables}')
        on = go(e, fen, 'depth 4')
        res['protocol'] += 2
        if not legal(fen, off['bestmove']) or not legal(fen, on['bestmove']):
            fail.append(('reload', fen, off['bestmove'], on['bestmove']))
    e.quit()

    soak_rows = [l.strip() for l in open(a.roots, encoding='ascii')]
    rng.shuffle(soak_rows)
    soak_rows = soak_rows[:a.soak_rows]
    tb_rows = [r['fen'] for r in rows[:a.soak_rows]]
    for threads in (2, 3, 4):
        e = Engine(a.exe, 300.0)
        setup(e, a, threads)
        n = 0
        for i, fen in enumerate(soak_rows + tb_rows):
            if i % 25 == 24:
                e.send(f'setoption name Hash value {rng.choice((1, 16, 64))}')
            r = go(e, fen, 'movetime 200')
            n += 1
            if not legal(fen, r['bestmove']):
                fail.append(('soak', threads, fen, r['bestmove']))
        e.send('setoption name Threads value 1')
        e.send('bench 13')
        lines = e.read_until(lambda l: 'bench depth' in l)
        res['soak'][str(threads)] = {'searches': n, 'bench13_line': lines[-1].split(' time ')[0]}
        e.quit()
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: (v if k != 'failures' else len(v)) for k, v in res.items()}))
    for f in fail[:10]:
        print('FAIL', f)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
