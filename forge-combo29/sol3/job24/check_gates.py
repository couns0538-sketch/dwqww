"""Check Job 24 known-answer and independence gates from retained UCI data."""

import argparse
import csv
import json
from pathlib import Path

import chess


def table(path):
    with path.open(newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def metadata(run):
    return json.loads((run / 'summary.json').read_text())


def compare(run, prior, count, node_sum):
    summary = metadata(run)
    observed = table(run / 'rows.tsv')
    reference = table(prior)
    fields = ('fen', 'nodes', 'bestmove')
    differences = [{ 'row': got['row'], 'expected': {name: old[name] for name in fields},
                    'observed': {name: got[name] for name in fields}}
                   for got, old in zip(observed, reference) if any(got[name] != old[name] for name in fields)]
    exits = [process['exit'] for process in summary['processes']]
    stderr = sum(process['stderr_bytes'] for process in summary['processes'])
    correct = (len(observed) == len(reference) == count == summary['searches'] == summary['bestmoves']
               and summary['completed_searches'] == count and summary['reported_nodes'] == node_sum
               and not differences and summary['error'] is None and exits == [0] and not stderr
               and not summary['assert_stops'] and not summary['checker_reports'])
    return {'pass': correct, 'observed': len(observed), 'reference': len(reference),
            'searches': summary['searches'], 'bestmoves': summary['bestmoves'],
            'nodes': summary['reported_nodes'], 'exits': exits, 'stderr_bytes': stderr,
            'differences': differences}


def direct_only(run, fixture):
    summary = metadata(run)
    assert len(summary['processes']) == 1
    process = summary['processes'][0]
    assert len(summary['findings']) <= 1
    finding = summary['findings'][0] if summary['findings'] else {}
    search = finding.get('search') or {}
    witness = []
    local_fen, uci = process['assert_fen'], process['assert_move']
    if local_fen and uci:
        board = chess.Board(local_fen)
        move = board.parse_uci(uci)
        assert not board.is_capture(move) and not move.promotion and not board.is_castling(move), uci
        board.push(move)
        witness = [chess.square_name(square) for square in board.checkers()
                   if square != move.to_square]
        assert move.to_square not in board.checkers(), uci
    row = table(fixture)[0]
    correct = (search.get('row') == 1 and search.get('fen') == row['fen'] and row['classes'] == 'DQ'
               and process['assert'] == 'A1s' and process['exit'] == -6 and witness
               and summary['searches'] == summary['assert_stops'] == 1
               and summary['bestmoves'] == summary['checker_reports'] == summary['runtime_failures'] == 0
               and summary['error'] is None)
    return {'pass': bool(correct), 'root': search.get('fen'), 'move': uci, 'local_fen': local_fen,
            'stationary_checkers': witness, 'exit': process['exit'], 'assert': process['assert'],
            'first_30_lines': finding.get('first_30_lines', [])}


def independence(run, plan):
    summary = metadata(run)
    rows = table(run / 'blind.tsv')
    expected = table(plan)
    if not rows:
        return {'pass': False, 'first': None, 'rows': 0}
    root = rows[0]
    first_process = summary['processes'][0]
    first_finding = next((finding for finding in summary['findings'] if finding['process'] == root['process']), {})
    planned = all((got['row'], got['fen']) == (want['row'], want['fen']) for got, want in zip(rows, expected))
    correct = (planned and len(rows) == len(expected) == len(summary['processes']) == 20
               and root['status'] == 'assert_stop' and first_process['assert'] in ('A2s', 'A4')
               and first_process['exit'] == -6 and bool(first_finding.get('first_30_lines'))
               and summary['error'] is None)
    return {'pass': correct, 'first': root, 'first_30_lines': first_finding.get('first_30_lines', []),
            'rows': len(rows), 'engine_exit_codes': [p['exit'] for p in summary['processes']],
            'assert_stops': summary['assert_stops'], 'checker_reports': summary['checker_reports']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sol3', required=True, type=Path)
    parser.add_argument('--gate', choices=('k1', 'k2', 'wrong2', 'new-blind'), required=True)
    args = parser.parse_args()
    root = args.sol3
    job = root / 'job24'
    if args.gate == 'k1':
        result = compare(job / 'step2/known', root / 'job22/clean/AU-kF-d9/rows.tsv', 200, 4_097_080)
    elif args.gate == 'k2':
        result = compare(job / 'step3/r1', root / 'job23/step3/r1/rows.tsv', 2000, 35_709_215)
    elif args.gate == 'wrong2':
        result = direct_only(job / 'step2/wrong2', root / 'job23/step1/positions.tsv')
    else:
        result = independence(job / 'step2/new-blind', job / 'plan/blind.tsv')
    print(json.dumps(result, indent=2))
    return int(not result['pass'])


if __name__ == '__main__':
    raise SystemExit(main())
