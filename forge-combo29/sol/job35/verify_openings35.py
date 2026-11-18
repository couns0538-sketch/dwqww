#!/usr/bin/env python3
"""Independently check Job 35 fixture rows and cross-arm byte identity."""

from hashlib import sha256
from pathlib import Path
from random import Random
import sys

import chess


PHASES = (
    ('K25', 1, 20, ('K25a', 'K25b', 'C25')),
    ('U1', 1, 1000, ('U1-r15d', 'U1-kF')),
    ('U2', 1001, 1500, ('U2-r15d', 'U2-kF')),
)


def replay(game, moves):
    rng = Random(game)
    board = chess.Board()
    for token in moves:
        if board.outcome(claim_draw=True):
            raise ValueError(f'game {game} continued after a terminal random position')
        legal = tuple(board.generate_legal_moves())
        selected = legal[rng.randrange(len(legal))]
        if selected.uci() != token:
            raise ValueError(f'game {game}: RNG selected {selected.uci()}, fixture contains {token}')
        board.push(selected)
    outcome = board.outcome(claim_draw=True)
    if not 1 <= len(moves) <= 8 or len(moves) != 8 and not outcome:
        raise ValueError(f'game {game}: random plies do not match the stopping rule')
    return (outcome.termination.name.lower() if outcome else 'ready'), board.fen()


def main():
    if chess.__version__ != '1.11.2':
        raise ValueError('python-chess 1.11.2 required')
    directory = Path(sys.argv[1])
    print(f'Independent readback with python-chess {chess.__version__}.')
    print('Replayed each row with Random(game).randrange indexing generate_legal_moves() in native order.')
    for phase, first, last, arms in PHASES:
        expected_bytes = None
        for arm in arms:
            path = directory / f'{arm}.openings.txt'
            data = path.read_bytes()
            if not data.endswith(b'\n') or b'\r' in data:
                raise ValueError(f'{path} lacks canonical LF newlines')
            rows = data.decode('ascii').splitlines()
            terminals = []
            samples = []
            for game, line in zip(range(first, last + 1), rows, strict=True):
                identifier, trail, state = line.split('\t')
                if identifier != str(game):
                    raise ValueError(f'{path}: wrong identifier {identifier!r} for game {game}')
                observed, fen = replay(game, trail.split())
                if observed != state:
                    raise ValueError(f'{path}: game {game} has incorrect terminal status {state}')
                if state != 'ready':
                    terminals.append((game, len(trail.split()), state))
                if game in (first, last):
                    samples.append((game, trail, fen))
            if expected_bytes is None:
                expected_bytes = data
                for game, trail, fen in samples:
                    print(f'{phase} game {game} opening {trail} -> {fen}')
            elif data != expected_bytes:
                raise ValueError(f'{path} does not match its paired arm bytes')
            print(f'{arm}: {len(rows)} games, {len(data)} bytes, SHA-256 {sha256(data).hexdigest()}, terminal rows {terminals}.')


if __name__ == '__main__':
    main()
