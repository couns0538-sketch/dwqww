"""Verify the known answer and the deliberate direct-check-only stop."""

import argparse
import csv
import json
from pathlib import Path

import chess


def tsv(path):
    with path.open(newline='') as source:
        return list(csv.DictReader(source, delimiter='\t'))


def summary(path):
    return json.loads((path / 'summary.json').read_text())


def known_gate(path, reference):
    clean = summary(path)
    observed = tsv(path / 'rows.tsv')
    expected = tsv(reference)
    fields = ('fen', 'nodes', 'bestmove')
    mismatches = []
    for actual, prior in zip(observed, expected):
        if any(actual[key] != prior[key] for key in fields):
            mismatches.append({'row': actual['row'], 'expected': {key: prior[key] for key in fields},
                               'actual': {key: actual[key] for key in fields}})
    good = len(observed) == len(expected) == clean['searches'] == clean['bestmoves'] == 200
    good = (good and not mismatches and clean['reported_nodes'] == 4_097_080
            and clean['error'] is None and len(clean['processes']) == 1
            and clean['processes'][0]['exit'] == 0 and clean['processes'][0]['stderr_bytes'] == 0)
    return {'pass': good, 'observed_rows': len(observed), 'expected_rows': len(expected),
            'mismatches': mismatches, 'nodes': clean['reported_nodes'],
            'child_exits': [process['exit'] for process in clean['processes']]}


def control_gate(path, fixture):
    control = summary(path)
    hit = control['findings'][0] if control['findings'] else {}
    root = hit.get('search')
    entry = tsv(fixture)[root['row'] - 1] if root else {}
    planned = [index for index, row in enumerate(tsv(fixture), 1) if 'D' in row['classes']]
    internal_fen, move_uci = hit.get('assert_fen'), hit.get('assert_move')
    witnesses = []
    if internal_fen and move_uci:
        board = chess.Board(internal_fen)
        move = board.parse_uci(move_uci)
        if board.is_capture(move) or move.promotion or board.is_castling(move):
            raise ValueError(f'expected an ordinary quiet move, got {move_uci}')
        board.push(move)
        witnesses = [chess.square_name(square) for square in board.checkers()]
        if not witnesses or chess.square_name(move.to_square) in witnesses:
            raise ValueError(f'{move_uci} did not give a discovered-only check')
    good = (hit.get('assert') == 'A1' and hit.get('assert_detail') == 'fast 1 ref 0' and hit.get('exit') == -6
            and entry.get('fen') == root['fen'] and 'D' in entry['classes'] and witnesses
            and control['assert_stops'] == 1 and control['checker_reports'] == 0
            and control['runtime_failures'] == 0 and control['error'] is None
            and planned == control['scheduled_rows'])
    return {'pass': bool(good), 'attempted_searches': control['searches'],
            'bestmoves': control['bestmoves'], 'root': root, 'move': move_uci,
            'internal_fen': internal_fen, 'stationary_checkers': witnesses,
            'assert': hit.get('assert'), 'assert_detail': hit.get('assert_detail'),
            'child_exit': hit.get('exit'), 'first_30_lines': hit.get('first_30_lines', [])}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ('known', 'reference', 'control', 'fixture'):
        cli.add_argument(f'--{name}', type=Path, required=name != 'control')
    args = cli.parse_args()
    receipts = {'known': known_gate(args.known, args.reference)}
    if args.control is not None:
        receipts['control'] = control_gate(args.control, args.fixture)
    print(json.dumps(receipts, indent=2))
    return int(not all(result['pass'] for result in receipts.values()))


if __name__ == '__main__':
    raise SystemExit(main())
