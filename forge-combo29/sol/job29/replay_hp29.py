#!/usr/bin/env python3
"""Run the first Job 29 HC replay and enforce its declared gate."""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
for candidate in (ROOT / 'job28', ROOT / 'sol-job28'):
    if (candidate / 'replay_known28.py').is_file():
        sys.path.insert(0, str(candidate))
        break
from replay_known28 import Engine, PC20, key, ordered_rows, parse_row, read_games, sha256, utc_now

ROW_COUNT = 1200
HP_INFO = re.compile(r'info string HP27 (\d+) (\d+)')
SEARCH = 'go softnodes 2000'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    parser.add_argument('games', type=Path)
    parser.add_argument('job28_rows', type=Path)
    parser.add_argument('kimi_rows', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    games = read_games(args.games)[:20]
    job28 = ordered_rows(args.job28_rows)
    kimi = ordered_rows(args.kimi_rows)
    if len(games) != 20 or any(len(game.moves) != 60 for game in games) or len(job28) != ROW_COUNT or len(kimi) != ROW_COUNT:
        raise ValueError('expected 20 × 60 exact replay positions and references')
    outputs = args.output / 'keep1024_soft.jsonl'
    metadata = outputs.with_suffix('.meta')
    if outputs.exists() or metadata.exists():
        raise FileExistsError('refusing to overwrite replay output')
    args.output.mkdir(parents=True, exist_ok=True)
    settings = [f'setoption name {name} value {value}' for name, value in (
        ('Threads', '1'), ('Hash', '16'), *PC20, ('HistoryAgeKeep', '1024'),
    )]
    meta = {
        'command': sys.argv, 'start_utc': utc_now(), 'engine': str(args.engine.resolve(strict=True)),
        'engine_sha256': sha256(args.engine), 'games_sha256': sha256(args.games),
        'job28_rows_sha256': sha256(args.job28_rows), 'kimi_rows_sha256': sha256(args.kimi_rows),
        'settings_sent': settings, 'search': SEARCH, 'ucinewgame_per_game': True, 'external_net_file': None,
        'rows': 0, 'hp27_lines': 0, 'job28_matches': 0, 'kimi_matches': 0,
        'last_info_nodes': 0, 'hp27_nodes': 0, 'hp27_count': 0, 'matching_info_hp27_nodes': 0,
        'matching_final_hp27_nodes': 0, 'first_inequality': None, 'status': 'incomplete',
    }
    with outputs.open('x', encoding='utf-8') as rows:
        try:
            with Engine(args.engine.resolve(strict=True), 15) as engine:
                engine.send('uci')
                uci = engine.until('uciok')
                meta['id_name'] = next(line for line in uci if line.startswith('id name '))
                meta['uci_history_age_keep'] = next(line for line in uci if line.startswith('option name HistoryAgeKeep '))
                for option in settings:
                    engine.send(option)
                engine.send('isready')
                engine.until('readyok')
                for game in games:
                    engine.send('ucinewgame')
                    engine.send('isready')
                    engine.until('readyok')
                    for ply in range(60):
                        index = meta['rows'] + 1
                        reference = job28[index - 1]
                        kimi_row = kimi[index - 1]
                        if key(reference) != (index, game.index, ply) or key(kimi_row) != key(reference):
                            raise ValueError(f'reference rows out of order at {index}')
                        position = f'position fen {game.fen}'
                        if ply:
                            position += ' moves ' + ' '.join(game.moves[:ply])
                        if position != reference['position']:
                            raise ValueError(f'position differs from Job 28 at {index}')
                        engine.send(position)
                        engine.send(SEARCH)
                        lines = engine.until('bestmove')
                        row = parse_row(index, game.fen, lines, require_counter=True)
                        hp_lines = [line for line in lines if line.startswith('info string HP27 ')]
                        if len(hp_lines) != 1 or not (hp := HP_INFO.fullmatch(hp_lines[0])):
                            raise ValueError(f'row {index}: expected exactly one well-formed HP27 line, saw {hp_lines!r}')
                        count, hp_nodes = map(int, hp.groups())
                        nodes, move = row['nodes'], row['bestmove']
                        raw = {
                            'index': index, 'game': game.index, 'ply': ply, 'position': position,
                            'info': row['info'], 'nodes': nodes, 'bestmove_line': lines[-1], 'bestmove': move,
                            'hp27_line': hp_lines[0], 'hp27_count': count, 'hp27_nodes': hp_nodes,
                            'final_nodes_info': row['final_nodes_info'], 'final_nodes': row['final_nodes'],
                        }
                        rows.write(json.dumps(raw, separators=(',', ':')) + '\n')
                        meta['rows'] = index
                        meta['hp27_lines'] += 1
                        meta['job28_matches'] += (nodes, move) == (reference['nodes'], reference['bestmove'])
                        meta['kimi_matches'] += (nodes, move, count, hp_nodes) == (
                            kimi_row['nodes'], kimi_row['bestmove'], kimi_row['hp27'], kimi_row['hp27_nodes'],
                        )
                        meta['last_info_nodes'] += nodes
                        meta['hp27_nodes'] += hp_nodes
                        meta['hp27_count'] += count
                        meta['matching_final_hp27_nodes'] += row['final_nodes'] == hp_nodes
                        meta['matching_info_hp27_nodes'] += nodes == hp_nodes
                        if nodes != hp_nodes and meta['first_inequality'] is None:
                            meta['first_inequality'] = raw
            met_gate = (meta['rows'], meta['hp27_lines'], meta['job28_matches'], meta['last_info_nodes'],
                        meta['hp27_count'], meta['matching_info_hp27_nodes']) == (1200, 1200, 1200, 4294263, 11633, 1200)
            meta['status'] = 'pass' if met_gate else 'gate_failed'
        except Exception as error:
            meta['error'] = f'{type(error).__name__}: {error}'
            raise
        finally:
            rows.flush()
            meta['output_sha256'] = sha256(outputs)
            meta['end_utc'] = utc_now()
            with metadata.open('x', encoding='utf-8') as receipt:
                json.dump(meta, receipt, indent=2)
                receipt.write('\n')
    print(json.dumps(meta, indent=2))
    return 0 if met_gate else 2


if __name__ == '__main__':
    raise SystemExit(main())
