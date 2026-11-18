#!/usr/bin/env python3
"""Regrade Job 20 S2 by replaying the raw logs and validating the saved rows."""

import argparse
import hashlib
import json
from pathlib import Path
import re

import chess

import identity


K_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
ARTIFACTS = {'engine.commands.txt', 'engine.stdout.txt', 'engine.stderr.txt', 'plies.jsonl', 'games.jsonl'}
COUNT_KEYS = ('evals', 'differ', 'final_nodes', 'last_info_nodes')
ACTIVE = re.compile(r'info string NNUE v3 active: .+\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    with path.open('rb') as raw:
        return hashlib.file_digest(raw, 'sha256').hexdigest()


def read_lines(path):
    raw = path.read_bytes()
    require(not raw or raw.endswith(b'\n'), f'missing final LF in {path}')
    return raw.decode('ascii').splitlines()


def fixture_roots(path):
    require(file_hash(path) == K_SHA, 'incorrect fixture SHA-256')
    fens = read_lines(path)
    require(len(fens) == 1000, 'incorrect fixture row count')
    return fens[20:40]


def require_command(log, expected):
    actual = next(log, None)
    require(actual == expected, f'expected input {expected!r}, got {actual!r}')


def take_until(log, predicate, label):
    buffer = []
    for line in log:
        buffer.append(line)
        if predicate(line):
            return buffer
    raise ValueError(f'stdout ended before {label}')


def check_startup(commands, stdout, net):
    require_command(commands, 'uci')
    for option, value in identity.PC20.items():
        require_command(commands, f'setoption name {option} value {value}')
    require_command(commands, f'setoption name NNUEArchFile value {net}')
    require_command(commands, 'setoption name NNUEArch value true')
    require_command(commands, 'isready')
    startup = take_until(stdout, lambda line: line == 'readyok', 'initial readyok')
    active = [line for line in startup if line.startswith('info string NNUE v3 active: ')]
    require(startup.count('uciok') == 1 and len(active) == 1 and ACTIVE.search(active[0])
            and startup.index('uciok') < startup.index(active[0]), 'missing or misplaced startup/net activation receipt')
    require(sum(line.startswith('id name ') for line in startup) == 1, 'expected one engine name')
    return active[0]


def check_frame(lines, board, prior_details):
    bestmove = lines[-1].split()
    require(len(bestmove) in {2, 4} and bestmove[0] == 'bestmove', 'invalid bestmove syntax')
    if len(bestmove) == 4:
        require(bestmove[2] == 'ponder' and re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?', bestmove[3]),
                'invalid ponder syntax')
    move = chess.Move.from_uci(bestmove[1])
    require(move in board.legal_moves, f'illegal move {move.uci()} on {board.fen()}')

    markers = [line for line in lines if line.startswith('info string shadow evals')]
    require(len(markers) == 1 and markers[0] == lines[-2], 'expected only one shadow totals line directly before bestmove')
    mark = markers[0].split()
    require(len(mark) == 7 and mark[:4] == ['info', 'string', 'shadow', 'evals'] and mark[5] == 'differ'
            and mark[4].isdigit() and mark[6].isdigit(), 'invalid shadow totals fields')
    evals, differ = int(mark[4]), int(mark[6])
    require(differ <= evals, 'shadow differences exceed evaluations')
    diagnostics = []
    for line in lines:
        if not line.startswith('info string shadow') or line == markers[0]:
            continue
        fields = line.split(maxsplit=8)
        require(len(fields) == 9 and fields[:5] == ['info', 'string', 'shadow', 'differ', 'fast']
                and fields[6] == 'ref', 'unknown shadow emission')
        ref_and_fen = fields[8].split(maxsplit=1)
        require(len(ref_and_fen) == 2 and ref_and_fen[0] == 'fen', 'invalid shadow FEN field')
        fast, ref, fen = int(fields[5]), int(fields[7]), ref_and_fen[1]
        require(fast != ref and len(fen.split()) == 6, 'invalid shadow mismatch payload')
        diagnostics.append({'fast': fast, 'ref': ref, 'fen': fen, 'line': line})
    require(len(diagnostics) == min(differ, 5 - prior_details), 'incorrect first-five diagnostic count')

    finals = [line for line in lines if line.startswith('info string softnodes nodes')]
    require(len(finals) == 1 and re.fullmatch(r'info string softnodes nodes [0-9]+', finals[0]),
            'expected one exact total-consumed softnodes marker')
    consumed = int(finals[0].rsplit(' ', 1)[1])
    infos = [line for line in lines if line.startswith('info depth ')]
    require(bool(infos), 'no depth info in the search')
    fields = infos[-1].split()
    require(fields[1:4:2] == ['depth', 'seldepth'] and fields[5:9:3] == ['score', 'nodes'] and len(fields) >= 17
            and fields[10:17:2] == ['nps', 'hashfull', 'time', 'pv'] and fields[6] in {'cp', 'mate'},
            'invalid last depth-info fields')
    depth, seldepth, score, info_nodes = map(int, (fields[2], fields[4], fields[7], fields[9]))
    require(0 < info_nodes <= consumed <= 8000, 'depth-info and final consumed nodes inconsistent with cap')
    return move, {
        'bestmove': bestmove[1], 'ponder': bestmove[3] if len(bestmove) == 4 else None,
        'depth': depth, 'seldepth': seldepth, 'score_kind': fields[6], 'score': score,
        'pv': fields[17:], 'last_info_nodes': info_nodes, 'final_nodes': consumed,
        'evals': evals, 'differ': differ, 'details': diagnostics, 'shadow_line': markers[0],
        'final_line': finals[0], 'last_info': infos[-1], 'bestmove_line': lines[-1],
    }


def read_workload(path, fens):
    meta = json.loads((path / 'summary.json').read_text(encoding='ascii'))
    files = meta['files_sha256']
    require(files.keys() == ARTIFACTS and all(file_hash(path / name) == digest for name, digest in files.items()),
            f'changed/missing driver artifacts in {path}')
    require(meta['error'] is None and meta['workload'] == 'S2' and meta['fixture_sha256'] == K_SHA
            and meta['pc20'] == identity.PC20 and meta['net_sha256'] == identity.NET_SHA
            and meta['python_chess'] == chess.__version__ == '1.11.2'
            and meta['soft_nodes'] == 2000 and meta['hard_node_cap'] == 8000
            and meta['ply_cap'] == 200 and meta['claim_draw'] is True,
            f'mislabeled or incomplete run in {path}')
    identity.check_logs(path / 'engine.stdout.txt', path / 'engine.stderr.txt')
    commands = iter(read_lines(path / 'engine.commands.txt'))
    stdout = iter(read_lines(path / 'engine.stdout.txt'))
    active = check_startup(commands, stdout, meta['net_path'])
    saved_plies = iter(map(json.loads, read_lines(path / 'plies.jsonl')))
    saved_games = iter(map(json.loads, read_lines(path / 'games.jsonl')))
    games = []
    searched_plies = []
    detail_count = 0
    for w1_position, start_fen in enumerate(fens, 21):
        require_command(commands, 'ucinewgame')
        require_command(commands, 'isready')
        require(next(stdout, None) == 'readyok', f'missing or noisy newgame reply at W1 row {w1_position}')
        board = chess.Board(start_fen)
        path_rows = []
        moves = []
        first_detail = None
        while len(moves) < 200 and board.outcome(claim_draw=True) is None:
            command = 'position fen ' + start_fen + ' moves'
            if moves:
                command += ' ' + ' '.join(moves)
            require_command(commands, command)
            require_command(commands, 'go softnodes 2000')
            frame = take_until(stdout, lambda line: line.startswith('bestmove '), 'bestmove')
            require(not any(line in {'readyok', 'uciok'} or line.startswith('info string NNUE v3 active: ')
                            for line in frame), 'extraneous protocol output inside a search')
            move, data = check_frame(frame, board, detail_count)
            detail_count += len(data['details'])
            ply = len(moves) + 1
            row = {'w1_position': w1_position, 'ply': ply, 'root_fen': board.fen(), **data}
            require(row == next(saved_plies, None), f'ply row differs from raw in {path}, W1 row {w1_position}, ply {ply}')
            if data['details'] and first_detail is None:
                first_detail = {'w1_position': w1_position, 'ply': ply, 'root_fen': board.fen(),
                                'last_played_root_move': moves[-1] if moves else None, **data['details'][0]}
            path_rows.append(row)
            moves.append(move.uci())
            board.push(move)
        outcome = board.outcome(claim_draw=True)
        game = {'w1_position': w1_position, 'start_fen': start_fen, 'plies': len(moves), 'moves': moves,
                **{key: sum(row[key] for row in path_rows) for key in COUNT_KEYS},
                'stop': outcome.termination.name if outcome else 'PLY_CAP', 'result': outcome.result() if outcome else '*',
                'ply_cap_reached': len(moves) == 200, 'final_fen': board.fen(), 'first_detail': first_detail}
        require(game == next(saved_games, None), f'game row differs from raw in {path}, W1 row {w1_position}')
        games.append(game)
        searched_plies.append(path_rows)
    require_command(commands, 'quit')
    require(all(next(log, None) is None for log in (commands, stdout, saved_plies, saved_games)), 'unexpected extra raw or derived rows')
    totals = {key: sum(game[key] for game in games) for key in COUNT_KEYS}
    first_detail = next((game['first_detail'] for game in games if game['first_detail'] is not None), None)
    eval_rate = totals['evals'] / totals['final_nodes'] if totals['final_nodes'] else None
    require(meta['totals'] == totals and meta['searches'] == sum(game['plies'] for game in games)
            and meta['games'] == len(games) and meta['evals_per_consumed_node'] == eval_rate
            and meta['first_detail'] == first_detail, 'summary differs from the raw replay')
    verified = {'build': meta['build'], 'exe_sha256': meta['exe_sha256'], 'net_active': active,
                'games': meta['games'], 'searches': meta['searches'], 'totals': totals,
                'evals_per_consumed_node': eval_rate, 'first_detail': first_detail}
    return verified, games, searched_plies


def compare(left_path, right_path, fens):
    left, left_games, left_plies = read_workload(left_path, fens)
    right, right_games, right_plies = read_workload(right_path, fens)
    require({left['build'], right['build']} == {'r15d-shadow', 'kF-shadow'}, 'compare exactly r15d-shadow and kF-shadow')
    comparisons = []
    for a, b, rows_a, rows_b in zip(left_games, right_games, left_plies, right_plies, strict=True):
        index = 0
        while index < min(a['plies'], b['plies']) and a['moves'][index] == b['moves'][index]:
            index += 1
        equal = index == a['plies'] == b['plies']
        first_diff = None
        if not equal:
            first_diff = {'ply': index + 1, 'position': ' '.join(('position fen', a['start_fen'], 'moves', *a['moves'][:index])),
                          'left': rows_a[index] if index < len(rows_a) else {'game_ended': a['stop']},
                          'right': rows_b[index] if index < len(rows_b) else {'game_ended': b['stop']}}
        comparisons.append({'w1_position': a['w1_position'], 'left_plies': a['plies'], 'right_plies': b['plies'],
                            'equal': equal, 'first_difference': first_diff})
    count_equal = sum(game['equal'] for game in comparisons)
    return {'left': left, 'right': right, 'games_compared': len(comparisons), 'equal_move_lists': count_equal,
            'differing_move_lists': len(comparisons) - count_equal, 'game_comparisons': comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest='operation', required=True)
    verify = operations.add_parser('verify')
    verify.add_argument('--fixture', type=Path, required=True)
    verify.add_argument('run', type=Path)
    compare_cli = operations.add_parser('compare')
    compare_cli.add_argument('--fixture', type=Path, required=True)
    compare_cli.add_argument('left', type=Path)
    compare_cli.add_argument('right', type=Path)
    args = parser.parse_args()
    try:
        fens = fixture_roots(args.fixture)
        result = (read_workload(args.run, fens)[0] if args.operation == 'verify'
                  else compare(args.left, args.right, fens))
    except (KeyError, OSError, ValueError) as err:
        parser.exit(1, f'{err}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
