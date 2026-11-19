#!/usr/bin/env python3
"""Independently read Job 38 fastchess PGNs, node fields and archived bytes."""

import argparse
from dataclasses import dataclass
from hashlib import file_digest, sha256
from itertools import islice, zip_longest
import json
from pathlib import Path
import re
import subprocess

import chess


BOOK = Path('/workspace/work/sol-job12/UHO_Lichess_4852_v1.epd')
BOOK_SHA = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
PC20_SHA = 'e355dbddb98abb000283ca7b37126e4cf71e152ce6df0bec8f1ea11fb715c7af'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
FASTCHESS_SHA = 'fb945c0930ff17786ccc1c07267930e1c0a6098f9bb16dcd13be20a11baec72e'
FASTCHESS_REVISION = 'd7b47e8dec6b564aaf4cbb2922ab37e6c6761e75'
FASTCHESS_VERSION = 'fastchess alpha 1.8.3 20261107-d7b47e8'
ENGINE_SHA = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
ARCHIVE = Path('forge-combo29/sol/job38/raw')
LIMIT = 20_000_000
CHECKSUM = '30ab43b4ba5db5f3'
ARMS = ('X1', 'X2')
PLAN = {
    'K38a': ('r15d', 4001, 10, 20_000, 93),
    'K38b': ('r15d', 4001, 10, 20_000, 93),
    'C38': ('r15d', 4001, 10, 20_000, 60),
    'G20-r15d': ('r15d', 4011, 300, 20_000, 93),
    'G20-kF': ('kF', 4011, 300, 20_000, 93),
    'G50-r15d': ('r15d', 4311, 150, 50_000, 93),
    'G50-kF': ('kF', 4311, 150, 50_000, 93),
    'G250-r15d': ('r15d', 4461, 24, 250_000, 93),
    'G250-kF': ('kF', 4461, 24, 250_000, 93),
}
COMPARE = {
    'K38': ('K38a', 'K38b'),
    'C38': ('K38a', 'C38'),
    **{stage: (f'{stage}-r15d', f'{stage}-kF') for stage in ('G20', 'G50', 'G250')},
}
GAME = re.compile(r'(?m)(?=^\[Event ")')
TAG = re.compile(r'\[([^ ]+) "((?:[^"\\]|\\.)*)"\]')
MOVE = re.compile(r'\s*(?:(\d+)(\.{3}|\.)\s+)?(\S+)\s+\{([^{}]*)\}')
NODES = re.compile(r'(?:^|, )n=(\d+)(?=,|$)')
START = re.compile(r'^Started game (\d+) of (\d+) \((\S+) vs (\S+)\)$', re.M)
FINISH = re.compile(r'^Finished game (\d+) \((\S+) vs (\S+)\): (1-0|0-1|1/2-1/2) \{([^{}]+)\}$', re.M)
ACTIVE = re.compile(r'^info string NNUE v3 active: .* checksum ' + CHECKSUM + r' ', re.M)


@dataclass(frozen=True)
class Game:
    fen: str
    opening: int
    moves: tuple[str, ...]
    nodes: tuple[int | None, ...]


def opening_suite():
    with BOOK.open('rb') as book:
        assert file_digest(book, 'sha256').hexdigest() == BOOK_SHA, BOOK
    with BOOK.open(encoding='ascii') as book:
        positions = {index: line.strip() for index, line in enumerate(islice(book, 4000, 4484), 4001)}
    assert len(positions) == len(set(positions.values())) == 484
    for number, fen in positions.items():
        board = chess.Board(fen)
        assert board.is_valid() and not board.is_game_over() and board.fen() == fen, (number, fen)
    return positions


def compare_archive(data, path, args):
    archive = subprocess.check_output(['git', '-C', str(args.repo), 'show', f'{args.rev}:{path.as_posix()}'])
    assert archive == data, (args.rev, path)


def read_bytes(path, args, allow_empty=False):
    data = path.read_bytes()
    assert (allow_empty or data) and len(data) <= LIMIT, path
    if args.repo is not None:
        compare_archive(data, args.archive / path.relative_to(args.raw), args)
    return data


def argv_group(command, flag):
    start = command.index(flag) + 1
    end = next((i for i in range(start, len(command)) if command[i].startswith('-')), len(command))
    return command[start:end]


def verify_argv(argv, meta, opening, count, nodes, lmr):
    assert argv[0] == meta['fastchess']
    assert set(argv_group(argv, '-each')) >= {'proto=uci', f'nodes={nodes}', 'restart=on'}
    assert set(argv_group(argv, '-openings')) >= {f'file={BOOK}', 'format=epd', 'order=sequential', f'start={opening}'}
    assert set(argv_group(argv, '-pgnout')) >= {'nodes=true'}
    assert argv_group(argv, '-rounds') == [str(count)] and argv_group(argv, '-games') == ['1']
    assert meta['concurrency'] == meta['nproc'] - 1 and argv_group(argv, '-concurrency') == [str(meta['concurrency'])]
    assert argv.count('-engine') == 2 and '-noswap' in argv
    for omitted in ('-recover', '-repeat', '-sprt', '-resign', '-draw'):
        assert omitted not in argv, omitted
    for i, name in zip((i for i, argument in enumerate(argv) if argument == '-engine'), ARMS, strict=True):
        end = next((j for j in range(i + 1, len(argv)) if argv[j].startswith('-')), len(argv))
        settings = argv[i + 1:end]
        assert f'cmd={meta["exe"]}' in settings
        for setting in (f'name={name}', 'option.Threads=1', 'option.Hash=16', 'option.OwnBook=false',
                        f'option.LmrQuietBase={lmr}', 'option.NNUEArch=true'):
            assert setting in settings, (name, setting)
        net_option = next(option for option in settings if option.startswith('option.NNUEArchFile='))
        assert Path(net_option.split('=', 1)[1]).name == 'net768.nnue'
        options = ['setoption name ' + setting.removeprefix('option.').replace('=', ' value ', 1)
                   for setting in settings if setting.startswith('option.')]
        assert options == meta['settings'] and options[-2:] == [
            f'setoption name NNUEArchFile value {net_option.split("=", 1)[1]}', 'setoption name NNUEArch value true'
        ], (name, options)
        assert options[:2] == ['setoption name Threads value 1', 'setoption name Hash value 16']
        pc20 = '\n'.join(options[2:-2]).replace(f'LmrQuietBase value {lmr}', 'LmrQuietBase value 93') + '\n'
        assert sha256(pc20.encode()).hexdigest() == meta['pc20_sha256'] == PC20_SHA, name


def console_games(log, total, match):
    starts = START.findall(log)
    finishes = FINISH.findall(log)
    seen = set()
    for game, count, white, black in starts:
        number = int(game)
        assert number not in seen and 1 <= number <= total and int(count) == total and (white, black) == ARMS, (
            match, game, count, white, black)
        seen.add(number)
    finished = {}
    for game, white, black, outcome, reason in finishes:
        number = int(game)
        assert number not in finished and number in seen and (white, black) == ARMS, (match, game, white, black)
        finished[number] = (outcome, reason)
    return seen, finished


def read_game(pgn, positions, opening_start, finished):
    header, movetext = pgn.split('\n\n', 1)
    tags = {}
    for line in header.splitlines():
        parsed = TAG.fullmatch(line)
        assert parsed and parsed[1] not in tags, line
        tags[parsed[1]] = parsed[2]
    round_number = int(tags['Round'])
    opening = opening_start + round_number - 1
    fen = tags['FEN']
    board = chess.Board(fen)
    outcome, reason = finished[round_number]
    assert fen == positions[opening] == board.fen(), (opening, fen, positions[opening])
    assert tags.get('SetUp') == '1' and tags.get('Termination') == 'normal' and tags.get('TimeControl') == '-', tags
    assert (tags['White'], tags['Black']) == ARMS and tags['Result'] == outcome, tags
    if 'GameId' in tags:
        assert int(tags['GameId']) == round_number, tags

    moves, nodes = [], []
    last = None
    offset = 0
    for token in MOVE.finditer(movetext):
        assert token.start() == offset, (opening, movetext[offset:token.start()])
        offset = token.end()
        number, dots, san, comment = token.groups()
        if number:
            assert int(number) == board.fullmove_number and dots == ('.' if board.turn else '...'), (opening, token[0])
        move = board.parse_san(san)
        assert move in board.legal_moves, (opening, board.fen(), san)
        fields = NODES.findall(comment)
        assert len(fields) <= 1, (opening, comment)
        nodes.append(int(fields[0]) if fields else None)
        moves.append(move.uci())
        board.push(move)
        last = comment
    assert movetext[offset:].strip() == outcome and len(moves) == int(tags['PlyCount']), (opening, movetext[offset:])
    if last is not None:
        assert last.endswith(', ' + reason), (opening, last, reason)
    return round_number, Game(fen, opening, tuple(moves), tuple(nodes))


def move_bytes(games):
    return ''.join(f"{game.fen}{' ' + ' '.join(game.moves) if game.moves else ''}\n"
                   for game in sorted(games.values(), key=lambda game: game.fen)).encode('ascii')


def read_run(match, positions, args):
    meta_path = args.raw / f'{match}.meta'
    if not meta_path.is_file():
        assert not any((args.raw / f'{match}.{ext}').is_file() for ext in ('pgn', 'out')), match
        return {'status': 'not played'}, {}
    meta = json.loads(read_bytes(meta_path, args))
    build, opening, count, nodes, lmr = PLAN[match]
    assert meta['match'] == match and meta['status'] in ('complete', 'interrupted', 'failed'), meta
    assert (meta['build'], meta['opening_start'], meta['games_requested'], meta['nodes'], meta['lmr_quiet_base']) == (
        build, opening, count, nodes, lmr), meta
    assert meta['restart'] is meta['pgn_nodes'] is meta['x1_always_white'] is True, meta
    assert meta['adjudication'] is meta['recover'] is False and meta['timecontrol'] is None, meta
    assert meta['book_sha256'] == BOOK_SHA and meta['net_checksum'] == CHECKSUM, meta
    assert meta['exe_sha256'] == ENGINE_SHA[build] and meta['net_sha256'] == NET_SHA, meta
    assert meta['fastchess_sha256'] == FASTCHESS_SHA and meta['fastchess_revision'] == FASTCHESS_REVISION, meta
    assert meta['fastchess_version'] == FASTCHESS_VERSION and meta['opening_end'] == opening + count - 1, meta
    verify_argv(meta['fastchess_command'], meta, opening, count, nodes, lmr)

    raw = {}
    for ext in ('pgn', 'out'):
        path = args.raw / f'{match}.{ext}'
        if path.is_file():
            data = read_bytes(path, args, allow_empty=(ext == 'pgn'))
            assert (len(data), sha256(data).hexdigest()) == (meta[f'{ext}_bytes'], meta[f'{ext}_sha256']), path
            raw[ext] = data
        else:
            assert ext == 'pgn' and meta['status'] != 'complete' and f'{ext}_sha256' not in meta, path
    log = raw['out'].decode()
    started, finished = console_games(log, count, match)
    assert len(ACTIVE.findall(log)) == 2 or (not started and meta['status'] != 'complete'), match
    if meta['status'] == 'complete':
        assert started == finished.keys() == set(range(1, count + 1)), match

    games = {}
    reviewed = set()
    for block in GAME.split(raw.get('pgn', b'').decode()):
        if not block.strip():
            continue
        round_number, game = read_game(block, positions, opening, finished)
        assert round_number not in reviewed and game.fen not in games, (match, round_number)
        reviewed.add(round_number)
        games[game.fen] = game
    assert reviewed == finished.keys(), (match, reviewed, finished.keys())
    rows = move_bytes(games)
    if args.repo is not None and 'pgn' in raw:
        compare_archive(rows, args.archive.parent / 'move-lists' / f'{match}.moves.txt', args)
    if args.moves_dir is not None:
        (args.moves_dir / f'{match}.moves.txt').write_bytes(rows)
    values = [node for game in games.values() for node in game.nodes]
    zeros = [(game.opening, i, game.moves[i - 1]) for game in sorted(games.values(), key=lambda game: game.opening)
             for i, node in enumerate(game.nodes, 1) if node == 0]
    return {
        'status': meta['status'], 'build': build, 'game_node_limit': nodes, 'lmr_quiet_base': lmr,
        'opening_start': opening, 'opening_end': opening + count - 1, 'started': len(started), 'games': len(games),
        'opening_lines': sorted(game.opening for game in games.values()),
        'plies': len(values), 'moves_sha256': sha256(rows).hexdigest(),
        'node_fields': len(values) - values.count(None), 'missing_node_fields': values.count(None),
        'zero_node_fields': len(zeros), 'first_zero_node_field': zeros[0] if zeros else None,
        'nodes_sum': sum(value for value in values if value is not None),
        'artifacts': {ext: {'bytes': len(data), 'sha256': sha256(data).hexdigest()} for ext, data in raw.items()},
    }, games


def find_difference(before, after, kind):
    a_plies = zip(before.moves, before.nodes, strict=True)
    b_plies = zip(after.moves, after.nodes, strict=True)
    for ply, (a, b) in enumerate(zip_longest(a_plies, b_plies), 1):
        a_move, a_nodes = a if a is not None else (None, None)
        b_move, b_nodes = b if b is not None else (None, None)
        differs = {
            'either': a != b,
            'move': a_move != b_move,
            'node': a_nodes != b_nodes or a is None or b is None,
        }
        if differs[kind]:
            return {
                'book_line': before.opening, 'fen': before.fen, 'ply': ply,
                'absolute_ply': chess.Board(before.fen).ply() + ply,
                'left_move': a_move, 'right_move': b_move, 'left_nodes': a_nodes, 'right_nodes': b_nodes,
            }
    raise ValueError(f'No first difference for selected opening {before.opening}')


def compare(left, right):
    examples = {}
    changed = []
    move_differences = node_differences = 0
    for fen in sorted(left.keys() & right.keys(), key=lambda fen: left[fen].opening):
        before, after = left[fen], right[fen]
        assert before.opening == after.opening
        move_unequal, node_unequal = before.moves != after.moves, before.nodes != after.nodes
        if not (move_unequal or node_unequal):
            continue
        changed.append(before.opening)
        move_differences += move_unequal
        node_differences += node_unequal
        if 'first_difference' not in examples:
            examples['first_difference'] = find_difference(before, after, 'either')
        if move_unequal and 'first_move_difference' not in examples:
            examples['first_move_difference'] = find_difference(before, after, 'move')
        if node_unequal and 'first_node_difference' not in examples:
            examples['first_node_difference'] = find_difference(before, after, 'node')
    return {
        'paired_games': len(left.keys() & right.keys()),
        'unpaired_left': sorted(left[fen].opening for fen in left.keys() - right.keys()),
        'unpaired_right': sorted(right[fen].opening for fen in right.keys() - left.keys()),
        'games_different': len(changed), 'move_differences': move_differences, 'node_differences': node_differences,
        'differing_opening_lines': changed,
        **{key: examples.get(key) for key in ('first_difference', 'first_move_difference', 'first_node_difference')},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    select = parser.add_mutually_exclusive_group()
    select.add_argument('--match', choices=PLAN)
    select.add_argument('--stage', choices=COMPARE)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--rev', default='HEAD')
    parser.add_argument('--archive', default=ARCHIVE, type=Path)
    parser.add_argument('--moves-dir', type=Path)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    assert chess.__version__ == '1.11.2', chess.__version__
    if args.moves_dir is not None:
        args.moves_dir.mkdir(parents=True, exist_ok=True)
    positions = opening_suite()
    runs, games = {}, {}
    selected = (args.match,) if args.match else COMPARE[args.stage] if args.stage else PLAN
    for match in selected:
        runs[match], games[match] = read_run(match, positions, args)
    comparisons = {stage: compare(games[left], games[right]) for stage, (left, right) in COMPARE.items()
                   if runs.get(left, {}).get('status') != 'not played' and runs.get(right, {}).get('status') != 'not played'
                   and left in runs and right in runs}
    receipt = json.dumps({'runs': runs, 'comparisons': comparisons}, indent=2, allow_nan=False) + '\n'
    if args.json is not None:
        args.json.write_text(receipt)
    print(receipt, end='')


if __name__ == '__main__':
    main()
