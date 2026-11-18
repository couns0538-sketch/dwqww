#!/usr/bin/env python3
"""Build the first 1,000 fifth-ply FENs and their legal-move coverage."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import struct

import chess
import chess.pgn


CHESS_VERSION = '1.11.2'
INPUT_SHA = 'd9a02ff4b3128fcbeb39582aec5a350831b40fda6d38010fd630a94498b8a4d0'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
EXPECTED_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
EXPECTED_FIRST = 'r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11'
EXPECTED_LAST = '1nr5/1b3kpp/r3pn2/2p5/1pP5/p3BP2/PPB3PP/2RR1NK1 w - - 0 20'
EXPECTED_COVERAGE = {'king': 984, 'castle': 40, 'en_passant': 1, 'promotion': 25}
MEASURES = (*EXPECTED_COVERAGE, 'king_bucket', 'king_key', 'mirror_only_move')


class StrictGameBuilder(chess.pgn.GameBuilder):
    def handle_error(self, error):
        raise ValueError('malformed PGN game') from None


def read_net(path):
    data = path.read_bytes()
    net_sha = hashlib.sha256(data).hexdigest()
    if net_sha != NET_SHA:
        raise ValueError(f'net SHA-256 is {net_sha}, expected {NET_SHA}')
    fields = struct.unpack_from('<IIIIIIIiii', data, 8)
    if data[:8] != b'FORGENN3' or fields != (3, 192, 768, 768, 8, 8, 2, 255, 64, 400):
        raise ValueError('unexpected net768 header')
    king_map = tuple(data[48:112])
    if any(bucket >= fields[4] for bucket in king_map):
        raise ValueError('out-of-range king bucket in net')
    mirror = bool(fields[6] & 2)
    return king_map, mirror


def king_key(square, color, king_map, mirror):
    relative = square if color == chess.WHITE else square ^ 56
    return king_map[relative], 7 if mirror and chess.square_file(relative) >= 4 else 0


def coverage(board, king_map, mirror):
    color = board.turn
    current_key = king_key(board.king(color), color, king_map, mirror)
    counts = Counter()
    for move in list(board.legal_moves):
        counts['castle'] += board.is_castling(move)
        counts['en_passant'] += board.is_en_passant(move)
        counts['promotion'] += move.promotion is not None
        if board.piece_type_at(move.from_square) != chess.KING:
            continue
        counts['king'] += 1
        board.push(move)
        next_key = king_key(board.king(color), color, king_map, mirror)
        board.pop()
        counts['king_bucket'] += current_key[0] != next_key[0]
        counts['king_key'] += current_key != next_key
        counts['mirror_only_move'] += current_key[0] == next_key[0] and current_key[1] != next_key[1]
    return counts


def sample_games(source, king_map, mirror):
    game_number = 0
    rows = []
    skipped_terminal_samples = 0
    while len(rows) < 1000:
        try:
            game = chess.pgn.read_game(source, Visitor=StrictGameBuilder)
        except ValueError:
            raise ValueError(f'PGN could not be parsed at game {game_number + 1}') from None
        if game is None:
            raise ValueError(f'PGN ended after {game_number} games and {len(rows)} samples')
        game_number += 1
        if 'FEN' not in game.headers:
            raise ValueError(f'game {game_number} has no FEN tag')
        board = game.board()
        if not board.is_valid():
            raise ValueError(f'invalid initial board in game {game_number}')
        for ply, move in enumerate(game.mainline_moves(), 1):
            if not board.is_legal(move):
                raise ValueError(f'illegal move in game {game_number} at ply {ply}')
            board.push(move)
            if ply % 5:
                continue
            if board.is_game_over():
                skipped_terminal_samples += 1
                continue
            rows.append((board.fen(), game_number, ply, board.turn, coverage(board, king_map, mirror)))
            if len(rows) == 1000:
                break
    return rows, game_number, skipped_terminal_samples


def build(input_pgn, input_net):
    if chess.__version__ != CHESS_VERSION:
        raise ValueError(f'expected python-chess module {CHESS_VERSION}, got {chess.__version__}')
    with input_pgn.open('rb') as raw_pgn:
        pgn_sha = hashlib.file_digest(raw_pgn, 'sha256').hexdigest()
    if pgn_sha != INPUT_SHA:
        raise ValueError(f'PGN SHA-256 is {pgn_sha}, expected {INPUT_SHA}')
    king_map, mirror = read_net(input_net)
    with input_pgn.open(encoding='utf-8-sig') as source:
        rows, game_count, skipped = sample_games(source, king_map, mirror)

    positions = ''.join(f'{fen}\n' for fen, *_ in rows).encode('ascii')
    positions_sha = hashlib.sha256(positions).hexdigest()
    by_position = {key: sum(counts[key] > 0 for *_, counts in rows) for key in MEASURES}
    by_move = {key: sum(counts[key] for *_, counts in rows) for key in MEASURES}
    tsv = ['\t'.join(('index', 'game', 'ply', 'turn', *MEASURES))]
    for index, (_, game_number, ply, color, counts) in enumerate(rows, 1):
        tsv.append('\t'.join(map(str, (index, game_number, ply, 'w' if color else 'b',
                                     *(counts[key] for key in MEASURES)))))
    coverage_file = '\n'.join(tsv) + '\n'
    receipt = [
        f'python-chess module {chess.__version__}',
        f'input PGN SHA-256 {pgn_sha}',
        f'input synthetic net768 SHA-256 {NET_SHA}',
        f'synthetic net768 mirror flag {int(mirror)}',
        'synthetic net768 king map, bytes 48–111 in square-index order',
        *(' '.join(map(str, king_map[rank:rank + 8])) for rank in range(0, 64, 8)),
        f'games read {game_count}',
        f'terminal fifth-ply samples skipped {skipped}',
        f'positions {len(rows)}',
        f'positions SHA-256 {positions_sha}',
        f'expected positions SHA-256 {EXPECTED_SHA}',
        f'positions SHA-256 match {positions_sha == EXPECTED_SHA}',
        f'first FEN {rows[0][0]} (game {rows[0][1]}, ply {rows[0][2]})',
        f'first FEN matches {rows[0][0] == EXPECTED_FIRST}',
        f'last FEN {rows[-1][0]} (game {rows[-1][1]}, ply {rows[-1][2]})',
        f'last FEN matches {rows[-1][0] == EXPECTED_LAST}',
        'position-level coverage, at least one legal move of the indicated kind',
        *(f'{key} {by_position[key]} expected {expected} match {by_position[key] == expected}'
          for key, expected in EXPECTED_COVERAGE.items()),
        f'king_bucket {by_position["king_bucket"]}',
        f'king_key {by_position["king_key"]}',
        f'mirror_only_move {by_position["mirror_only_move"]} (may overlap with king_bucket)',
        f'king_key positions without king_bucket {by_position["king_key"] - by_position["king_bucket"]}',
        'king_bucket positions by turn ' + ', '.join(
            f'{label}={sum(color == turn and counts["king_bucket"] > 0 for *_, color, counts in rows)}'
            for label, turn in (('white', chess.WHITE), ('black', chess.BLACK))),
        'move-level totals ' + ', '.join(f'{key}={by_move[key]}' for key in MEASURES),
        f'coverage TSV SHA-256 {hashlib.sha256(coverage_file.encode("ascii")).hexdigest()}',
        'kF src/nnue_v3.cpp:585–588,621–626 reads bucket count, mirror flag and map.',
        'kF include/forge/nnue_v3.hpp:75–78,176–181 uses square for White or square xor 56 for Black, then indexes the map and stores the mirror flip separately.',
        'kF src/search.cpp:3897–3911 checks the full KingKey in the parent-valid path. This fixture counts legal root opportunities. Engine execution is outside this measurement.',
    ]
    return positions, coverage_file, '\n'.join(receipt) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_pgn', type=Path)
    parser.add_argument('input_net', type=Path)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    positions, coverage_file, receipt = build(args.input_pgn, args.input_net)
    with (args.output_dir / 'positions.txt').open('xb') as output:
        output.write(positions)
    with (args.output_dir / 'coverage.tsv').open('x', encoding='ascii', newline='\n') as output:
        output.write(coverage_file)
    with (args.output_dir / 'receipt.txt').open('x', encoding='utf-8', newline='\n') as output:
        output.write(receipt)
    print(receipt, end='')


if __name__ == '__main__':
    main()
