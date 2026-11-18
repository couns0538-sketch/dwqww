#!/usr/bin/env python3
"""Extract the first thirty eligible mate games without emitting player metadata."""

import argparse
import hashlib
from pathlib import Path

import chess
import chess.pgn


CHESS_VERSION = '1.11.2'
INPUT_SHA = '9c89d7bbb8ea2b66c24625881775c48a6f4a17e23fd64c5f98b158e6934f41b1'
EXPECTED_OUTPUT_SHA = 'ce9c50e11ae4a0a7f27b3561bb8677a4551ba2b546e7be11a35a991c547f33b5'
EXPECTED_FIRST = '8/8/8/8/5b2/5kpp/2p5/2B3K1 b - - 1 81\t1\t3'
EXPECTED_LAST = '2K5/8/8/2n4r/8/8/p4ppp/5k2 b - - 7 88\t43\t7'


class StrictGameBuilder(chess.pgn.GameBuilder):
    def handle_error(self, error):
        raise ValueError('malformed PGN game') from None


def file_sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def scan_game(game, game_number):
    board = game.board()
    if not board.is_valid():
        raise ValueError(f'invalid initial board in game {game_number}')
    moves = list(game.mainline_moves())
    for move in moves:
        if not board.is_legal(move):
            raise ValueError(f'illegal main-line move in game {game_number}')
        board.push(move)
    return board, moves


def extract_samples(final, moves, game_number):
    winner = not final.turn
    rewind = final.copy(stack=7)
    samples = []
    for plies_before in range(1, 8):
        rewind.pop()
        if plies_before not in (3, 5, 7):
            continue
        if rewind.turn != winner:
            raise ValueError(f'wrong side to move in game {game_number} at minus {plies_before}')
        replay = rewind.copy(stack=False)
        for move in moves[-plies_before:]:
            if not replay.is_legal(move):
                raise ValueError(f'invalid sampled continuation in game {game_number}')
            replay.push(move)
        if replay.fen() != final.fen() or not replay.is_checkmate() or replay.turn == winner:
            raise ValueError(f'sampled continuation does not replay to checkmate in game {game_number}')
        samples.append(f'{rewind.fen()}\t{game_number}\t{plies_before}')
    return samples


def build(pgn):
    if chess.__version__ != CHESS_VERSION:
        raise ValueError(f'expected python-chess module {CHESS_VERSION}, got {chess.__version__}')
    source_sha = file_sha(pgn)
    if source_sha != INPUT_SHA:
        raise ValueError(f'PGN SHA-256 is {source_sha}, expected {INPUT_SHA}')
    games = 0
    checkmates = 0
    eligible = 0
    result_disagreements = 0
    selected = []
    lines = []
    with pgn.open(encoding='utf-8-sig') as source:
        while True:
            try:
                game = chess.pgn.read_game(source, Visitor=StrictGameBuilder)
            except ValueError:
                raise ValueError(f'PGN could not be parsed at game {games + 1}') from None
            if game is None:
                break
            games += 1
            board, moves = scan_game(game, games)
            if not board.is_checkmate():
                continue
            checkmates += 1
            winner = not board.turn
            expected_result = '1-0' if winner == chess.WHITE else '0-1'
            result_disagreements += (game.headers.get('Result') != expected_result)
            if len(moves) < 8:
                continue
            eligible += 1
            if len(selected) < 30:
                selected.append(games)
                lines.extend(extract_samples(board, moves, games))

    content = ('\n'.join(lines) + '\n').encode('ascii') if lines else b''
    result_sha = hashlib.sha256(content).hexdigest()
    receipt = [
        f'python-chess module {chess.__version__}',
        f'input SHA-256 {source_sha}',
        f'games {games}',
        f'final positions checkmated {checkmates}',
        f'checkmated games of at least eight plies {eligible}',
        f'checkmate/recorded-result disagreements {result_disagreements}',
        f'selected game indices {",".join(map(str, selected))}',
        f'positions {len(lines)}',
        'Every sample has the eventual winner to move, and its saved continuation reaches the same final checkmate.',
        f'positions SHA-256 {result_sha}',
        f'expected SHA-256 {EXPECTED_OUTPUT_SHA}',
        f'positions SHA-256 match {result_sha == EXPECTED_OUTPUT_SHA}',
        f'first line {lines[0] if lines else ""}',
        f'expected first line match {bool(lines) and lines[0] == EXPECTED_FIRST}',
        f'last line {lines[-1] if lines else ""}',
        f'expected last line match {bool(lines) and lines[-1] == EXPECTED_LAST}',
    ]
    return content, '\n'.join(receipt) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_pgn', type=Path)
    parser.add_argument('positions', type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    positions, receipt = build(args.input_pgn)
    with args.positions.open('xb') as output:
        output.write(positions)
    with args.receipt.open('x', encoding='ascii', newline='\n') as output:
        output.write(receipt)
    print(receipt, end='')


if __name__ == '__main__':
    main()
