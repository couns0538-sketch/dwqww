#!/usr/bin/env python3
"""Generate the exact random starting moves for a Job 35 game range."""

from argparse import ArgumentParser
from pathlib import Path
import random

import chess


def opening(game):
    rng = random.Random(game)
    board = chess.Board()
    moves = []
    termination = 'ready'
    for _ in range(8):
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        moves.append(move.uci())
        if board.is_game_over(claim_draw=True):
            termination = board.outcome(claim_draw=True).termination.name.lower()
            break
    return f'{game}\t{" ".join(moves)}\t{termination}\n'


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('first', type=int)
    parser.add_argument('last', type=int)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if not 1 <= args.first <= args.last:
        parser.error('game range must be positive and increasing')
    if chess.__version__ != '1.11.2':
        parser.error('python-chess 1.11.2 required for legal move ordering')
    with args.output.open('x', encoding='ascii', newline='\n') as stream:
        for game in range(args.first, args.last + 1):
            stream.write(opening(game))


if __name__ == '__main__':
    main()
