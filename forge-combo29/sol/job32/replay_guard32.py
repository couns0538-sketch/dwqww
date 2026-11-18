#!/usr/bin/env python3
"""Replay the four pinned Astra5 null-mate guard suites and check their rows."""

import argparse
import csv
from hashlib import file_digest
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
for directory in (ROOT / 'job2', ROOT / 'sol-job2'):
    if (directory / 'run_matrix.py').is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit('missing adjacent Job 2 run_matrix.py')
from run_matrix import Engine, PC20, Refused, parse_row, utc_now

GUARD_UCI = 'option name NullMateGuard type spin default 0 min 0 max 2'
AGE_UCI = 'option name HistoryAgeKeep type spin default 1024 min 0 max 1024'
COLUMNS = ['index', 'fen', 'nodes', 'bestmove']
UCI_MOVE = re.compile(r'(?:[a-h][1-8]){2}[qrbn]?|0000|\(none\)')
CASES = (
    (0, 'O', 'zero', 200, 8315168, 'de704702e8e43556572e5954dd331135b6b20a4dfe0f81c55c7051c6b30fcca8'),
    (0, 'G', 'zero', 353, 17611204, 'f13c1318b1311ecf503541a4b88e07b5f57e9d1302723285fd95f31aaca0d930'),
    (2, 'O', 'one', 200, 8315218, '9d1c78d3e6dea536bb8da0625989c09174e5fb9f6bcc010a4c8a9a4c5825158b'),
    (2, 'G', 'one', 353, 17848355, '08aa8851206809aa791b892d76854511c21d631d2e531bdf6e776c8b8b6ca889'),
)


def digest(path):
    with path.open('rb') as source:
        return file_digest(source, 'sha256').hexdigest()


def checked_references(directory):
    reference_sets = {}
    for guard, suite, oracle, count, expected_sum, expected_hash in CASES:
        path = directory / oracle / f'{suite}.tsv'
        if digest(path) != expected_hash:
            raise ValueError(f'{path}: reference hash changed')
        with path.open(encoding='utf-8', newline='') as source:
            reader = csv.DictReader(source, delimiter='\t')
            if reader.fieldnames != COLUMNS:
                raise ValueError(f'{path}: unexpected TSV header {reader.fieldnames}')
            rows = [(int(row['index']), row['fen'], int(row['nodes']), row['bestmove']) for row in reader]
        if len(rows) != count or sum(row[2] for row in rows) != expected_sum:
            raise ValueError(f'{path}: reference count or node sum changed')
        if any(index != expected or len(fen.split()) != 6 or nodes < 0 or not UCI_MOVE.fullmatch(move)
               for expected, (index, fen, nodes, move) in enumerate(rows, 1)):
            raise ValueError(f'{path}: malformed reference row or unexpected ordering')
        if guard and [row[:2] for row in rows] != [row[:2] for row in reference_sets[0, suite]]:
            raise ValueError(f'{path}: guard-on and guard-off positions differ')
        reference_sets[guard, suite] = rows
    return reference_sets


def options_for(guard):
    return [('Threads', '1'), ('Hash', '16'), *PC20,
            ('HistoryAgeKeep', '1024'), ('NullMateGuard', str(guard))]


def check_uci(uci, options):
    for line in (GUARD_UCI, AGE_UCI, 'option name UseNNUE type check default true',
                 'option name NnueFile type string default <empty>'):
        if line not in uci:
            raise ValueError(f'expected UCI line {line!r}')
    for name, value in options:
        pattern = re.escape(f'option name {name} type ')
        if value in ('true', 'false'):
            pattern += 'check default (true|false)'
        else:
            pattern += r'spin default -?\d+ min (-?\d+) max (-?\d+)'
        candidate = next((match for line in uci if (match := re.fullmatch(pattern, line))), None)
        if not candidate:
            raise ValueError(f'option missing or differently typed in UCI list: {name}')
        if value not in ('true', 'false') and not int(candidate[1]) <= int(value) <= int(candidate[2]):
            raise ValueError(f'{name} requested value {value} is outside the advertised range')


def run_case(args, case, reference):
    guard, suite, oracle, count, expected_sum, expected_hash = case
    label = f'Guard{guard}-{suite}'
    raw = args.output / f'{label}.jsonl'
    sidecar = raw.with_suffix('.meta')
    options = options_for(guard)
    settings = [f'setoption name {name} value {value}' for name, value in options]
    meta = {
        'start_utc': utc_now(), 'command': sys.argv, 'exe': str(args.engine), 'exe_sha256': args.sha256,
        'preset': 'PC20', 'external_net_file': None, 'settings_sent': [], 'search': 'go depth 12',
        'reset_per_position': ['ucinewgame', 'isready'], 'guard': guard, 'suite': suite,
        'reference': f'{oracle}/{suite}.tsv', 'reference_sha256': expected_hash,
        'expected_rows': count, 'expected_nodes_sum': expected_sum,
        'compared': 0, 'equal': 0, 'nodes_sum': 0, 'last_depth12': 0, 'status': 'incomplete',
    }
    if raw.exists() or sidecar.exists():
        raise FileExistsError(f'refusing to overwrite {raw} or {sidecar}')
    with raw.open('x', encoding='utf-8') as output:
        try:
            with Engine(args.engine, 30) as engine:
                engine.send('uci')
                uci = engine.until('uciok')
                meta['uci'] = uci
                check_uci(uci, options)
                for command in settings:
                    engine.send(command)
                    meta['settings_sent'].append(command)
                engine.send('isready')
                meta['settings_reply'] = engine.until('readyok')
                for index, fen, expected_nodes, expected_move in reference:
                    engine.send('ucinewgame')
                    engine.send('isready')
                    engine.until('readyok')
                    engine.send(f'position fen {fen}')
                    engine.send(meta['search'])
                    lines = engine.until('bestmove')
                    row = parse_row(index, fen, lines, require_counter=False)
                    observed = row['nodes'], row['bestmove']
                    expected = expected_nodes, expected_move
                    match = observed == expected
                    output.write(json.dumps({
                        'index': index, 'fen': fen, 'depth': row['depth'], 'nodes': row['nodes'],
                        'bestmove': row['bestmove'], 'info': row['info'], 'bestmove_line': lines[-1],
                        'expected_nodes': expected_nodes, 'expected_bestmove': expected_move, 'equal': match,
                    }, separators=(',', ':')) + '\n')
                    meta['compared'] += 1
                    meta['equal'] += match
                    meta['nodes_sum'] += row['nodes']
                    meta['last_depth12'] += row['depth'] == 12
                    if not match and 'first_difference' not in meta:
                        meta['first_difference'] = {'index': index, 'observed': observed, 'expected': expected}
            meta['status'] = 'pass' if (meta['compared'], meta['equal'], meta['nodes_sum']) == (
                count, count, expected_sum,
            ) else 'gate_failed'
        except Exception as error:
            meta['status'] = 'refused' if isinstance(error, Refused) else 'incomplete'
            meta['error'] = f'{type(error).__name__}: {error}'
        finally:
            output.flush()
            meta['output_sha256'] = digest(raw)
            meta['end_utc'] = utc_now()
            with sidecar.open('x', encoding='utf-8') as receipt:
                json.dump(meta, receipt, indent=2)
                receipt.write('\n')
    return meta


def audit_raw(args, references):
    for guard, suite, _, count, expected_sum, expected_hash in CASES:
        path = args.output / f'Guard{guard}-{suite}.jsonl'
        meta = json.loads(path.with_suffix('.meta').read_text())
        if meta['status'] != 'pass' or any(meta[key] != value for key, value in (
            ('output_sha256', digest(path)), ('reference_sha256', expected_hash), ('expected_rows', count),
            ('guard', guard), ('search', 'go depth 12'), ('external_net_file', None), ('suite', suite),
            ('settings_sent', [f'setoption name {name} value {value}' for name, value in options_for(guard)]),
        )):
            raise ValueError(f'{path}: metadata readback failed')
        check_uci(meta['uci'], options_for(guard))
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        total, at_depth = 0, 0
        for row, expected in zip(rows, references[guard, suite], strict=True):
            info_words = row['info'].split()
            if info_words[:2] != ['info', 'depth']:
                raise ValueError(f'{path}: malformed depth info at row {row["index"]}')
            actual_depth = int(info_words[2])
            nodes = int(info_words[info_words.index('nodes') + 1])
            best = row['bestmove_line'].split()
            if best[0] != 'bestmove' or (row['index'], row['fen'], nodes, best[1]) != expected:
                raise ValueError(f'{path}: raw output differs from oracle at row {row["index"]}')
            if (actual_depth, nodes, best[1]) != (row['depth'], row['nodes'], row['bestmove']):
                raise ValueError(f'{path}: parsed fields differ from raw output at row {row["index"]}')
            total += nodes
            at_depth += actual_depth == 12
        if (len(rows), total, at_depth) != (meta['compared'], meta['nodes_sum'], meta['last_depth12']) or total != expected_sum:
            raise ValueError(f'{path}: total or depth readback differs')
        print(f'{path.name} SHA-256, settings, all {len(rows)}/{count} raw rows and {total:,} nodes verified; '
              f'{at_depth}/{count} last info lines at depth 12.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('validate', 'run', 'audit'))
    parser.add_argument('references', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--engine', type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    references = checked_references(args.references)
    if args.mode == 'validate':
        for guard, suite, oracle, count, expected_sum, expected_hash in CASES:
            print(f'{oracle}/{suite}.tsv SHA-256 {expected_hash}; {count} rows; {expected_sum:,} nodes; HG guard {guard}.')
        return 0
    if args.output is None:
        parser.error('--output is required for run and audit')
    if args.mode == 'audit':
        audit_raw(args, references)
        return 0
    if args.engine is None or not args.sha256 or not re.fullmatch('[0-9a-f]{64}', args.sha256):
        parser.error('run requires --engine and --sha256')
    args.engine = args.engine.resolve(strict=True)
    if digest(args.engine) != args.sha256:
        raise ValueError('HG executable SHA-256 does not match the provided pin')
    args.output.mkdir(parents=True, exist_ok=True)
    print('## Step 2. Astra5 known-answer replays\n', flush=True)
    print('HG with PC20, embedded AL1 s198, Threads 1, Hash 16 and HistoryAgeKeep 1024 ran `go depth 12` '
          'with `ucinewgame` and `isready` before each position, one engine process per suite and guard value.\n', flush=True)
    print('| Guard | Suite | Astra5 reference | Compared | Exact nodes and best move | Observed nodes | Expected nodes | Last info depth 12 | Gate |', flush=True)
    print('|---:|---|---|---:|---:|---:|---:|---:|---|', flush=True)
    for case in CASES:
        guard, suite, oracle, count, expected_sum, _ = case
        meta = run_case(args, case, references[guard, suite])
        print(f'| {guard} | {suite} | `{oracle}/{suite}.tsv` | {meta["compared"]:,}/{count:,} | '
              f'{meta["equal"]:,}/{count:,} | {meta["nodes_sum"]:,} | {expected_sum:,} | '
              f'{meta["last_depth12"]:,}/{count:,} | {meta["status"].upper()} |', flush=True)
        if meta['status'] != 'pass':
            print(f'\nStep 2 stopped in Guard{guard}-{suite}. {meta.get("error", meta.get("first_difference"))}', flush=True)
            return 2
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, TypeError, ValueError) as error:
        raise SystemExit(str(error)) from error
