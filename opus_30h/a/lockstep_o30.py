#!/usr/bin/env python3
"""lockstep_o30.py <pgn> <exe A> <exe B> [--opt-b N=V] [--games 3] [--nodes 20000] [--mask 0x2] - Opus 30-h job: are two
engines that should be IDENTICAL in search identical in GAME conditions? Both run in their own long-lived process
(hash, history and correction tables evolve as in a game) and walk the same games from a match PGN ply by ply
(`position startpos moves ...` + `go nodes N`): with identical evaluation and search they must report the same
bestmove, score and node count at every ply. Prints the first divergence per game (if any) and LOCKSTEP PASS / FAIL.
Node limits instead of time make it deterministic (Threads 1). Own code (python-chess for the PGN)."""
import argparse
import ctypes
import os
import re
import sys

import chess.pgn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from depth_probe_o30 import Engine  # noqa: E402


def search(e, moves, nodes):
    e.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
    e.send(f'go nodes {nodes}')
    lines = e.wait('bestmove', 60)
    info = [l for l in lines if l.startswith('info depth')]
    last = info[-1] if info else ''
    sc = re.search(r' score (cp|mate) (-?\d+)', last)
    nd = re.search(r' nodes (\d+)', last)
    return lines[-1].split()[1], (sc.group(1) + ' ' + sc.group(2)) if sc else '?', int(nd.group(1)) if nd else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pgn')
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--opt-b', action='append', default=[])
    ap.add_argument('--games', type=int, default=3)
    ap.add_argument('--nodes', type=int, default=20000)
    ap.add_argument('--mask', default='0x2')
    a = ap.parse_args()
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(int(a.mask, 16))):
        sys.exit('cannot pin (fail closed)')
    games = []
    with open(a.pgn, encoding='utf-8', errors='replace') as f:
        while len(games) < a.games:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            fen = g.headers.get('FEN')
            if fen:   # book openings start from a FEN: replay from the start position is not possible
                b = chess.Board(fen)
                games.append((fen, [m.uci() for m in g.mainline_moves()]))
            else:
                games.append((None, [m.uci() for m in g.mainline_moves()]))
    ea, eb = Engine(a.a, []), Engine(a.b, a.opt_b)
    plies = diverged = 0
    for gi, (fen, moves) in enumerate(games):
        for e in (ea, eb):
            e.send('ucinewgame')
            e.send('isready')
            e.wait('readyok')
        first = None
        for i in range(len(moves)):
            prefix = moves[:i]
            ra = search_fen(ea, fen, prefix, a.nodes)
            rb = search_fen(eb, fen, prefix, a.nodes)
            plies += 1
            if ra != rb and first is None:
                first = (i, ra, rb)
        if first:
            diverged += 1
            print(f'game {gi + 1}: FIRST DIVERGENCE at ply {first[0]}: A {first[1]} vs B {first[2]}')
        else:
            print(f'game {gi + 1}: {len(moves)} plies identical (bestmove, score, nodes)')
    ea.quit()
    eb.quit()
    print(f"LOCKSTEP {'PASS' if diverged == 0 else 'FAIL'}: {len(games)} games, {plies} plies, {diverged} game(s) diverged")
    sys.exit(1 if diverged else 0)


def search_fen(e, fen, moves, nodes):
    if fen is None:
        return search(e, moves, nodes)
    e.send(f'position fen {fen}' + (' moves ' + ' '.join(moves) if moves else ''))
    e.send(f'go nodes {nodes}')
    lines = e.wait('bestmove', 60)
    info = [l for l in lines if l.startswith('info depth')]
    last = info[-1] if info else ''
    sc = re.search(r' score (cp|mate) (-?\d+)', last)
    nd = re.search(r' nodes (\d+)', last)
    return lines[-1].split()[1], (sc.group(1) + ' ' + sc.group(2)) if sc else '?', int(nd.group(1)) if nd else -1


if __name__ == '__main__':
    main()
