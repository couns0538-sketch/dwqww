#!/usr/bin/env python3
"""Extract the first forty piece-rich mate games without emitting player metadata."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path

import chess
import chess.pgn


CHESS_VERSION = '1.11.2'
INPUT_SHA = '9c89d7bbb8ea2b66c24625881775c48a6f4a17e23fd64c5f98b158e6934f41b1'
EXPECTED_OUTPUT_SHA = 'b2131c5af5307ac14174fe30d66780d8007dab68c7fbc6a8b9126f52637389ab'
EXPECTED_FIRST = '2k5/1R3Qp1/ppp4p/8/8/8/PPP2PPP/R2r2K1 w - - 1 33\t45\t3\t17'
EXPECTED_LAST = '1R4n1/pp2k3/q1p3p1/4P3/1P2P1Q1/2P5/P3N1K1/8 w - - 3 31\t512\t7\t16'


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
        pieces = len(rewind.piece_map())
        samples.append((rewind.fen(), game_number, plies_before, pieces))
    return samples


def seven_ply_piece_count(final):
    rewind = final.copy(stack=7)
    for _ in range(7):
        rewind.pop()
    return len(rewind.piece_map())


def piece_bin(pieces):
    if pieces < 12:
        return 'under 12'
    if pieces < 16:
        return '12–15'
    if pieces < 20:
        return '16–19'
    return '20+'


def build(pgn):
    if chess.__version__ != CHESS_VERSION:
        raise ValueError(f'expected python-chess module {CHESS_VERSION}, got {chess.__version__}')
    source_sha = file_sha(pgn)
    if source_sha != INPUT_SHA:
        raise ValueError(f'PGN SHA-256 is {source_sha}, expected {INPUT_SHA}')
    games = 0
    checkmates = 0
    checkmates_long_enough = 0
    eligible = 0
    result_disagreements = 0
    selected = []
    samples = []
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
            checkmates_long_enough += 1
            if seven_ply_piece_count(board) < 14:
                continue
            eligible += 1
            if len(selected) < 40:
                selected.append(games)
                samples.extend(extract_samples(board, moves, games))

    lines = [f'{fen}\t{game}\t{plies}\t{pieces}' for fen, game, plies, pieces in samples]
    content = ('\n'.join(lines) + '\n').encode('ascii') if lines else b''
    result_sha = hashlib.sha256(content).hexdigest()
    labels = ('under 12', '12–15', '16–19', '20+')
    bins = Counter((plies, piece_bin(pieces)) for _, _, plies, pieces in samples)
    piece_histogram = Counter(pieces for _, _, _, pieces in samples)
    receipt = [
        f'python-chess module {chess.__version__}',
        f'input SHA-256 {source_sha}',
        f'games {games}',
        f'final positions checkmated {checkmates}',
        f'checkmated games of at least eight plies {checkmates_long_enough}',
        f'checkmated games qualifying at seven plies before mate {eligible}',
        f'checkmate/recorded-result disagreements {result_disagreements}',
        f'selected game indices {",".join(map(str, selected))}',
        f'positions {len(lines)}',
        'Every sample has the eventual winner to move, and its saved continuation reaches the same final checkmate.',
        'Piece count histogram ' + ', '.join(f'{piece_count}={count}' for piece_count, count in sorted(piece_histogram.items())),
        'All sample bins ' + ', '.join(f'{label}={sum(bins[plies, label] for plies in (3, 5, 7))}' for label in labels),
        *(f'Bins at minus {plies} plies ' + ', '.join(f'{label}={bins[plies, label]}' for label in labels)
          for plies in (3, 5, 7)),
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
    with args.receipt.open('x', encoding='utf-8', newline='\n') as output:
        output.write(receipt)
    print(receipt, end='')


if __name__ == '__main__':
    main()
