#!/usr/bin/env python3
"""Build the Job 9 position-parser fixture from prior warm-game commands."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

import chess


TRACE_SHA = '7d824fe1e2be9cac0986b06a42a5714997233b1f0777d943db03589b24ed3c13'
SEED = 2026111809
FORK_BASE = 'position startpos moves e2e4 e7e5 g1f3'
FORK_NEXT = 'position startpos moves e2e4 e7e5 g1h3'
PARTIAL = 'r3k2r/8/8/8/8/8/8/R3K2R b Kq - 17 30'
HIGH_CLOCK = '8/8/8/8/8/1k6/8/R5K1 b - - 97 63'
LONG_ROOT = 'r3k1nr/P2p4/8/4P3/8/8/8/RN2K1NR w KQkq - 0 1'
REPEAT = 'b1c3 g8f6 c3b1 f6g8'.split()
LONG_TAIL = 'g1f3 e8c8 e1g1 d7d5 e5d6 g8f6'.split()


def fen(board):
    return board.fen(en_passant='fen')


def add_moves(root, moves):
    return root + (' moves ' + ' '.join(moves) if moves else '')


def load_trace(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != TRACE_SHA:
        raise ValueError('incorrect Job 8 Step 1 trace SHA-256')
    games = [[] for _ in range(60)]
    for line in raw.splitlines():
        entry = json.loads(line)
        command = entry['position']
        prefix = 'position startpos moves '
        if not command.startswith(prefix):
            raise ValueError(f'expected historical startpos command: {command}')
        moves = command[len(prefix):].split()
        game = entry['game']
        group = games[game]
        if len(moves) != entry['ply']:
            raise ValueError(f'game {game} move count disagrees with its ply')
        if group:
            previous, previous_moves = group[-1]
            if moves != previous_moves + [previous['bestmove']]:
                raise ValueError(f'game {game} has a non-growing position history')
        elif len(moves) != 8:
            raise ValueError(f'game {game} does not start after eight opening moves')
        group.append((entry, moves))
    if any(not game for game in games) or sum(map(len, games)) != 8612:
        raise ValueError('expected all 8,612 positions of 60 warm games')
    return games


def emit(rows, kind, command):
    index = len(rows) + 1
    rows.append({'index': index, 'kind': kind, 'position': command, 'before': []})
    return index


def check_position(command):
    fields = command.split()
    if fields[:2] == ['position', 'startpos']:
        board = chess.Board()
        suffix = fields[2:]
    elif fields[:2] == ['position', 'fen']:
        board = chess.Board(' '.join(fields[2:8]))
        suffix = fields[8:]
    else:
        raise ValueError(f'unsupported position syntax: {command}')
    if not board.is_valid() or (suffix and suffix[0] != 'moves'):
        raise ValueError(f'invalid position fixture: {command}')
    events = {
        'plies': 0, 'illegal': None, 'unread_tokens': [], 'repetition': False,
        'castles': [], 'en_passant': [], 'promotions': [],
    }
    for index, token in enumerate(suffix[1:]):
        try:
            move = board.parse_uci(token)
        except ValueError:
            events['illegal'] = token
            events['unread_tokens'] = suffix[index + 2:]
            break
        if board.is_castling(move):
            color = 'white' if board.turn else 'black'
            side = 'kingside' if board.is_kingside_castling(move) else 'queenside'
            events['castles'].append(f'{color} {side}')
        if board.is_en_passant(move):
            events['en_passant'].append(token)
        if move.promotion:
            events['promotions'].append(chess.piece_symbol(move.promotion))
        board.push(move)
        events['plies'] += 1
        events['repetition'] |= board.is_repetition(3)
    events['result_fen'] = fen(board)
    return events


def special_positions(rows, games, rng):
    evidence = []

    def add(kind, command, illegal=None):
        index = emit(rows, kind, command)
        events = check_position(command)
        if events['illegal'] != illegal:
            raise ValueError(f'row {index} expected illegal token {illegal!r}: {command}')
        evidence.append({'index': index, 'kind': kind, **events})
        return events

    first = add('fork_base', FORK_BASE)
    second = add('fork_next', FORK_NEXT)
    if first['result_fen'] == second['result_fen']:
        raise ValueError('control-opening fork must reach a different placement')
    add('noncanonical_whitespace', 'position startpos moves e2e4\t e7e5  g1h3')

    for amount in (1, 2, 10):
        group = rng.choice([game for game in games if len(game[-1][1]) > 25])
        long = rng.choice([moves for _, moves in group if len(moves) >= 25])
        add(f'takeback_{amount}_long', add_moves('position startpos', long))
        add(f'takeback_{amount}_short', add_moves('position startpos', long[:-amount]))
        add(f'takeback_{amount}_regrow', add_moves('position startpos', long))

    invalid = 'position startpos moves e2e4 e7e5 g1g5'
    invalid_events = add('illegal_move', invalid, illegal='g1g5')
    continued = add('continued_past_illegal', invalid + ' b8c6', illegal='g1g5')
    if (continued['result_fen'] != invalid_events['result_fen'] or
            continued['unread_tokens'] != ['b8c6']):
        raise ValueError('illegal continuation failed to preserve the legal prefix')
    add('legal_recovery', 'position startpos moves e2e4 e7e5 g1f3 b8c6')

    add('fen_black_partial_rights', 'position fen ' + PARTIAL)
    add('fen_black_partial_rights_grow', add_moves('position fen ' + PARTIAL, ['e8c8', 'e1g1']))
    add('fen_high_halfmove', 'position fen ' + HIGH_CLOCK)
    clock = add('fen_high_halfmove_grow', add_moves('position fen ' + HIGH_CLOCK, ['b3c4', 'a1a2', 'c4d5']))
    if int(clock['result_fen'].split()[4]) != 100:
        raise ValueError('high-clock fixture did not reach halfmove 100')
    ep = chess.Board()
    for move in ['e2e4', 'a7a6', 'e4e5', 'd7d5']:
        ep.push_uci(move)
    ep_root = 'position fen ' + fen(ep)
    add('fen_en_passant', ep_root)
    add('fen_en_passant_grow', add_moves(ep_root, ['e5d6', 'g8f6']))

    repeat_counts = rng.sample([5, 6, 7, 8], 4)
    for promotion, repeats in zip('qrbn', repeat_counts, strict=True):
        full = REPEAT * repeats + LONG_TAIL + ['a7a8' + promotion]
        root = 'position fen ' + LONG_ROOT
        for length in (len(REPEAT) * repeats, len(full) - 1, len(full)):
            event = add(f'long_{promotion}_{length}', add_moves(root, full[:length]))
        if (event['plies'] < 27 or not event['repetition'] or
                event['castles'] != ['black queenside', 'white kingside'] or
                event['en_passant'] != ['e5d6'] or event['promotions'] != [promotion]):
            raise ValueError(f'long promotion-{promotion} coverage missing')
    return evidence


def warm_positions(rows, games):
    warm_indexes = []
    placement_digest = hashlib.sha256()
    for game, group in enumerate(games):
        start = chess.Board()
        first_opening = group[0][1]
        for move in first_opening[:7]:
            start.push_uci(move)
        root_fen = fen(start)
        fen_board = chess.Board(root_fen)
        if fen_board.turn != chess.BLACK:
            raise ValueError(f'game {game} FEN-root color is not black')
        start_rows = []
        fen_rows = []
        last_ply = 7
        for entry, moves in group:
            for move in moves[last_ply:]:
                start.push_uci(move)
                fen_board.push_uci(move)
            last_ply = len(moves)
            expected = fen(start)
            if expected != fen(fen_board):
                raise ValueError(f'game {game} ply {last_ply} FEN root reaches a different placement')
            placement_digest.update(f'{game}\t{last_ply}\t{expected}\n'.encode())
            start_rows.append(entry['position'])
            fen_rows.append(add_moves('position fen ' + root_fen, moves[7:]))
        for kind, commands in (('warm_startpos', start_rows), ('warm_fen', fen_rows)):
            for offset, command in enumerate(commands):
                index = emit(rows, kind, command)
                if offset:
                    warm_indexes.append(index)
    return warm_indexes, placement_digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('stream', type=Path)
    parser.add_argument('coverage', type=Path)
    args = parser.parse_args()
    rng = random.Random(SEED)
    games = load_trace(args.trace)
    rows = []
    specials = special_positions(rows, games, rng)
    warm_indexes, paired_placement_digest = warm_positions(rows, games)
    before = (
        ('go depth 4',),
        ('go nodes 2000',),
        ('setoption name Hash value 16', 'isready'),
        ('ucinewgame', 'isready'),
    )
    injections = sorted(rng.sample(warm_indexes, 12))
    for index, commands in zip(injections, before * 3, strict=True):
        rows[index - 1]['before'].extend(commands)
    counts = Counter(row['kind'] for row in rows)
    if (counts['warm_startpos'] != 8612 or counts['warm_fen'] != 8612 or
            rows[0]['position'] != FORK_BASE or rows[1]['position'] != FORK_NEXT):
        raise ValueError('warm coverage or initial control fork changed')
    digest = hashlib.sha256()
    with args.stream.open('xb') as output:
        for row in rows:
            line = (json.dumps(row, separators=(',', ':')) + '\n').encode()
            output.write(line)
            digest.update(line)
    coverage = {
        'seed': SEED,
        'python_chess_version': chess.__version__,
        'source_trace_sha256': TRACE_SHA,
        'stream_sha256': digest.hexdigest(),
        'position_commands': len(rows),
        'fixed_commands_after_each_position': ['go perft 1', 'eval', 'isready'],
        'positions_by_kind': dict(sorted(counts.items())),
        'games': len(games),
        'warm_black_to_move_fen_roots': len(games),
        'warm_pairs_with_identical_final_fen': counts['warm_startpos'],
        'warm_pair_game_ply_fen_sha256': paired_placement_digest,
        'takeback_lengths': [1, 2, 10],
        'partial_castling_fen': PARTIAL,
        'high_halfmove_fen': HIGH_CLOCK,
        'first_fork_commands': [FORK_BASE, FORK_NEXT],
        'before_injections': [{'index': i, 'commands': rows[i - 1]['before']} for i in injections],
        'special_coverage': specials,
    }
    with args.coverage.open('x') as output:
        json.dump(coverage, output, indent=2)
        output.write('\n')
    print(f'{len(rows)} position commands SHA-256 {digest.hexdigest()}')


if __name__ == '__main__':
    main()
