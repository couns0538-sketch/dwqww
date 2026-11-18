import argparse
from collections import Counter
import csv
import json
import re
from pathlib import Path

import chess


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='ascii').splitlines()]


def main():
    parser = argparse.ArgumentParser(description='Summarize independently checked S2 game paths.')
    parser.add_argument('directory', type=Path)
    parser.add_argument('table', type=Path)
    args = parser.parse_args()
    builds = ('r15d-shadow', 'kF-shadow')
    records = [json_lines(args.directory / build / 'games.jsonl') for build in builds]
    plies = [json_lines(args.directory / build / 'plies.jsonl') for build in builds]
    for left, right in zip(*plies, strict=True):
        for row in (left, right):
            row['last_info'] = re.sub(r' (?:time|nps) \d+\b', '', row['last_info'])
        assert left == right, (left['w1_position'], left['ply'])
    comparison = json.loads((args.directory / 'comparison.json').read_text())
    assert comparison['games_compared'] == comparison['equal_move_lists'] == 20
    assert comparison['differing_move_lists'] == 0
    moves = Counter()
    records_a = records[0]
    for row in records_a:
        board = chess.Board(row['start_fen'])
        for text in row['moves']:
            move = chess.Move.from_uci(text)
            assert move in board.legal_moves
            moves['promotion'] += (move.promotion is not None)
            moves['en_passant'] += board.is_en_passant(move)
            moves['castling'] += board.is_castling(move)
            board.push(move)

    with args.table.open('x', encoding='ascii', newline='') as file:
        table = csv.writer(file, delimiter='\t', lineterminator='\n')
        metrics = ('plies', 'evals', 'differ', 'final_nodes')
        table.writerow(['w1_position', 'result', 'stop', *(f'{build}:{name}' for build in builds for name in metrics), 'moves_equal'])
        for left, right, compared in zip(*records, comparison['game_comparisons'], strict=True):
            assert left['w1_position'] == right['w1_position'] == compared['w1_position']
            assert left['result'] == right['result'] and left['stop'] == right['stop']
            table.writerow([left['w1_position'], left['result'], left['stop'],
                            *(row[name] for row in (left, right) for name in metrics), str(compared['equal']).lower()])

    search = plies[0]
    aggregate = {name: sum(row[name] for row in search) for name in ('evals', 'differ', 'final_nodes', 'last_info_nodes')}
    aggregate.update(games=len(records_a), searches=len(search), stop_counts=Counter(row['stop'] for row in records_a),
                     result_counts=Counter(row['result'] for row in records_a), played_move_classes=moves,
                     min_plies=min(row['plies'] for row in records_a), max_plies=max(row['plies'] for row in records_a),
                     searches_at_hard_cap=sum(row['final_nodes'] == 8000 for row in search),
                     searches_with_partial_iteration=sum(row['final_nodes'] > row['last_info_nodes'] for row in search),
                     stable_rows_equal=len(search), evals_per_consumed_node=aggregate['evals'] / aggregate['final_nodes'])
    print(json.dumps(aggregate, indent=2))


if __name__ == '__main__':
    main()
