"""Independently reclassify every selected FEN and check discovery witnesses."""

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

import chess


def read_tsv(path):
    with path.open(encoding='ascii', newline='') as source:
        return list(csv.DictReader(source, delimiter='\t'))


def reclassify(fen):
    board = chess.Board(fen)
    assert board.is_valid() and not board.is_check()
    us = board.turn
    tags = set()
    discoveries = []
    doubles = []
    for move in board.generate_pseudo_legal_moves():
        if board.piece_at(move.to_square) or move.promotion is not None or board.is_en_passant(move):
            continue
        pinned = board.is_pinned(us, move.from_square)
        if not board.is_legal(move):
            if move.from_square == board.king(us):
                tags.add('K')
            if pinned:
                tags.add('X')
            continue
        if pinned and move.to_square in board.pin(us, move.from_square):
            tags.add('P')
        if not board.gives_check(move):
            continue
        moved_squares = {move.to_square}
        vacated_squares = {move.from_square}
        if board.is_castling(move):
            tags.add('C')
            short = move.to_square > move.from_square
            rank = chess.square_rank(move.from_square)
            moved_squares.add(chess.square(5 if short else 3, rank))
            vacated_squares.add(chess.square(7 if short else 0, rank))
        board.push(move)
        enemy_king = board.king(not us)
        checkers = set(board.attackers(us, enemy_king))
        stationary = checkers - moved_squares
        assert all(set(chess.SquareSet(chess.between(enemy_king, square))) & vacated_squares for square in stationary)
        board.pop()
        if move.to_square in checkers:
            tags.add('Q')
        if stationary:
            tags.add('D')
            discoveries.append(move.uci())
            if len(checkers) > 1:
                doubles.append(move.uci())
    return ''.join(tag for tag in 'DQCPXK' if tag in tags), sorted(discoveries), sorted(doubles)


def audit(directory):
    assert chess.__version__ == '1.11.2'
    with (directory / 'receipt.json').open(encoding='ascii') as source:
        receipt = json.load(source)
    for name, expected in receipt['files'].items():
        raw = (directory / name).read_bytes()
        assert len(raw) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], name
    p = read_tsv(directory / 'positions.tsv')
    top = read_tsv(directory / 'top10.tsv')
    eligible = read_tsv(directory / 'eligible.tsv')
    selected = {row['fen']: row for row in p}
    universe = {row['fen']: row for row in eligible}
    witnesses = {row['fen']: row for row in read_tsv(directory / 'discovery_witnesses.tsv')}
    assert len(p) == len(selected) == 2000 and len(eligible) == len(universe)
    assert all(universe[fen] == row for fen, row in selected.items())
    assert top == sorted((row for row in p if 'D' in row['classes']),
                         key=lambda row: (-int(row['discovered_moves']), row['fen']))[:10]
    positions_per_class = Counter()
    total_discovered = total_double = positions_with_double = 0
    for fen, row in selected.items():
        tags, found_discoveries, found_double_checks = reclassify(fen)
        assert tags == row['classes'], fen
        assert len(found_discoveries) == int(row['discovered_moves']), fen
        assert len(found_double_checks) == int(row['double_checks']), fen
        if 'D' in tags:
            evidence = witnesses.pop(fen)
            assert evidence['discovered_uci'].split() == found_discoveries, fen
            assert evidence['double_check_uci'].split() == found_double_checks, fen
        positions_per_class.update(tags)
        total_discovered += len(found_discoveries)
        total_double += len(found_double_checks)
        positions_with_double += bool(found_double_checks)
    assert not witnesses
    return {'verified_legal_and_pseudo_legal_classifications': len(p), 'top_D_ranking_matches': True,
            'class_positions': {tag: positions_per_class[tag] for tag in 'DQCPXK'},
            'discovered_moves': total_discovered, 'double_check_moves': total_double,
            'positions_with_double_check_discovery': positions_with_double}


if __name__ == '__main__':
    print(json.dumps(audit(Path(sys.argv[1])), indent=2))
