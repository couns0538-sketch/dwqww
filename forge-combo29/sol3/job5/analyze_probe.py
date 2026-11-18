#!/usr/bin/env python3
"""Read back Job 5 probe evidence without starting an engine."""

import argparse
import hashlib
import re
import sys
from pathlib import Path


TREES = ('10', '11', 'P')
JOB4_HASHES = {
    'B2': '16786cec209c333815749833026a62fcf492aa352030ee3e61d88d1e16a949c3',
    'N2': '291672dff227ae44449e0b83a0bdeee98879da27908f856f755d658ef6a27899',
}
ROW_COUNT = 389
CAP = 20_000
FINAL = re.compile(rb'info string final nodes ([0-9]+)')
REFUSAL = re.compile(rb'unknown option|invalid value|\bERROR\b', re.IGNORECASE)


def read_stdout(path):
    rows = []
    counts = []
    iteration = None
    final_count = None
    for line_number, line in enumerate(path.read_bytes().splitlines(), 1):
        location = f'{path}:{line_number}'
        if REFUSAL.search(line):
            raise ValueError(f'{location} engine refused command: {line!r}')
        if line.startswith(b'info depth '):
            if final_count is not None:
                raise ValueError(f'{location} depth-info appeared after the final count')
            iteration = line.split()
        elif line.startswith(b'info string final nodes'):
            match = FINAL.fullmatch(line)
            if match is None or iteration is None or final_count is not None:
                raise ValueError(f'{location} malformed, duplicate, or misplaced final count: {line!r}')
            final_count = int(match[1])
        elif line.startswith(b'bestmove '):
            if iteration is None or final_count is None:
                raise ValueError(f'{location} bestmove is missing its depth-info or final count')
            try:
                pv_index = iteration.index(b'pv')
                depth = iteration[2]
                nodes = iteration[iteration.index(b'nodes', 3, pv_index) + 1]
                pv_head = iteration[pv_index + 1] if pv_index + 1 < len(iteration) else b'-'
                bestmove = line.split()[1]
            except (IndexError, ValueError) as error:
                raise ValueError(f'{location} malformed depth-info or bestmove') from error
            if int(nodes) > final_count:
                raise ValueError(f'{location} last iteration count exceeds the final count')
            row_number = str(len(rows) + 1).encode('ascii')
            rows.append(b'\t'.join((row_number, depth, nodes, pv_head, bestmove)) + b'\n')
            counts.append(final_count)
            iteration = None
            final_count = None
    if iteration is not None or final_count is not None:
        raise ValueError(f'{path} ends with an unfinished search')
    if len(rows) != ROW_COUNT:
        raise ValueError(f'{path} expected {ROW_COUNT} searches, got {len(rows)}')
    return b''.join(rows), counts


def data_dir(root, tag):
    nested = root / tag
    return nested if nested.is_dir() else root


def read_matrix(logs, reference):
    matrix = {}
    for cell, old_hash in JOB4_HASHES.items():
        old_dir = data_dir(reference, f'11_{cell}')
        job4_rows = (old_dir / f'rows_11_{cell}.txt').read_bytes()
        if hashlib.sha256(job4_rows).hexdigest() != old_hash:
            raise ValueError(f'Job 4 {cell} reference row SHA-256 mismatch')
        for tree in TREES:
            tag = f'{tree}_{cell}'
            folder = data_dir(logs, tag)
            raw = folder / f'identity_{tag}.stdout.txt'
            reconstructed, counts = read_stdout(raw)
            rows = (folder / f'rows_{tag}.txt').read_bytes()
            digest = hashlib.sha256(rows).hexdigest()
            if reconstructed != rows:
                raise ValueError(f'{tag} rows file disagrees with independently parsed stdout')
            matrix[(tree, cell)] = (rows == job4_rows and digest == old_hash, digest, counts)
    return matrix


def print_table(matrix):
    failures = []
    print('| Probe | Cell | Job 4 rows byte-identical | Final counts at 20,000 | Final counts equal to k10f | First final count difference (k10f → probe) |')
    print('| --- | --- | --- | ---: | ---: | --- |')
    for tree in TREES:
        for cell in JOB4_HASHES:
            rows_equal, digest, counts = matrix[(tree, cell)]
            reference_counts = matrix[('10', cell)][2]
            differences = [(row, base, count) for row, (base, count) in
                           enumerate(zip(reference_counts, counts, strict=True), 1) if base != count]
            first = '—'
            if differences:
                row, base, count = differences[0]
                first = f'{row} ({base} → {count})'
            display_tree = f'k{tree}f' if tree != 'P' else 'Pf'
            same = len(counts) - len(differences)
            print(f'| {display_tree} | {cell} | {"yes" if rows_equal else "no"} | {counts.count(CAP)} | {same}/{ROW_COUNT} | {first} |')
            if not rows_equal:
                failures.append(f'{display_tree}/{cell} row SHA-256 {digest} differs from Job 4')
            if tree != 'P' and max(counts) > CAP:
                failures.append(f'{display_tree}/{cell} exceeded the cap, max was {max(counts)}')
            if tree == '11' and differences:
                failures.append(f'{display_tree}/{cell} final counts differ from k10f')
    print()
    for cell in JOB4_HASHES:
        baseline, planted = matrix[('11', cell)][2], matrix[('P', cell)][2]
        cap_hits = baseline.count(CAP)
        wrong = [(row, before, after) for row, (before, after)
                 in enumerate(zip(baseline, planted, strict=True), 1)
                 if after != before + int(before == CAP)]
        print(f'{cell} control: k11f hit {CAP} on {cap_hits} searches. Pf gave {CAP + 1} on {planted.count(CAP + 1)} searches.')
        print(f'{cell} row SHA-256: ' + ', '.join(f'{tree} {matrix[(tree, cell)][1]}' for tree in TREES))
        if cap_hits == 0:
            failures.append(f'{cell} did not exercise the planted fault')
        if wrong:
            row, before, after = wrong[0]
            failures.append(f'{cell} planted-control mismatch at {len(wrong)} rows. First row {row}, {before} → {after}')
    print('Step 4 gates: ' + ('FAILED' if failures else 'PASS'))
    for failure in failures:
        print(failure)
    return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', type=Path, help='probe logs, flat or grouped under 10_B2, 11_B2, etc.')
    parser.add_argument('job4', type=Path, help='Job 4 reference rows, flat or grouped under 11_B2 and 11_N2')
    args = parser.parse_args()
    try:
        return print_table(read_matrix(args.logs, args.job4))
    except (OSError, ValueError) as error:
        print(f'Probe evidence failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
