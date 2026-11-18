import argparse
import csv
from itertools import zip_longest
import json
from pathlib import Path


KEY = ('index', 'fen', 'requested_depth')
COUNTERS = tuple(f'nc{i}' for i in range(5))
REQUIRED = {*KEY, 'nodes', 'bestmove', *COUNTERS}


def records(path):
    with path.open(encoding='ascii', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        names = reader.fieldnames or []
        if len(names) != len(set(names)) or REQUIRED - set(names):
            raise ValueError(f'{path}: duplicate headers or missing required columns: {names!r}')
        for index, row in enumerate(reader, 1):
            try:
                if None in row or None in row.values():
                    raise ValueError('row does not match TSV header')
                key = int(row['index']), row['fen'], int(row['requested_depth'])
                nodes = int(row['nodes'])
                nc = tuple(int(row[name]) for name in COUNTERS)
                if (key[0] != index or len(key[1].split()) != 6 or key[2] < 1 or nodes < 0
                        or not row['bestmove'] or min(nc) < 0):
                    raise ValueError('invalid index, FEN, depth, node count, best move or NC0')
            except ValueError as error:
                raise ValueError(f'{path}: row {index}: {error}') from error
            yield key, nodes, nc, row


def audit(baseline, guarded):
    total = flagged = unflagged_unchanged = 0
    k4_violations = []
    k5_violations = []
    for number, (a, b) in enumerate(zip_longest(records(baseline), records(guarded)), 1):
        if a is None or b is None:
            raise ValueError(f'baseline and guarded have different row counts at row {number}')
        key, old_nodes, old_nc, old_row = a
        new_key, new_nodes, new_nc, new_row = b
        if key != new_key:
            raise ValueError(f'position/depth mismatch at row {number}: {key!r} versus {new_key!r}')
        total += 1
        baseline_flagged = old_nc[4] > 0
        flagged += baseline_flagged
        nodes_changed = old_nodes != new_nodes
        move_changed = old_row['bestmove'] != new_row['bestmove']
        fails_k4 = new_nc[4] > 0
        fails_k5 = not baseline_flagged and (nodes_changed or move_changed)
        if not baseline_flagged and not fails_k5:
            unflagged_unchanged += 1
        if not (fails_k4 or fails_k5):
            continue
        witness = dict(index=key[0], fen=key[1], requested_depth=key[2], baseline_nc0=old_nc,
                       guarded_nc0=new_nc, nodes_changed=nodes_changed, bestmove_changed=move_changed,
                       baseline_row=old_row, guarded_row=new_row)
        if fails_k4:
            k4_violations.append(witness)
        if fails_k5:
            k5_violations.append(witness)
    if not total:
        raise ValueError('no searches in either input')
    return dict(baseline=str(baseline), guarded=str(guarded), searches=total, baseline_flagged=flagged,
                baseline_unflagged=total-flagged, unflagged_unchanged=unflagged_unchanged,
                k4_passed=not k4_violations, guard_on_nc4_positive=len(k4_violations),
                guard_on_nc4_positive_rows=k4_violations, k5_passed=not k5_violations,
                unflagged_node_or_move_changes=len(k5_violations), unflagged_changed_rows=k5_violations)


def main():
    parser = argparse.ArgumentParser(description='Audit Job 15 K4/K5 against the two complete row files.')
    parser.add_argument('baseline', type=Path, help='NullMateGuard 0 rows.tsv')
    parser.add_argument('guarded', type=Path, help='NullMateGuard 1 rows.tsv')
    args = parser.parse_args()
    try:
        report = audit(args.baseline, args.guarded)
    except (OSError, ValueError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps(report, indent=2))
    return int(not (report['k4_passed'] and report['k5_passed']))


if __name__ == '__main__':
    raise SystemExit(main())
