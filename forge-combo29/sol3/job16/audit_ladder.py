#!/usr/bin/env python3
"""Check Job 16 ladder evidence without importing its runner or starting an engine."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys


P = '2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1'
S14_PIN = 'facb7ff2bf4b9a758a013a52a5867d5c65522719c43f25183a5d71d20f0f9589'
OPTIONS = {
    'HistRework': (0, 3),
    'HistReworkQuiet': (-1, 3),
    'HistReworkCorrection': (-1, 3),
    **{f'QuietReadPlainR{i}': (0, 1) for i in range(1, 4)},
}
FIELDS = ('requested_depth', 'info_depth', 'bestmove', 'score_type', 'score', 'nodes')
ROW_FIELDS = (*FIELDS, 'last_info', 'bestmove_line', *(f'nc{i}' for i in range(5)))
MOVE = r'[a-h][1-8][a-h][1-8][qrbn]?'
BESTMOVE = re.compile(rf'bestmove ({MOVE}|0000)(?: ponder {MOVE})?')
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b|invalid FEN|NNUE v3 active', re.IGNORECASE)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings(profile, overrides):
    path = Path(__file__).with_name('S14.setoption.txt')
    if checksum(path) != S14_PIN:
        raise ValueError('S14 command source is not the pinned Astra ladder archive projection')
    s14 = path.read_text(encoding='ascii').splitlines()
    if profile == 'S14':
        base = s14
    else:
        base = [*s14[:2], 'setoption name MultiPV value 1',
                'setoption name UseNNUE value true', 'setoption name OwnBook value false',
                *s14[2:], 'setoption name CuckooRep value true',
                'setoption name HistRework value 2', 'setoption name TtPruneV2 value true',
                'setoption name CorrHistV2 value true', 'setoption name MateAlphaGuard value true']
    for override in overrides:
        name, equal, value = override.partition('=')
        if not equal or name not in OPTIONS or not re.fullmatch(r'-?\d+', value):
            raise ValueError(f'invalid override {override!r}')
        lo, hi = OPTIONS[name]
        if not lo <= int(value) <= hi:
            raise ValueError(f'override out of range: {override}')
        base.append(f'setoption name {name} value {int(value)}')
    return base


def command_check(commands, profile, overrides):
    expected = ['uci', *settings(profile, overrides), 'isready']
    for depth in range(1, 21):
        expected.extend(('ucinewgame', 'isready', f'position fen {P}', f'go depth {depth}'))
    expected.append('quit')
    if commands != expected:
        for index in range(max(len(expected), len(commands))):
            a = expected[index] if index < len(expected) else None
            b = commands[index] if index < len(commands) else None
            if a != b:
                raise ValueError(f'command line {index + 1}: wanted {a!r}, got {b!r}')


def verify_advertisements(lines, profile, overrides):
    expected = [
        'NNUEArch type check default false', 'UseNNUE type check default true',
        'MultiPV type spin default 1 min 1 max 8',
        'NullMateGuard type spin default 0 min 0 max 1',
        'HistReworkQuiet type spin default -1 min -1 max 3',
        'HistReworkCorrection type spin default -1 min -1 max 3',
    ]
    if profile == 'S14':
        expected.extend(('HistRework type spin default 0 min 0 max 3', 'OwnBook type check default true'))
        expected.extend(f'{flag} type check default false' for flag in ('CuckooRep', 'TtPruneV2', 'CorrHistV2', 'MateAlphaGuard'))
    for name in ('QuietReadPlainR1', 'QuietReadPlainR2', 'QuietReadPlainR3'):
        if any(line.startswith(f'option name {name} ') for line in lines) or any(arg.startswith(name+'=') for arg in overrides):
            expected.append(f'{name} type spin default 0 min 0 max 1')
    missing = [line for line in expected if f'option name {line}' not in lines]
    if missing:
        raise ValueError(f'wrong option advertisements: {missing}')


def parse_case(case, depth):
    info = [line for line in case if line.startswith('info depth ')]
    best = [line for line in case if line.startswith('bestmove ')]
    count = [line for line in case if line.startswith('NC0 ')]
    if not info or len(best) != 1 or len(count) != 1 or case[-2:] != [best[0], count[0]]:
        raise ValueError(f'D{depth}: expected depth info and exactly one final bestmove/NC0 pair')
    bestmatch = BESTMOVE.fullmatch(best[0])
    words = info[-1].split()
    score, nodes = words.index('score'), words.index('nodes')
    counters = [int(value) for value in count[0].split()[1:]]
    if bestmatch is None or len(counters) != 5 or words[score + 1] not in ('cp', 'mate'):
        raise ValueError(f'D{depth}: malformed comparison fields')
    started, shallow, cutoff, shallow_cutoff, mate = counters
    if not (0 <= mate <= shallow_cutoff <= min(shallow, cutoff) <= max(shallow, cutoff) <= started):
        raise ValueError(f'D{depth}: NC0 ordering violated {counters}')
    if int(words[2]) < 0 or int(words[nodes + 1]) < 0:
        raise ValueError(f'D{depth}: negative reported depth or node count')
    int(words[score + 2])
    values = (str(depth), words[2], bestmatch[1], words[score + 1], words[score + 2], words[nodes + 1],
              info[-1], best[0], *(str(c) for c in counters))
    return dict(zip(ROW_FIELDS, values, strict=True))


def parse_stdout(lines, actions, profile, overrides):
    diagnostic = next((line for line in lines if REFUSAL.search(line)), None)
    if diagnostic is not None:
        raise ValueError(f'refusal or external net activation: {diagnostic}')
    if lines.count('uciok') != 1 or lines.count('readyok') != actions.count('isready'):
        raise ValueError('unexpected number of UCI acknowledgements')
    if sum(line.startswith('NC0 ') for line in lines) != 20:
        raise ValueError('expected exactly 20 NC0 lines')
    uciok = lines.index('uciok')
    verify_advertisements(lines[:uciok], profile, overrides)
    ready = [i for i, line in enumerate(lines) if line == 'readyok']
    if len(ready) != 21 or uciok >= ready[0]:
        raise ValueError('expected a setup barrier before all 20 search barriers')
    return [parse_case(lines[start + 1:stop], depth)
            for depth, (start, stop) in enumerate(zip(ready[1:], [*ready[2:], len(lines)], strict=True), 1)]


def read_tsv(path):
    with path.open(encoding='ascii', newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def compare_rows(live, saved, keys):
    if len(live) != len(saved):
        return {'live_rows': len(live), 'saved_rows': len(saved)}
    for depth, (a, b) in enumerate(zip(live, saved, strict=True), 1):
        diff = {field: [a.get(field), b.get(field)] for field in keys if a.get(field) != b.get(field)}
        if diff:
            return {'depth': depth, 'differences_raw_expected': diff, 'raw': a, 'expected': b}
    return None


def audit(path, profile, overrides, reference):
    commands = path / 'engine.commands.txt'
    stdout = path / 'engine.stdout.txt'
    stderr = path / 'engine.stderr.txt'
    saved = path / 'rows.tsv'
    if stderr.read_bytes():
        raise ValueError(f'engine stderr has {stderr.stat().st_size} bytes')
    actions = commands.read_text(encoding='ascii').splitlines()
    command_check(actions, profile, overrides)
    raw = parse_stdout(stdout.read_text(encoding='ascii').splitlines(), actions, profile, overrides)
    saved_difference = compare_rows(raw, read_tsv(saved), ROW_FIELDS)
    reference_difference = compare_rows(raw, read_tsv(reference), FIELDS) if reference is not None else None
    first = next((row for row in raw if row['bestmove'] == 'g3g6' and
                  row['score_type'] == 'mate' and int(row['score']) > 0), None)
    return {
        'run': str(path), 'profile': profile, 'overrides': overrides,
        'records_from_raw': len(raw), 'nc0_lines': len(raw),
        'last_reported_depth_differs': [int(row['requested_depth']) for row in raw if row['requested_depth'] != row['info_depth']],
        'first_g3g6_mate': {field: first[field] for field in FIELDS} if first else None,
        'depth_20': {field: raw[-1][field] for field in FIELDS},
        'counter_sums': [sum(int(row[f'nc{i}']) for row in raw) for i in range(5)],
        'saved_rows_difference': saved_difference,
        'oracle': str(reference) if reference is not None else None,
        'oracle_first_difference': reference_difference,
        'sha256': {file.name: checksum(file) for file in (commands, stdout, stderr, saved)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--profile', choices=('S14', 'PC20'), required=True)
    parser.add_argument('--option', action='append', default=[])
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.run, args.profile, args.option, args.reference)
        print(json.dumps(result, indent=2))
        return int(result['saved_rows_difference'] is not None or result['oracle_first_difference'] is not None)
    except (OSError, ValueError, IndexError) as error:
        print(f'Ladder evidence failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
