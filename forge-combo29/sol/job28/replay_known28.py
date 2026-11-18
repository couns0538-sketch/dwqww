#!/usr/bin/env python3
"""Replay the three Job 28 HistoryAgeKeep known answers on fixed Job 3 games."""

import argparse
from hashlib import file_digest
from itertools import islice
import json
from pathlib import Path
import sys

SCRIPT_ROOT = Path(__file__).resolve().parent
for root in (SCRIPT_ROOT.parent / 'job3', SCRIPT_ROOT.parent / 'sol-job3'):
    if (root / 'run_games.py').is_file():
        sys.path.insert(0, str(root))
        break
from run_games import Engine, PC20, parse_row, read_games, utc_now

GAME_COUNT = 20
PLIES_PER_GAME = 60
CASES = (
    ('keep1024_soft', 1024, 'softnodes 2000', None),
    ('keep896_soft', 896, 'softnodes 2000', 4_080_162),
    ('keep896_hard', 896, 'nodes 20000', 16_285_974),
)


def sha256(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def ordered_rows(path, count=None):
    with path.open(encoding='utf-8') as data:
        return [json.loads(line) for line in islice(data, count)]


def key(row):
    return row['index'], row['game'], row['ply']


def prepare(games_path, default_reference, kimi_directory):
    games = read_games(games_path)[:GAME_COUNT]
    if len(games) != GAME_COUNT or any(len(game.moves) != PLIES_PER_GAME for game in games):
        raise ValueError('expected the first 20 Job 3 games to have 60 plies each')
    keys = [(index, game.index, ply) for index, (game, ply) in enumerate(
        ((game, ply) for game in games for ply in range(len(game.moves))), 1
    )]
    references = {}
    for label, _, _, expected_nodes in CASES:
        path = default_reference if expected_nodes is None else kimi_directory / f'{label}.jsonl'
        rows = ordered_rows(path, len(keys) if expected_nodes is None else None)
        if [key(row) for row in rows] != keys:
            raise ValueError(f'{label}: reference row keys differ from the exact Job 3 prefix')
        nodes = sum(row['nodes'] for row in rows)
        if expected_nodes is not None and nodes != expected_nodes:
            raise ValueError(f'{label}: reference {nodes} nodes differs from pinned {expected_nodes}')
        if label == 'keep1024_soft':
            openings = {game.index: game.fen for game in games}
            if any(row['fen'] != openings[row['game']] for row in rows):
                raise ValueError('the Job 3 default reference has a different starting position')
        references[label] = (path, rows, nodes)
    return games, references


def run_case(executable, games_path, games, options, case, reference, output, timeout):
    label, keep, budget, _ = case
    reference_path, expected, expected_nodes = reference
    search = f'go {budget}'
    commands = [f'setoption name {name} value {value}' for name, value in (
        ('Threads', '1'), ('Hash', '16'), *options, ('HistoryAgeKeep', str(keep)),
    )]
    rows_path = output / f'{label}.jsonl'
    meta_path = output / f'{label}.meta'
    meta = {
        'start_utc': utc_now(),
        'command': sys.argv,
        'exe': str(executable),
        'exe_sha256': sha256(executable),
        'games': str(games_path),
        'games_sha256': sha256(games_path),
        'game_numbers': [game.index for game in games],
        'search': search,
        'reset_per_game': ['ucinewgame', 'isready'],
        'settings_sent': commands,
        'reference': str(reference_path),
        'reference_sha256': sha256(reference_path),
        'reference_rows': len(expected),
        'reference_nodes_sum': expected_nodes,
        'external_net_file': None,
        'status': 'incomplete',
        'rows': 0,
        'node_matches': 0,
        'move_matches': 0,
        'both_match': 0,
        'last_info_nodes_sum': 0,
    }
    if rows_path.exists() or meta_path.exists():
        raise FileExistsError(f'refusing to overwrite outputs for {label}')
    with rows_path.open('x', encoding='utf-8') as rows:
        try:
            with Engine(executable, timeout) as engine:
                engine.send('uci')
                uci = engine.until('uciok')
                meta['id_name'] = next(line for line in uci if line.startswith('id name '))
                meta['option_advertised'] = next(line for line in uci
                    if line.startswith('option name HistoryAgeKeep '))
                for command in commands:
                    engine.send(command)
                engine.send('isready')
                engine.until('readyok')
                for game in games:
                    engine.send('ucinewgame')
                    engine.send('isready')
                    engine.until('readyok')
                    for ply in range(len(game.moves)):
                        position = f'position fen {game.fen}'
                        if ply:
                            position += ' moves ' + ' '.join(game.moves[:ply])
                        engine.send(position)
                        engine.send(search)
                        engine_output = engine.until('bestmove')
                        index = meta['rows'] + 1
                        row = parse_row(index, game.fen, engine_output, require_counter=True)
                        target = expected[index - 1]
                        nodes_match = row['nodes'] == target['nodes']
                        moves_match = row['bestmove'] == target['bestmove']
                        rows.write(json.dumps({
                            'index': index,
                            'game': game.index,
                            'ply': ply,
                            'position': position,
                            'info': row['info'],
                            'nodes': row['nodes'],
                            'bestmove_line': engine_output[-1],
                            'bestmove': row['bestmove'],
                            'expected_nodes': target['nodes'],
                            'expected_bestmove': target['bestmove'],
                        }, separators=(',', ':')) + '\n')
                        meta['rows'] = index
                        meta['node_matches'] += nodes_match
                        meta['move_matches'] += moves_match
                        meta['both_match'] += nodes_match and moves_match
                        meta['last_info_nodes_sum'] += row['nodes']
            meta['status'] = 'pass' if meta['both_match'] == len(expected) else 'mismatch'
        except Exception as error:
            meta['error'] = f'{type(error).__name__}: {error}'
            raise
        finally:
            rows.flush()
            meta['output_sha256'] = sha256(rows_path)
            meta['end_utc'] = utc_now()
            with meta_path.open('x', encoding='utf-8') as receipt:
                json.dump(meta, receipt, indent=2)
                receipt.write('\n')
    print(f'{label} {meta["status"].upper()}: {meta["both_match"]}/{len(expected)} exact pairs of fields, '
          f'{meta["node_matches"]} nodes matches, {meta["move_matches"]} best moves match, '
          f'{meta["last_info_nodes_sum"]} last-info nodes; '
          f'rows SHA-256 {meta["output_sha256"]}; UTC {meta["start_utc"]} to {meta["end_utc"]}.', flush=True)
    return meta['status'] == 'pass'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('games', type=Path)
    parser.add_argument('default_reference', type=Path)
    parser.add_argument('kimi_reference_directory', type=Path)
    parser.add_argument('--engine', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args()
    if args.timeout <= 0 or bool(args.engine) != bool(args.output_dir):
        parser.error('specify a positive timeout and provide both --engine and --output-dir for a replay')
    games_path = args.games.resolve(strict=True)
    games, references = prepare(games_path, args.default_reference.resolve(strict=True),
                                args.kimi_reference_directory.resolve(strict=True))
    print(f'Selected games 1–20 and plies 0–59 from Job 3. Source SHA-256 {sha256(games_path)}.', flush=True)
    for label, (path, rows, nodes) in references.items():
        print(f'{label} reference: {len(rows)} rows, {nodes} last-info nodes, SHA-256 {sha256(path)}.', flush=True)
    if args.engine:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        executable = args.engine.resolve(strict=True)
        for case in CASES:
            if not run_case(executable, games_path, games, PC20, case, references[case[0]],
                            args.output_dir, args.timeout):
                return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
