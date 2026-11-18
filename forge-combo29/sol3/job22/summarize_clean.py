import argparse
import csv
import json
from pathlib import Path
import re


NODES = re.compile(r'\bnodes (\d+)\b')
FINAL = re.compile(r'info string softnodes nodes (\d+)')


def tsv(path):
    with path.open(newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def readback(path):
    saved = tsv(path / 'rows.tsv')
    engine = json.loads((path / 'summary.json').read_text())
    text = (path / 'engine.stdout.txt').read_text().splitlines()
    frames = []
    latest = ''
    final = None
    for line in text:
        if line.startswith('info depth '):
            latest = line
        elif match := FINAL.fullmatch(line):
            final = int(match[1])
        elif line.startswith('bestmove '):
            count = NODES.search(latest)
            label = str(final) if final is not None else count[1] if count else ''
            frames.append((line, latest, label))
            latest = ''
            final = None
    if engine['workload_complete']:
        assert len(frames) == len(saved), path
    assert len(frames) == engine['raw_bestmove_lines'], path
    assert len(saved) == engine['completed_searches'], path
    assert frames[:len(saved)] == [
        (row['bestmove_line'], row['last_info_line'], row['nodes']) for row in saved
    ], path
    markers = [line for line in text if line.startswith('info string NNUE v3 active: ')]
    if engine['startup_complete']:
        assert markers == [engine['net_active']]
        assert 'checksum 30ab43b4ba5db5f3' in markers[0]
    return engine, saved


def compare_d9(observed, reference):
    baseline = tsv(reference)[:200]
    assert len(baseline) == 200
    changes = []
    for row in observed:
        expected = baseline[int(row['w1_position']) - 1]
        assert row['fen'] == expected['fen']
        if row['nodes'] != expected['nodes'] or row['bestmove'] != expected['bestmove']:
            changes.append({'w1_position': int(row['w1_position']), 'fen': row['fen'],
                            'reference': expected['last_info'] + ' / ' + expected['bestmove'],
                            'observed': row['last_info_line'] + ' / ' + row['bestmove']})
    return {'compared': len(observed), 'node_or_move_differences': changes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clean', type=Path)
    parser.add_argument('diagnostics', type=Path)
    parser.add_argument('baseline', type=Path, help='Job 19 W1 directory')
    args = parser.parse_args()
    diagnostics = {run['run']: run for run in json.loads(args.diagnostics.read_text())['runs']}
    results = {}
    for summary in sorted(args.clean.glob('*/summary.json')):
        path = summary.parent
        engine, rows = readback(path)
        name = path.name
        log = diagnostics[name]
        seen = {'run': name, 'engine_exit': engine['engine_returncode'],
                'complete': engine['workload_complete'], 'stage': engine['stage'],
                'searches': engine['completed_searches'], 'raw_bestmoves': engine['raw_bestmove_lines'],
                'games': engine['completed_games'], 'phases': engine['phase_counts'],
                'known_nodes': sum(int(row['nodes']) for row in rows if row['nodes']),
                'searches_without_nodes': sum(row['nodes'] == '' for row in rows),
                'total_report_blocks': log['total_blocks'], 'distinct_reports': log['distinct_reports'],
                'startup_failure_blocks': log['runtime_failure_blocks'],
                'stderr_bytes': log['stderr_bytes']}
        if engine['part'] == 'au-d9':
            family = 'r15d' if name.startswith('AU-r15d-') else 'kF'
            seen['job19'] = compare_d9(rows, args.baseline / family / 'rows.tsv')
        if engine['part'] == 't-clean':
            durations = [int(row['go_to_stop_ns']) for row in tsv(path / 'infinite.tsv')]
            seen['infinite_stops'] = len(durations)
            seen['go_to_stop_ns_range'] = [min(durations), max(durations)] if durations else None
        results[name] = seen
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
