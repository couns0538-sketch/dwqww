#!/usr/bin/env python3
"""pgn_positions.py - full-FEN game positions for PGO workloads and identity checks (speed job, own code).

usage: python -I -B pgn_positions.py <games.pgn> <out.tsv> [--games 30] [--per-game 10] [--min-ply 16] [--seed 20261105]

Reads the PGN with python-chess, takes --games games chosen by a seeded shuffle of the game list, and from each game
--per-game positions at evenly spaced plies from --min-ply on (past the opening book). Output: two '#' header lines
(source PGN path + md5, generator settings), then game number, ply, FEN (all six fields), tab separated, in game order
(a workload can keep the TT warm inside one game). Positions with no legal move are skipped. Refuses to overwrite an
existing output. Prints the output md5 and the source's md5 so both can be recorded.
"""
import argparse
import hashlib
import os
import random
import sys

import chess
import chess.pgn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pgn')
    ap.add_argument('out')
    ap.add_argument('--games', type=int, default=30)
    ap.add_argument('--per-game', type=int, default=10)
    ap.add_argument('--min-ply', type=int, default=16)
    ap.add_argument('--seed', type=int, default=20261105)
    a = ap.parse_args()
    offsets = []
    with open(a.pgn, encoding='utf-8', errors='replace') as f:
        while True:
            off = f.tell()
            hdr = chess.pgn.read_headers(f)
            if hdr is None:
                break
            offsets.append(off)
    if not offsets:
        sys.exit('no games in ' + a.pgn)
    rng = random.Random(a.seed)
    order = list(range(len(offsets)))
    rng.shuffle(order)
    rows = []
    used = 0
    with open(a.pgn, encoding='utf-8', errors='replace') as f:
        for gi in order:
            if used >= a.games:
                break
            f.seek(offsets[gi])
            game = chess.pgn.read_game(f)
            if game is None or game.errors:
                continue
            board = game.board()
            fens = []
            for ply, mv in enumerate(game.mainline_moves(), start=1):
                board.push(mv)
                if ply >= a.min_ply and any(True for _ in board.legal_moves):
                    fens.append((ply, board.fen()))
            if len(fens) < a.per_game:
                continue
            step = len(fens) / a.per_game
            pick = [fens[int(i * step)] for i in range(a.per_game)]
            used += 1
            for ply, fen in pick:
                rows.append('%d\t%d\t%s' % (gi, ply, fen))
    src_md5 = hashlib.md5(open(a.pgn, 'rb').read()).hexdigest()
    # provenance header (Code Review SHOULD 3): readers skip lines that start with '#'
    head = ['# pgn_positions.py source %s md5 %s' % (a.pgn.replace('\\', '/'), src_md5),
            '# games %d of %d, per_game %d, min_ply %d, seed %d; columns: game index, ply, FEN (six fields)' % (
                used, len(offsets), a.per_game, a.min_ply, a.seed)]
    data = ('\n'.join(head + rows) + '\n').encode()
    if os.path.exists(a.out):
        sys.exit('refusing to overwrite ' + a.out)
    with open(a.out, 'wb') as f:
        f.write(data)
    print('%d positions from %d games of %d -> %s md5 %s (source md5 %s)' % (
        len(rows), used, len(offsets), a.out, hashlib.md5(data).hexdigest(), src_md5))


if __name__ == '__main__':
    main()
