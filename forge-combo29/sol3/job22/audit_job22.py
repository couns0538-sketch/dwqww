#!/usr/bin/env python3
"""Read back completed Job 22 raw UCI and sanitizer logs independently."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from statistics import median


COUNT = re.compile(r'\bnodes (\d+)\b')
DEPTH = re.compile(r'^info depth (\d+)\b')
SOFT = re.compile(r'^info string softnodes nodes (\d+)$')
SANITIZER = re.compile(r'ERROR: AddressSanitizer:|WARNING: ThreadSanitizer:|FATAL: ThreadSanitizer:|'
                       r'runtime error:|AddressSanitizer:DEADLYSIGNAL|ERROR: LeakSanitizer:')
ACTIVE = ' hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 '
COUNTER = b"Location is global 'forge::SanitizerControlNodes'"


def file_hash(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def lines(path):
    return path.read_text().splitlines()


def table(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def expect(observed, expected, label):
    if observed != expected:
        raise ValueError(f'{label}: got {repr(observed)[:500]}, expected {repr(expected)[:500]}')


def stdout_rows(path):
    raw = lines(path)
    active = [line for line in raw if line.startswith('info string NNUE v3 active:')]
    rows = []
    depth = ''
    final = []
    for index, line in enumerate(raw, 1):
        if line.startswith('info depth '):
            depth = line
        elif soft := SOFT.fullmatch(line):
            final.append(int(soft[1]))
        elif line.startswith('bestmove '):
            rows.append({'bestmove': line.split()[1], 'depth': int(DEPTH.match(depth)[1]) if depth else None,
                         'depth_nodes': int(COUNT.search(depth)[1]) if depth else None, 'soft': final,
                         'depth_info': depth, 'bestmove_line': line, 'stdout_line': index})
            depth = ''
            final = []
    return rows, active


def command_rows(commands, initial_options, net_path):
    startup = ['uci'] + [f'setoption name {key} value {value}' for key,value in initial_options.items()]
    startup += [f'setoption name NNUEArchFile value {net_path}', 'setoption name NNUEArch value true', 'isready']
    expect(commands[:len(startup)], startup, 'startup UCI profile')
    position = None
    threads = int(initial_options['Threads'])
    output = []
    changes = []
    reset_count = 0
    stops = 0
    rest = commands[len(startup):]
    for index, line in enumerate(rest):
        if line.startswith('position fen '):
            position = line.removeprefix('position fen ')
        elif line.startswith('setoption name Threads value '):
            threads = int(line.split()[-1])
            changes.append(threads)
        elif line == 'ucinewgame':
            expect(rest[index+1], 'isready', 'new game barrier')
            reset_count += 1
        elif line.startswith('go '):
            if position is None:
                raise ValueError(f'search {len(output) + 1} has no position command')
            if line == 'go infinite':
                expect(rest[index+1], 'stop', 'go infinite stop')
            output.append((line, position, threads, reset_count))
            position = None
        elif line == 'stop':
            stops += 1
    return output, changes, reset_count, stops


def verify_metadata(path, omitted=()):
    summary = json.loads((path / 'summary.json').read_text())
    if not summary.get('finished_utc'):
        raise ValueError(f'no end time in {path}')
    for name, digest in summary['files_sha256'].items():
        if name not in omitted:
            expect(file_hash(path / name), digest, f'{path.name} {name} SHA-256')
    return summary


def assert_active(active, summary):
    expect(active, [summary['net_active']], 'raw net active marker')
    if ACTIVE not in active[0] or not active[0].endswith(' kernel avx512'):
        raise ValueError(f'wrong net identity {active}')


def verify_control(path, fens, kind, position, exit_code, initial_options, net_path):
    summary = verify_metadata(path)
    raw, active = stdout_rows(path / 'engine.stdout.txt')
    assert_active(active, summary)
    expect(summary['engine_returncode'], exit_code, f'{path.name} exit')
    expect((len(raw), summary['raw_bestmove_lines'], summary['completed_searches']), (0, 0, 0), f'{path.name} bestmove count')
    commands = lines(path / 'engine.commands.txt')
    profile = {**initial_options, 'Threads': 2 if kind == 'race' else 1}
    searches, changes, resets, stops = command_rows(commands, profile, net_path)
    go = 'go nodes 50000' if kind == 'race' else 'go depth 9'
    expect((searches, changes, resets, stops), ([(go, fens[position-1], profile['Threads'], 1)], [], 1, 0), f'{path.name} command plan')
    stderr = (path / 'engine.stderr.txt').read_bytes()
    target = {'address': b'ERROR: AddressSanitizer: heap-buffer-overflow',
              'undefined': b'runtime error: signed integer overflow',
              'race': b'WARNING: ThreadSanitizer: data race'}[kind]
    expect(stderr.count(target), 1, f'{path.name} expected checker report')
    if kind == 'race':
        expect(stderr.count(COUNTER), 1, f'{path.name} named counter')
    return {'name': path.name, 'position': position, 'command': go, 'threads': profile['Threads'],
            'exit': exit_code, 'bestmoves': len(raw), 'report_blocks': 1, 'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
            'checker_line': next(line.decode() for line in stderr.splitlines() if target in line),
            'summary_line': next((line.decode() for line in stderr.splitlines() if line.startswith(b'SUMMARY:')), None)}


def verify_flood(path, baseline, fens):
    summary = verify_metadata(path, omitted=('engine.stderr.txt',))
    expect(summary['engine_returncode'], -15, 'interrupted C-T process signal')
    expect(summary['raw_bestmove_lines'], 0, 'interrupted C-T bestmove lines')
    raw, active = stdout_rows(path / 'engine.stdout.txt')
    assert_active(active, summary)
    expect(len(raw), 0, 'interrupted C-T raw bestmove lines')
    commands = lines(path / 'engine.commands.txt')
    observed = command_rows(commands, {**baseline['pc20'], 'Threads': 2}, baseline['net_path'])
    expect(observed, ([('go nodes 50000', fens[0], 2, 1)], [], 1, 0), 'interrupted C-T issued commands')
    receipt = lines(path / 'stderr_parts.receipt.txt')
    sha = hashlib.sha256()
    size = 0
    count = 0
    report_headers = 0
    named = 0
    part_count = 0
    for part in sorted((path / 'stderr_parts').glob('part-*.txt')):
        part_count += 1
        part_sha = hashlib.sha256()
        with part.open('rb') as handle:
            for line in handle:
                sha.update(line)
                part_sha.update(line)
                size += len(line)
                count += 1
                report_headers += line.startswith(b'WARNING: ThreadSanitizer:')
                named += COUNTER in line
        expected_hash = next(line.split()[0] for line in receipt if line.endswith('/' + part.name))
        expect(part_sha.hexdigest(), expected_hash, part.name)
    expect(size, int(next(line.split()[-1] for line in receipt if line.startswith('Raw bytes:'))), 'flood bytes')
    expect(count, int(next(line.split()[-1] for line in receipt if line.startswith('Raw lines:'))), 'flood lines')
    expect(report_headers, int(next(line.split()[-1] for line in receipt if line.startswith('TSan WARNING headers:'))), 'flood report headers')
    expect(sha.hexdigest(), summary['files_sha256']['engine.stderr.txt'], 'flood join SHA in summary')
    if sha.hexdigest() not in receipt or named == 0:
        raise ValueError('missing flood SHA or named control')
    return {'parts': part_count, 'bytes': size, 'lines': count, 'warning_headers': report_headers, 'named_locations': named,
            'stderr_sha256': sha.hexdigest(), 'bestmoves': len(raw), 'exit': summary['engine_returncode']}


def verify_clean(path, baseline_root, fens):
    import chess

    summary = verify_metadata(path)
    part = summary['part']
    build = 'r15d' if 'r15d' in path.name else 'kF'
    expected = json.loads((baseline_root / build / 'summary.json').read_text())
    raw, active = stdout_rows(path / 'engine.stdout.txt')
    expect(len(raw), summary['raw_bestmove_lines'], f'{path.name} raw bestmove lines')
    output = table(path / 'rows.tsv')
    expect(len(output), summary['completed_searches'], f'{path.name} row count')
    expect(summary['fixture_sha256'], expected['fixture_sha256'], f'{path.name} fixture SHA')
    expect(summary['net_sha256'], expected['net_sha256'], f'{path.name} net SHA')
    diagnostics = []
    previous = ''
    with (path / 'engine.stderr.txt').open() as handle:
        line_count = 0
        for number, line in enumerate(handle, 1):
            line_count = number
            if SANITIZER.search(line):
                if 'DEADLYSIGNAL' not in line or 'DEADLYSIGNAL' not in previous:
                    diagnostics.append({'line': number, 'header': line.rstrip('\n'), 'root_frames': []})
            if line.lstrip().startswith('#0 ') and diagnostics:
                diagnostics[-1]['root_frames'].append(line.rstrip('\n'))
            if line.startswith('SUMMARY: ') and diagnostics:
                diagnostics[-1]['summary'] = line.rstrip('\n')
            previous = line
    result = {'name': path.name, 'workload_complete': summary['workload_complete'], 'stage': summary['stage'],
              'exit': summary['engine_returncode'], 'bestmoves': len(raw), 'searches': len(output), 'stderr_lines': line_count,
              'diagnostic_headers': diagnostics, 'report_blocks': len(diagnostics), 'protocol_error': summary['protocol_error']}
    if not summary['startup_complete']:
        return result
    assert_active(active, summary)
    commands, changes, resets, stops = command_rows(lines(path / 'engine.commands.txt'), expected['pc20'], expected['net_path'])
    counts = {}
    games = {}
    differences = []
    valid_stops = []
    if part == 'au-d9':
        plain, _ = stdout_rows(baseline_root / build / 'engine.stdout.txt')
        plain_rows = table(baseline_root / build / 'rows.tsv')
        expect(len(plain), 1000, f'{build} plain baseline count')
        plain_commands = lines(baseline_root / build / 'engine.commands.txt')
        candidate_commands = lines(path / 'engine.commands.txt')
        expect(candidate_commands[-1], 'quit', f'{path.name} clean shutdown command')
        expect(candidate_commands[:-1], plain_commands[:len(candidate_commands)-1], f'{path.name} W1 command prefix')
    for number, (row, found, command) in enumerate(zip(output, raw, commands), 1):
        go, position, threads, current_resets = command
        index = int(row['w1_position'])
        phase = row['phase']
        raw_fen, _, history = position.partition(' moves')
        expect(raw_fen, fens[index - 1], f'{path.name} row {number} fixture FEN')
        expect((int(row['search']), row['bestmove'], row['last_info_line'], row['bestmove_line'], int(row['threads'])),
               (number, found['bestmove'], found['depth_info'], found['bestmove_line'], threads), f'{path.name} row {number} raw')
        phase_counts = counts.setdefault(phase, {'searches': 0, 'known_nodes': 0, 'searches_without_nodes': 0})
        phase_counts['searches'] += 1
        nodes = found['depth_nodes']
        if go == 'go softnodes 2000':
            board, moves, game_nodes = games.get(index, (chess.Board(raw_fen), [], 0))
            expect(history.split(), moves, f'{path.name} game {index} history')
            expect((board.is_game_over(claim_draw=True), int(row['ply']), board.fen()), (False, len(moves)+1, row['fen']), f'{path.name} game {index} current row')
            expect(len(found['soft']), 1, f'{path.name} final softnodes marker count')
            phase_name = 'au-games' if part == 'au-games' else 't-games'
            expect((phase, threads, current_resets), (phase_name, 1, index - 200 if phase_name == 'au-games' else index - 207),
                   f'{path.name} game {index} phase/threads/reset')
            nodes = found['soft'][0]
            move = board.parse_uci(found['bestmove'])
            if not move:
                raise ValueError(f'null game move at {index}:{number}')
            board.push(move)
            moves.append(found['bestmove'])
            games[index] = board, moves, game_nodes + nodes
        elif part == 'au-d9':
            expect((phase, go, index, current_resets, row['fen']), ('au-d9', 'go depth 9', number, number, raw_fen), f'{path.name} row {number} depth-9 command')
            base = plain[number - 1]
            expect((base['depth_nodes'], base['bestmove'], plain_rows[number - 1]['fen']),
                   (int(plain_rows[number - 1]['nodes']), plain_rows[number - 1]['bestmove'], raw_fen), f'{build} baseline verification {number}')
            if (nodes, found['bestmove']) != (base['depth_nodes'], base['bestmove']):
                differences.append({'row': number, 'fen': raw_fen, 'plain': base, 'au': found})
        else:
            expect(index, number, f'{path.name} fixed fixture index')
            is_stop = index % 5 == 0
            expect((go, phase), ('go infinite','t-infinite') if is_stop else ('go nodes 50000', 't-nodes'), f'{path.name} fixed UCI action')
            block = (index - 1) // 30
            expect((threads, row['fen'], current_resets), (2**block, raw_fen, block + 1), f'{path.name} fixed threads, reset and FEN')
            if is_stop:
                valid_stops.append((index, threads))
        expect(int(row['nodes']) if row['nodes'] else None, nodes, f'{path.name} row {number} nodes')
        phase_counts['known_nodes'] += nodes or 0
        phase_counts['searches_without_nodes'] += nodes is None
    expect(counts, summary['phase_counts'], f'{path.name} phase counts')
    game_rows = table(path / 'games.tsv')
    expect(len(game_rows), summary['completed_games'], f'{path.name} completed games')
    for row in game_rows:
        index = int(row['w1_position'])
        board, moves, nodes = games[index]
        outcome = board.outcome(claim_draw=True)
        expect((row['moves'].split(), int(row['plies']), int(row['nodes'])), (moves, len(moves), nodes), f'{path.name} game {index} totals')
        expect((row['termination'], row['result']), (outcome.termination.name, outcome.result()) if outcome else ('PLY_CAP', '*'), f'{path.name} game {index} result')
    if summary['workload_complete']:
        expect(len(commands), len(output), f'{path.name} completed search commands')
        if part == 'au-d9':
            expect((len(output), stops, changes, resets), (200, 0, [], 200), f'{path.name} completed depth-9 plan')
        elif part == 'au-games':
            expect((list(games), len(game_rows), stops, changes, resets), (list(range(201, 211)), 10, 0, [], 10), f'{path.name} completed AU games')
        elif part == 't-clean':
            expect((list(games), len(game_rows), stops, changes, resets), (list(range(211, 215)), 4, 18, [2,4,1], 7), f'{path.name} completed T games')
    result.update({'phase_counts': counts, 'verified_games': len(game_rows), 'raw_search_commands': len(commands),
                   'node_move_differences_vs_job19': differences, 'node_sum': sum(item['known_nodes'] for item in counts.values())})
    timing = table(path / 'infinite.tsv')
    if summary['workload_complete']:
        expect([(int(row['w1_position']),int(row['threads'])) for row in timing], valid_stops, f'{path.name} timed position/threads')
    if timing:
        elapsed = []
        for row in timing:
            started = int(row['go_monotonic_ns'])
            scheduled = int(row['scheduled_stop_monotonic_ns'])
            stopped = int(row['stop_monotonic_ns'])
            expect(scheduled - started, 100_000_000, f'{path.name} stop schedule')
            observed = stopped - started
            expect(observed, int(row['go_to_stop_ns']), f'{path.name} actual stop elapsed')
            if stopped < scheduled:
                raise ValueError(f'{path.name} sent stop before schedule')
            elapsed.append(observed / 1_000_000)
        result.update({'timed_stops': len(elapsed), 'stop_elapsed_ms': [min(elapsed), median(elapsed), max(elapsed)]})
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('sol3', type=Path)
    cli.add_argument('--controls', action='store_true')
    cli.add_argument('--clean', action='append', default=[])
    args = cli.parse_args()
    fens = lines(args.sol3 / 'job19/positions.txt')
    baseline_root = args.sol3 / 'job19/W1'
    baseline = json.loads((baseline_root / 'r15d/summary.json').read_text())
    job = args.sol3 / 'job22'
    result = {}
    if args.controls:
        specs = [('C-AU', 'address', 1, 1), ('C-UB', 'undefined', 1, 1)]
        specs.extend((f'C-T-pos-{i}', 'race', i, 66) for i in range(1, 6))
        result['controls'] = [verify_control(job / 'controls' / name, fens, kind, position, ex,
                                             baseline['pc20'], baseline['net_path']) for name,kind,position,ex in specs]
        result['interrupted_C-T'] = verify_flood(job / 'controls/C-T', baseline, fens)
    if args.clean:
        result['clean'] = [verify_clean(job / 'clean' / name, baseline_root, fens) for name in args.clean]
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
