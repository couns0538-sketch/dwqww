#!/usr/bin/env python3
"""Independently verify one Job 7 node-limit matrix from its UCI transcripts."""

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import sys


TREES = ('10', '11', 'P')
CELLS = ('B2', 'N2')
POSITIONS_SHA = 'd0630396e9e937318bf83e542d2f168c6216831e0dd83283875172d6ff72a2b2'
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b|invalid FEN', re.IGNORECASE)
FINAL = re.compile(r'info string final nodes ([0-9]+)')
SCORE = re.compile(r'\bscore (cp|mate) (-?[0-9]+)\b')
INFO_NODES = re.compile(r'\bnodes ([0-9]+)\b')
MOVE = r'[a-h][1-8][a-h][1-8][qrbn]?'
BESTMOVE = re.compile(rf'bestmove (0000|{MOVE})(?: ponder {MOVE})?')
NET_ACTIVE = 'info string NNUE v3 active:'
NET_MARKER = re.compile(r'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b')


@dataclass(frozen=True)
class Search:
    final_nodes: int
    bestmove: str
    score_kind: str
    score_value: int
    last_info: str

    def row(self, index):
        return f'{index}\t{self.final_nodes}\t{self.bestmove}\t{self.score_kind}\t{self.score_value}'

    def move_and_score(self):
        return self.bestmove, self.score_kind, self.score_value


def read_positions(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != POSITIONS_SHA:
        raise ValueError(f'{path} does not have the Job 4 position fixture SHA-256')
    positions = [' '.join(line.split()) for line in raw.decode('ascii').splitlines()]
    if len(positions) != 389:
        raise ValueError(f'{path} expected 389 positions, found {len(positions)}')
    return positions


def read_stdout(path, cell, expected_searches):
    searches = []
    last_info = None
    final = None
    net_markers = 0
    ready_lines = 0
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        location = f'{path}:{line_number}'
        if REFUSAL.search(line):
            raise ValueError(f'{location} engine refusal: {line}')
        if line == 'readyok':
            if last_info is not None or final is not None:
                raise ValueError(f'{location} began a new search before the old bestmove')
            ready_lines += 1
        elif line.startswith(NET_ACTIVE):
            if not NET_MARKER.search(line):
                raise ValueError(f'{location} unexpected active network: {line}')
            net_markers += 1
        elif line.startswith('info depth '):
            if final is not None:
                raise ValueError(f'{location} iteration info appeared after the final count')
            last_info = line
        elif line.startswith('info string final nodes'):
            match = FINAL.fullmatch(line)
            if match is None or last_info is None or final is not None:
                raise ValueError(f'{location} malformed, duplicate, or misplaced final count')
            final = int(match[1])
        elif line.startswith('bestmove '):
            move = BESTMOVE.fullmatch(line)
            score = SCORE.search(last_info or '')
            info_nodes = INFO_NODES.search(last_info or '')
            if move is None or score is None or info_nodes is None or final is None:
                raise ValueError(f'{location} malformed bestmove or missing score or final count')
            if ready_lines != len(searches) + 2:
                raise ValueError(f'{location} expected one readyok for each search and one for setup')
            if int(info_nodes[1]) > final:
                raise ValueError(f'{location} last info nodes exceed the final count')
            searches.append(Search(final, move[1], score[1], int(score[2]), last_info))
            last_info = None
            final = None
    if last_info is not None or final is not None or len(searches) != expected_searches:
        raise ValueError(f'{path} expected {expected_searches} complete searches, found {len(searches)}')
    if ready_lines != expected_searches + 1 or net_markers != int(cell == 'N2'):
        raise ValueError(f'{path} setup/search readiness or active-net marker count differs')
    return searches


def find_folder(root, limit, tag):
    filename = f'identity_{tag}.stdout.txt'
    folders = (root / str(limit) / tag, root / str(limit), root / f'{limit}_{tag}', root / tag, root)
    for folder in folders:
        if (folder / filename).is_file():
            return folder
    raise ValueError(f'No stdout for {limit} {tag} below {root}')


def read_arm(root, limit, tree, cell, positions):
    tag = f'{tree}_{cell}'
    folder = find_folder(root, limit, tag)
    commands_path = folder / f'identity_{tag}.commands.txt'
    commands = commands_path.read_text().splitlines()
    if 'ucinewgame' not in commands:
        raise ValueError(f'{commands_path} has no search commands')
    first = commands.index('ucinewgame')
    expected = [command for fen in positions for command in
                ('ucinewgame', 'isready', f'position fen {fen}', f'go nodes {limit}')]
    if commands[first:] != expected + ['quit']:
        raise ValueError(f'{commands_path} does not match the prescribed FEN order and limit')
    stderr = folder / f'identity_{tag}.stderr.txt'
    if REFUSAL.search(stderr.read_text()):
        raise ValueError(f'{stderr} contains an engine refusal')
    searches = read_stdout(folder / f'identity_{tag}.stdout.txt', cell, len(positions))
    rows = ''.join(f'{search.row(index)}\n' for index, search in enumerate(searches, 1)).encode('ascii')
    rows_path = folder / f'rows_{tag}.txt'
    if rows_path.read_bytes() != rows:
        raise ValueError(f'{rows_path} differs from rows independently recovered from stdout')
    return searches


def compare(root, limit, positions, cells):
    findings = []
    print('| Limit | Cell | Searches per tree | k10f at limit | k11f at limit | Pf at limit | k10f/k11f rows equal | k11f/Pf final increases | Control |')
    print('| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |')
    for cell in cells:
        base, candidate, planted = [read_arm(root, limit, tree, cell, positions) for tree in TREES]
        rows_differ = []
        changed_moves_or_scores = 0
        control_wrong = []
        control_changes = 0
        over_cap = []
        for index, (a, b, c) in enumerate(zip(base, candidate, planted, strict=True), 1):
            if a.row(index) != b.row(index):
                rows_differ.append(index)
            changed_moves_or_scores += a.move_and_score() != b.move_and_score()
            if a.final_nodes > limit or b.final_nodes > limit:
                over_cap.append(index)
            control_changes += c.final_nodes > b.final_nodes
            if c.final_nodes != b.final_nodes + int(b.final_nodes == limit):
                control_wrong.append(index)
        control_pass = not control_wrong and control_changes > 0
        at_limit = [sum(s.final_nodes == limit for s in arm) for arm in (base, candidate, planted)]
        print(f'| {limit} | {cell} | {len(positions)} | {at_limit[0]} | {at_limit[1]} | {at_limit[2]} | '
              f'{"no" if rows_differ else "yes"} | {control_changes} | {"pass" if control_pass else "fail"} |')
        if rows_differ:
            index = rows_differ[0]
            findings.append((f'{cell} has {len(rows_differ)} k10f/k11f row differences '
                             f'({changed_moves_or_scores} bestmove or score changes)', index,
                             'k10f', base[index - 1], 'k11f', candidate[index - 1]))
        if over_cap:
            index = over_cap[0]
            findings.append((f'{cell} has {len(over_cap)} k10f/k11f pairs with a count above the cap', index,
                             'k10f', base[index - 1], 'k11f', candidate[index - 1]))
        if control_wrong:
            index = control_wrong[0]
            findings.append((f'{cell} has {len(control_wrong)} planted-control count mismatches', index,
                             'k11f', candidate[index - 1], 'Pf', planted[index - 1]))
        elif not control_pass:
            findings.append((f'{cell} planted control never changed the final count',))
    print()
    for finding in findings:
        print(finding[0])
        if len(finding) > 1:
            _, index, left_name, left, right_name, right = finding
            print(f'First affected fixture position {index} {positions[index - 1]}')
            for name, result in ((left_name, left), (right_name, right)):
                print(f'{name} row      {result.row(index)}')
                print(f'{name} last info {result.last_info}')
        print()
    scope = f'{limit} node limit' + (f' {cells[0]}' if len(cells) == 1 else '')
    print(f'{scope} {"FAILED" if findings else "PASS"}')
    return int(bool(findings))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('limit', type=int, choices=(50000, 250000))
    parser.add_argument('logs', type=Path, help='matrix root, limit folder, or flat raw folder')
    parser.add_argument('positions', type=Path, help='Job 4 fixture of 389 FENs')
    parser.add_argument('--cell', choices=CELLS, help='read back only this cell')
    args = parser.parse_args()
    try:
        cells = (args.cell,) if args.cell else CELLS
        return compare(args.logs, args.limit, read_positions(args.positions), cells)
    except (OSError, ValueError) as error:
        print(f'Readback failed for limit {args.limit}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
