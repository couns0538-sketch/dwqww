import argparse
import csv
import json
from itertools import zip_longest
from pathlib import Path

def load(path):
    with path.open(encoding='ascii', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))

def compare(left, right, fields):
    first = None
    mismatches = 0
    for index, (a, b) in enumerate(zip_longest(left, right), 1):
        if a is None or b is None or any(a[key] != b[key] for key in fields):
            mismatches += 1
            if first is None:
                first = dict(row=index, reference=a, candidate=b)
    return dict(rows_reference=len(left), rows_candidate=len(right), mismatches=mismatches, first=first)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('ladder', 'A1', 'identity', 'Gref', 'sum'))
    parser.add_argument('candidate', type=Path)
    parser.add_argument('reference', type=Path, nargs='?')
    args = parser.parse_args()
    rows = load(args.candidate)
    if args.mode == 'ladder':
        mate = next((int(row['requested_depth']) for row in rows if row['bestmove'] == 'g3g6'
                     and row['score_type'] == 'mate' and int(row['score']) > 0), None)
        result = dict(rows=len(rows), first_winning_mate_depth=mate, first_g3g6_depth=next(
            (int(row['requested_depth']) for row in rows if row['bestmove'] == 'g3g6'), None))
        print(json.dumps(result, indent=2))
        return 0
    if args.mode == 'sum':
        sums = [sum(int(row[f'nc{i}']) for row in rows) for i in range(5)]
        nodes = sum(int(row['nodes']) for row in rows)
        print(json.dumps(dict(lines=len(rows), nodes=nodes, sums=sums,
                              per_1000_nodes=[1000 * number / nodes for number in sums]), indent=2))
        return int(len(rows) != 353)
    if args.mode == 'A1':
        fields = ('requested_depth', 'info_depth', 'bestmove', 'score_type', 'score', 'nodes')
    elif args.mode == 'Gref':
        fields = ('index', 'fen', 'nodes', 'bestmove')
    else:
        fields = ('index', 'fen', 'requested_depth', 'nodes', 'bestmove')
    reference = load(args.reference)
    result = compare(reference, rows, fields)
    if args.mode == 'Gref':
        result['reference_nodes'] = sum(int(row['nodes']) for row in reference)
        result['candidate_nodes'] = sum(int(row['nodes']) for row in rows)
        result['first_three_nodes'] = [int(row['nodes']) for row in rows[:3]]
    print(json.dumps(result, indent=2))
    return int(result['mismatches'] != 0)

if __name__ == '__main__':
    raise SystemExit(main())
