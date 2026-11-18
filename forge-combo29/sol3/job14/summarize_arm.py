import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re


COUNTERS = tuple(f'nc{i}' for i in range(5))
REQUIRED = {'index', 'fen', 'requested_depth', 'info_depth', 'bestmove', 'score_type', 'score', 'nodes', *COUNTERS}
MOVE = re.compile(r'0000|[a-h][1-8][a-h][1-8][qrbn]?')
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b|invalid FEN|no (?:v3 )?network (?:is )?loaded', re.I)


@dataclass(frozen=True)
class Position:
    index: int
    fen: str
    depth: int


@dataclass(frozen=True)
class Label:
    info_depth: int
    bestmove: str
    score_type: str
    score: int
    nodes: int


@dataclass(frozen=True)
class Row:
    position: Position
    label: Label
    counters: tuple[int, ...]
    last_info: str | None
    bestmove_line: str | None


def load(path):
    rows = []
    with path.open(encoding='ascii', newline='') as stream:
        table = csv.DictReader(stream, delimiter='\t')
        missing = REQUIRED - set(table.fieldnames or ())
        if missing:
            raise ValueError(f'{path}: missing columns {sorted(missing)}')
        for index, record in enumerate(table, 1):
            try:
                position = Position(int(record['index']), record['fen'], int(record['requested_depth']))
                label = Label(int(record['info_depth']), record['bestmove'], record['score_type'],
                              int(record['score']), int(record['nodes']))
                counters = tuple(int(record[key]) for key in COUNTERS)
            except (TypeError, ValueError) as error:
                raise ValueError(f'{path}: malformed row {index}') from error
            if (position.index != index or not position.fen or len(position.fen.split()) != 6 or position.depth < 1
                    or not 0 <= label.info_depth <= position.depth or label.nodes < 0
                    or label.score_type not in ('cp', 'mate') or not label.bestmove or not MOVE.fullmatch(label.bestmove)):
                raise ValueError(f'{path}: invalid row {index}: {position!r}, {label!r}')
            starts, shallow_starts, cutoffs, shallow_cutoffs, quiet_mates = counters
            if not 0 <= quiet_mates <= shallow_cutoffs <= min(shallow_starts, cutoffs) <= max(shallow_starts, cutoffs) <= starts:
                raise ValueError(f'{path}: row {index} has inconsistent NC0 counters {counters}')
            rows.append(Row(position, label, counters, record.get('last_info'), record.get('bestmove_line')))
    if not rows:
        raise ValueError(f'{path}: no searches')
    return rows


def verify_stdout(path, rows):
    info = None
    with path.open(encoding='ascii') as stream:
        raw = enumerate(stream, 1)
        row_number = 0
        for line_number, line in raw:
            line = line.rstrip('\r\n')
            if REFUSAL.search(line):
                raise ValueError(f'{path}:{line_number}: engine refused protocol: {line}')
            if line.startswith('info depth '):
                info = line
            elif line.startswith('bestmove '):
                if row_number == len(rows) or info is None:
                    raise ValueError(f'{path}:{line_number}: unexpected bestmove: {line}')
                row = rows[row_number]
                parts = info.split()
                try:
                    score_index = parts.index('score')
                    label = Label(int(parts[2]), line.split()[1], parts[score_index + 1],
                                  int(parts[score_index + 2]), int(parts[parts.index('nodes') + 1]))
                except (IndexError, ValueError) as error:
                    raise ValueError(f'{path}:{line_number}: malformed search info: {info}') from error
                _, next_line = next(raw, (None, ''))
                chunks = next_line.split()
                if chunks[:1] != ['NC0'] or len(chunks) != 6 or not all(s.isdecimal() for s in chunks[1:]):
                    raise ValueError(f'{path}:{line_number}: expected one NC0 line immediately after bestmove')
                if (label != row.label or tuple(map(int, chunks[1:])) != row.counters
                        or row.last_info not in (None, info) or row.bestmove_line not in (None, line)):
                    raise ValueError(f'{path}:{line_number}: raw search does not match TSV row {row_number + 1}')
                info = None
                row_number += 1
            elif line.startswith('NC0'):
                raise ValueError(f'{path}:{line_number}: stray NC0 counter line')
    if row_number != len(rows) or info is not None:
        raise ValueError(f'{path}: completed {row_number} raw searches, expected {len(rows)}')


def describe_difference(base, arm):
    def describe(row):
        return dict(bestmove=row.label.bestmove, nodes=row.label.nodes, info_depth=row.label.info_depth,
                    score_type=row.label.score_type, score=row.label.score, counters=row.counters)

    return dict(index=arm.position.index, fen=arm.position.fen, requested_depth=arm.position.depth,
                baseline_flagged=base.counters[4] > 0, baseline=describe(base), candidate=describe(arm))


def summarize(candidate, baseline, first):
    if len(candidate) != len(baseline):
        raise ValueError(f'row count differs: candidate {len(candidate)}, baseline {len(baseline)}')
    splits = {'baseline_flagged': {'positions': 0, 'changed': 0}, 'baseline_other': {'positions': 0, 'changed': 0}}
    first_move_changes = []
    first_label_difference = None
    first_counter_difference = None
    equal_labels = equal_counter_rows = 0
    for base, arm in zip(baseline, candidate):
        if base.position != arm.position:
            raise ValueError(f'position or depth disagrees: {base.position!r} versus {arm.position!r}')
        bucket = splits['baseline_flagged' if base.counters[4] > 0 else 'baseline_other']
        bucket['positions'] += 1
        if base.label.bestmove != arm.label.bestmove:
            bucket['changed'] += 1
            if len(first_move_changes) < first:
                first_move_changes.append(describe_difference(base, arm))
        if base.label == arm.label:
            equal_labels += 1
        elif first_label_difference is None:
            first_label_difference = describe_difference(base, arm)
        if base.counters == arm.counters:
            equal_counter_rows += 1
        elif first_counter_difference is None:
            first_counter_difference = describe_difference(base, arm)

    for bucket in splits.values():
        bucket['fraction'] = bucket['changed'] / bucket['positions'] if bucket['positions'] else None
    baseline_nodes = sum(row.label.nodes for row in baseline)
    nodes = sum(row.label.nodes for row in candidate)
    return dict(rows=len(candidate), nodes=nodes, baseline_nodes=baseline_nodes,
                node_ratio=nodes / baseline_nodes if baseline_nodes else None,
                first_three_nodes=[row.label.nodes for row in candidate[:3]],
                nc0_sums=[sum(column) for column in zip(*(row.counters for row in candidate))],
                nc4_positive_positions=sum(row.counters[4] > 0 for row in candidate),
                move_changes=splits, first_move_changes=first_move_changes,
                equal_search_labels=equal_labels, first_label_difference=first_label_difference,
                equal_counter_rows=equal_counter_rows, first_counter_difference=first_counter_difference)


def main():
    parser = argparse.ArgumentParser(description='Summarize Job 14 search labels and NC0 counters relative to baseline.')
    parser.add_argument('candidate', type=Path, help='candidate rows.tsv')
    parser.add_argument('baseline', type=Path, help='matching NullMoveBase 5 rows.tsv')
    parser.add_argument('--candidate-stdout', type=Path)
    parser.add_argument('--baseline-stdout', type=Path)
    parser.add_argument('--first', type=int, default=5, help='maximum number of first move changes to show')
    args = parser.parse_args()
    if args.first < 0:
        parser.error('--first must be nonnegative')
    try:
        candidate, baseline = load(args.candidate), load(args.baseline)
        if args.candidate_stdout:
            verify_stdout(args.candidate_stdout, candidate)
        if args.baseline_stdout:
            verify_stdout(args.baseline_stdout, baseline)
        print(json.dumps(summarize(candidate, baseline, args.first), indent=2))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == '__main__':
    main()
