#!/usr/bin/env python3
"""Independently compare one Job 10 cold-search cell with its Job 7 k11f evidence."""

import argparse
from pathlib import Path
import sys

from compare_limits import CELLS, find_folder, read_arm, read_positions


def setup_lines(folder, tag, cell):
    path = folder / f'identity_{tag}.commands.txt'
    commands = path.read_text(encoding='ascii').splitlines()
    setup = commands[:commands.index('ucinewgame')]
    net_prefix = 'setoption name NNUEArchFile value '
    expected_net_settings = int(cell == 'N2')
    if sum(line.startswith(net_prefix) for line in setup) != expected_net_settings:
        raise ValueError(f'{path} has incorrect NNUEArchFile command count')
    return [net_prefix + '<pinned net768>' if line.startswith(net_prefix) else line for line in setup]


def report(positions, baseline, candidate, limit, cell):
    changed = []
    over_cap = []
    changed_moves_or_scores = 0
    for index, (old, new) in enumerate(zip(baseline, candidate, strict=True), 1):
        if old.row(index) != new.row(index):
            changed.append(index)
        if old.final_nodes > limit or new.final_nodes > limit:
            over_cap.append(index)
        changed_moves_or_scores += old.move_and_score() != new.move_and_score()

    old_at_cap = sum(row.final_nodes == limit for row in baseline)
    new_at_cap = sum(row.final_nodes == limit for row in candidate)
    print(f'{cell} nodes={limit} rows={len(positions)} equal={len(positions) - len(changed)} '
          f'k11f_at_cap={old_at_cap} k13f_at_cap={new_at_cap} '
          f'move_or_score_changes={changed_moves_or_scores} over_cap_pairs={len(over_cap)}')
    affected = sorted({*changed[:1], *over_cap[:1]})
    for index in affected:
        reason = ', '.join(label for label, group in [('row difference', changed), ('above cap', over_cap)]
                           if group and index == group[0])
        print(f'First {reason} at fixture row {index} {positions[index - 1]}')
        for label, result in [('k11f', baseline[index - 1]), ('k13f', candidate[index - 1])]:
            print(f'{label} row       {result.row(index)}')
            print(f'{label} last info {result.last_info}')
    return int(bool(affected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('baseline_root', type=Path)
    parser.add_argument('candidate_root', type=Path)
    parser.add_argument('limit', type=int, choices=(50000, 250000))
    parser.add_argument('cell', choices=CELLS)
    args = parser.parse_args()
    try:
        positions = read_positions(args.fixture)
        baseline = read_arm(args.baseline_root, args.limit, '11', args.cell, positions)
        candidate = read_arm(args.candidate_root, args.limit, '11', args.cell, positions)
        tag = f'11_{args.cell}'
        baseline_folder = find_folder(args.baseline_root, args.limit, tag)
        candidate_folder = find_folder(args.candidate_root, args.limit, tag)
        if setup_lines(baseline_folder, tag, args.cell) != setup_lines(candidate_folder, tag, args.cell):
            raise ValueError('The two command transcripts differ on UCI setup')
        print(f'k11f raw {baseline_folder / f"identity_{tag}.stdout.txt"}')
        print(f'k13f raw {candidate_folder / f"identity_{tag}.stdout.txt"}')
        return report(positions, baseline, candidate, args.limit, args.cell)
    except (OSError, ValueError) as error:
        print(f'Readback failed for {args.limit} {args.cell}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
