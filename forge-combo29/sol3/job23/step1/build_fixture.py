#!/usr/bin/env python3
"""Construct the deterministic Job 23 quiet-move fixture and its receipts."""

import argparse
from collections import Counter, deque
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import chess


PYTHON_CHESS = '1.11.2'
W1_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
AU_SHA = '1ca69d39b8cf43b1a109b49efc56de66d37be571df2c6f7609e83cf34c754e5e'
CLASSES = 'DQCPXK'
FIELDS = ('fen', 'classes', 'discovered_moves', 'double_checks')
LIMIT = 2000


@dataclass(frozen=True)
class Row:
    fen: str
    tags: str
    discoveries: tuple[str, ...]
    double_checks: tuple[str, ...]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs(w1, r15d_games, kf_games):
    w1_bytes = w1.read_bytes()
    if sha(w1_bytes) != W1_SHA:
        raise ValueError('unrecognized W1 fixture')
    w1_lines = w1_bytes.decode('ascii').splitlines()
    w1_set = set(w1_lines)
    if len(w1_lines) != 1000 or len(w1_set) != 990:
        raise ValueError('expected 1,000 W1 input rows, of which 990 are distinct six-field FENs')
    r15d_raw, kf_raw = [path.read_bytes() for path in (r15d_games, kf_games)]
    if r15d_raw != kf_raw or sha(r15d_raw) != AU_SHA:
        raise ValueError('AU game transcripts differ or do not match the expected input')
    games = set()
    game_occurrences = 0
    endpoint_counts = Counter()
    path_table = csv.DictReader(r15d_raw.decode('ascii').splitlines(), delimiter='\t')
    root_indices = []
    for entry in path_table:
        index = int(entry['w1_position'])
        root_indices.append(index)
        tokens = entry['moves'].split()
        if (entry['phase'] != 'au-games' or entry['threads'] != '1' or len(tokens) > 200
                or len(tokens) != int(entry['plies'])):
            raise ValueError(f'bad AU fixture metadata at W1 row {index}')
        board = chess.Board(w1_lines[index - 1])
        games.add(board.fen())
        game_occurrences += 1
        for ply, token in enumerate(tokens, 1):
            if board.is_game_over(claim_draw=True):
                raise ValueError(f'AU W1 row {index} continued past termination before ply {ply}')
            move = board.parse_uci(token)
            if not move:
                raise ValueError(f'null AU W1 row {index}, ply {ply}')
            board.push(move)
            games.add(board.fen())
            game_occurrences += 1
        outcome = board.outcome(claim_draw=True)
        termination = outcome.termination.name if outcome else 'PLY_CAP'
        if termination != entry['termination'] or (outcome.result() if outcome else '*') != entry['result']:
            raise ValueError(f'AU termination mismatch at W1 row {index}')
        if outcome is None and len(tokens) != 200:
            raise ValueError(f'nonterminal AU W1 row {index} ended before the ply cap')
        endpoint_counts[termination] += 1
    if root_indices != list(range(201, 211)):
        raise ValueError('the AU games do not cover rows 201 to 210 in fixture order')
    details = {
        'python_chess': PYTHON_CHESS, 'w1_sha256': W1_SHA, 'au_each_games_sha256': AU_SHA,
        'w1_rows': len(w1_lines), 'w1_distinct_full_fens': len(w1_set), 'au_game_lists_byte_identical': True,
        'au_games': len(root_indices), 'au_moves': game_occurrences - len(root_indices),
        'au_board_occurrences_including_both_endpoints': game_occurrences, 'au_distinct_full_fens': len(games),
        'au_endings': dict(endpoint_counts), 'w1_au_overlap': len(w1_set & games),
    }
    return w1_set | games, details


def candidate_fens(roots):
    children = set()
    edges = 0
    checked_roots = 0
    for fen in sorted(roots):
        board = chess.Board(fen)
        if not board.is_valid() or board.fen() != fen:
            raise ValueError(f'invalid or noncanonical seed FEN {fen!r}')
        checked_roots += board.is_check()
        for move in list(board.legal_moves):
            board.push(move)
            children.add(board.fen())
            board.pop()
            edges += 1
    details = {'distinct_seed_fens': len(roots), 'seed_fens_in_check_expanded': checked_roots,
               'legal_seed_to_child_edges': edges, 'distinct_child_fens': len(children),
               'seed_child_overlap': len(roots & children), 'distinct_seed_and_child_fens': len(roots | children)}
    return roots | children, details


def is_quiet(board, move):
    return move.promotion is None and not board.is_capture(move)


def classify(board, fen):
    pinned = {}
    for square in chess.scan_forward(board.occupied_co[board.turn] & ~board.kings):
        line = board.pin_mask(board.turn, square)
        if line != chess.BB_ALL:
            pinned[square] = line
    king = board.king(board.turn)
    legal = [move for move in board.legal_moves if is_quiet(board, move)]
    legal_set = set(legal)
    classes = set()
    for move in board.generate_pseudo_legal_moves():
        if (move.from_square == king or move.from_square in pinned) and move not in legal_set and is_quiet(board, move):
            classes.add('K' if move.from_square == king else 'X')

    discoveries = []
    doubles = []
    c_direct_rook = 0
    c_stationary = 0
    for move in legal:
        destination = chess.BB_SQUARES[move.to_square]
        if pinned.get(move.from_square, 0) & destination:
            classes.add('P')
        castle = board.is_castling(move)
        moved = destination
        rook_destination = 0
        if castle:
            rank = chess.square_rank(move.from_square)
            file = 5 if board.is_kingside_castling(move) else 3
            rook_destination = chess.BB_SQUARES[chess.square(file, rank)]
            moved |= rook_destination
        board.push(move)
        checkers = board.checkers_mask()
        board.pop()
        if not checkers:
            continue
        if checkers & destination:
            classes.add('Q')
        stationary = checkers & ~moved
        if stationary:
            classes.add('D')
            discoveries.append(move.uci())
            if checkers.bit_count() >= 2:
                doubles.append(move.uci())
        if castle:
            classes.add('C')
            c_direct_rook += bool(checkers & rook_destination)
            c_stationary += bool(stationary)
    tags = ''.join(tag for tag in CLASSES if tag in classes)
    return Row(fen, tags, tuple(sorted(discoveries)), tuple(sorted(doubles))), c_direct_rook, c_stationary


def enumerate_eligible(fens):
    rows = []
    counts = Counter()
    for fen in sorted(fens):
        board = chess.Board(fen)
        if board.is_check():
            counts['in_check_excluded'] += 1
            continue
        counts['eligible_for_classification_not_in_check'] += 1
        row, castling_rook, castling_stationary = classify(board, fen)
        counts['legal_checking_castles_with_relocated_rook_checker'] += castling_rook
        counts['legal_checking_castles_with_stationary_checker'] += castling_stationary
        if row.tags:
            rows.append(row)
    return rows, dict(counts)


def discovery_rank(row):
    return -len(row.discoveries), row.fen


def select(rows):
    by_discovery = sorted((row for row in rows if 'D' in row.tags), key=discovery_rank)
    selected = by_discovery[:10]
    seen = {row.fen for row in selected}
    counts = Counter(tag for row in selected for tag in row.tags)
    ordered = sorted(rows, key=lambda row: (-len(row.tags), sha(row.fen.encode('ascii')), row.fen))
    queues = {tag: deque(row for row in ordered if tag in row.tags) for tag in CLASSES}
    scarcity = {tag: len(queue) for tag, queue in queues.items()}
    while len(selected) < min(LIMIT, len(rows)):
        for queue in queues.values():
            while queue and queue[0].fen in seen:
                queue.popleft()
        tag = min((tag for tag, queue in queues.items() if queue),
                  key=lambda tag: (counts[tag], scarcity[tag], CLASSES.index(tag)))
        row = queues[tag].popleft()
        selected.append(row)
        seen.add(row.fen)
        counts.update(row.tags)
    return selected


def write_rows(path, rows):
    with path.open('x', encoding='ascii', newline='') as out:
        writer = csv.writer(out, delimiter='\t', lineterminator='\n')
        writer.writerow(FIELDS)
        writer.writerows((row.fen, row.tags, len(row.discoveries), len(row.double_checks)) for row in rows)


def coverage(rows):
    tags = Counter(tag for row in rows for tag in row.tags)
    return {'rows': len(rows), 'class_positions': {tag: tags[tag] for tag in CLASSES},
            'tag_combinations': dict(sorted(Counter(row.tags for row in rows).items())),
            'positions_with_double_check_discovery': sum(bool(row.double_checks) for row in rows),
            'legal_discovered_moves': sum(len(row.discoveries) for row in rows),
            'legal_discovered_double_check_moves': sum(len(row.double_checks) for row in rows)}


def build(args):
    if chess.__version__ != PYTHON_CHESS:
        raise ValueError(f'expected python-chess module {PYTHON_CHESS}, got {chess.__version__}')
    roots, input_details = inputs(args.w1, args.r15d_games, args.kf_games)
    fens, provenance = candidate_fens(roots)
    eligible, eligibility = enumerate_eligible(fens)
    positions = select(eligible)
    top10 = sorted((row for row in positions if 'D' in row.tags), key=discovery_rank)[:10]

    args.out.mkdir(parents=True, exist_ok=False)
    for name, rows in (('positions.tsv', positions), ('top10.tsv', top10), ('eligible.tsv', eligible)):
        write_rows(args.out / name, rows)
    with (args.out / 'discovery_witnesses.tsv').open('x', encoding='ascii', newline='') as out:
        writer = csv.writer(out, delimiter='\t', lineterminator='\n')
        writer.writerow(('fen', 'discovered_uci', 'double_check_uci'))
        writer.writerows((row.fen, ' '.join(row.discoveries), ' '.join(row.double_checks))
                         for row in positions if 'D' in row.tags)

    report = {**input_details, **provenance, **eligibility, 'eligible': coverage(eligible), 'selected': coverage(positions),
              'selected_from_original_seeds': sum(row.fen in roots for row in positions),
              'top10': [{'rank': index, 'fen': row.fen, 'classes': row.tags,
                         'discovered_moves': len(row.discoveries), 'double_checks': len(row.double_checks)}
                        for index, row in enumerate(top10, 1)],
              'policy': [
                  'Deduplicate exact six-field board.fen() strings, including both clocks and canonical legal en-passant square.',
                  'Include root and final boards of both byte-identical AU paths once per game; expand every distinct seed by every legal move before excluding in-check candidates.',
                  'Quiet means a noncapture and nonpromotion. A stationary checking piece contributes D; the moved piece on its destination contributes Q. The relocated castling rook contributes C when castling gives check and is excluded from D. A castling move can independently contribute D if a stationary piece gives check.',
                  'Count each legal discovered-check move once, and separately flag discoveries with at least two checking pieces.',
                  'Seed P with the top ten D rows, then repeatedly choose the least represented class still available, breaking ties by lower class support and canonical class order. Prefer greater tag overlap, then ascending SHA-256 of FEN, then FEN.',
                  'Rank R2 by descending legal discovered-move count with lexicographic FEN ties.',
              ],
              'files': {path.name: {'size': path.stat().st_size, 'sha256': sha(path.read_bytes())}
                        for path in sorted(args.out.iterdir())}}
    payload = json.dumps(report, indent=2) + '\n'
    (args.out / 'receipt.json').write_text(payload, encoding='ascii')
    print(payload, end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('w1', 'r15d-games', 'kf-games', 'out'):
        parser.add_argument('--' + flag, type=Path, required=True)
    build(parser.parse_args())
