#!/usr/bin/env python3
"""Check Job 37 record bytes, worker receipts and block ratios independently."""

import argparse
from collections import Counter
import hashlib
from itertools import zip_longest
import json
from math import isclose, sqrt
from pathlib import Path
import random
import re
from statistics import mean, median, stdev
import subprocess

import chess


SCHEDULE = {'C37': 4, 'W0': 1, 'T1': 16, 'P1': 8}
ORDER = ('AB', 'BA', 'BA', 'AB')
LIMIT = 20_000_000
NET_CHECKSUM = '30ab43b4ba5db5f3'
ENGINE_HASHES = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
PC20_SHA = 'e355dbddb98abb000283ca7b37126e4cf71e152ce6df0bec8f1ea11fb715c7af'
MOVE = re.compile(rb'[a-h][1-8][a-h][1-8][qrbn]?')
T97 = (
    None, 12.7062047364, 4.3026527297, 3.1824463053, 2.7764451052, 2.5705818356,
    2.4469118511, 2.3646242510, 2.3060041352, 2.2621571629, 2.2281388520,
    2.2009851601, 2.1788128297, 2.1603686565, 2.1447866879, 2.1314495456,
)


def artifact(path, root, repo, revision, archive, allow_empty=False):
    content = path.read_bytes()
    assert (allow_empty or content) and len(content) <= LIMIT, path
    if repo is not None:
        target = archive / path.relative_to(root)
        archived = subprocess.check_output(['git', '-C', str(repo), 'show', f'{revision}:{target.as_posix()}'])
        assert archived == content, (str(revision), str(target))
    return content


def random_opening(game):
    board = chess.Board()
    rng = random.Random(game)
    for _ in range(8):
        board.push(rng.choice(list(board.legal_moves)))
        if board.is_game_over(claim_draw=True):
            break
    return board


def read_rows(data, base, workers, label, replay):
    assert not data or data.endswith(b'\n'), label
    rows, nodes_by_game, rows_by_game = {}, Counter(), Counter()
    last_game, last_ply, count, nodes_total = 0, 7, 0, 0
    for idx, line in enumerate(data.splitlines(), 1):
        game_text, ply_text, move, node_text = line.split(b' ')
        game, ply, nodes = int(game_text), int(ply_text), int(node_text)
        assert (base <= game < base + workers * 25 and game >= last_game
                and ply == (last_ply + 1 if game == last_game else 8)
                and ply < 300 and nodes > 0 and MOVE.fullmatch(move)), (label, idx, line)
        assert f'{game} {ply} {move.decode("ascii")} {nodes}'.encode() == line, (label, idx, line)
        if replay:
            rows.setdefault(game, []).append(move.decode('ascii'))
        else:
            rows.setdefault(game, [])
        rows_by_game[game] += 1
        nodes_by_game[game] += nodes
        last_game, last_ply = game, ply
        count += 1
        nodes_total += nodes
    return rows, count, nodes_total, rows_by_game, nodes_by_game


def check_settings(options, label):
    assert (len(options) == 24 and options[:2] == [['Threads', '1'], ['Hash', '16']]
            and options[-2][0] == 'NNUEArchFile' and Path(options[-2][1]).name == 'net768.nnue'
            and options[-1] == ['NNUEArch', 'true']), (label, options)
    commands = [f'setoption name {name} value {value}' for name, value in options]
    pc20_bytes = ('\n'.join(commands[2:-2]) + '\n').encode()
    assert hashlib.sha256(pc20_bytes).hexdigest() == PC20_SHA, label
    return commands


def check_worker_logs(read, files, receipts, commands, expected_nodes, base, workers, rows_by_game, nodes_by_game, label):
    valid_logs = 0
    for path in files:
        identifier = re.fullmatch(r'worker(\d+)\.out', path.name)
        assert identifier, (label, path.name)
        worker = int(identifier[1])
        lines = read(path.name, allow_empty=True).decode().splitlines()
        active = [line for line in lines if line.startswith('info string NNUE v3 active:')]
        if len(active) != 1:
            continue
        payload = [json.loads(line) for line in lines if line.startswith('{')]
        if len(payload) < 2 or not payload[0].get('settings_sent') or 'worker' not in payload[-1]:
            continue
        config, *games, final = payload
        assert config['settings_sent'] == commands and f' checksum {NET_CHECKSUM} ' in active[0], (label, path.name)
        assert config['active_line'] == active[0] and config['setup_reply'].count(active[0]) == 1, (label, path.name)
        assert config['setup_reply'][-1] == 'readyok' and f' checksum {NET_CHECKSUM} ' in config['load_line'], (label, path.name)
        if worker not in receipts:
            continue
        expected = receipts[worker]
        assert (expected['active_line'] == active[0] and final == expected
                and len(games) == expected['games_completed']), (label, path.name, final, expected)
        for i, game in enumerate(games):
            number = base + i * workers + worker
            assert (game['game'], game['records'], game['nodes']) == (number, rows_by_game[number], nodes_by_game[number]), (label, path.name, game)
            if game['records']:
                sample = re.fullmatch(rb'info string softnodes nodes (\d+).*', game['first_search_last_info'].encode())
                assert sample and 0 < int(sample[1]) <= game['nodes'], (label, path.name, game, expected_nodes)
        valid_logs += 1
    return valid_logs


def close_value(actual, expected, label):
    assert isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (label, actual, expected)


def check_run(folder, stage, block, arm, args):
    def read(name, allow_empty=False):
        return artifact(folder / name, args.raw, args.repo, args.rev, args.archive, allow_empty)

    label = f'{stage}/{block:02d}/{arm}'
    data = read('records.tsv', allow_empty=True)
    m = json.loads(read('run.json'))
    digest = hashlib.sha256(data).hexdigest()
    expected_build = 'kF' if stage in ('W0', 'T1') and arm == 'B' else 'r15d'
    expected_base = 199_000 if stage == 'W0' else 200_000 + 1000 * block
    expected_nodes = 3000 if stage == 'C37' and arm == 'B' else 2000
    assert (m['build'], m['base'], m['nodes']) == (expected_build, expected_base, expected_nodes), (label, m)
    assert m['record_sha256'] == digest and m['status'] in ('complete', 'interrupted', 'failed'), label
    assert m['engine_sha256'] == ENGINE_HASHES[expected_build] and m['net_sha256'] == NET_SHA, label
    assert m['python_chess'] == chess.__version__ and m['games_per_worker'] == 25, label
    commands = check_settings(m['settings'], label)

    workers = m['workers']
    if args.workers is not None:
        assert workers == args.workers, (label, workers)
    assert workers > 0 and m['games_requested'] == 25 * workers, label
    rows, count, nodes_total, rows_by_game, nodes_by_game = read_rows(data, expected_base, workers, label, args.replay)
    assert m['records'] == count, (label, m['records'], count)
    completed, receipts, receipt_pids = set(), {}, set()
    for entry in m['worker_receipts']:
        w = entry['worker']
        assert 0 <= w < workers and w not in receipts, (label, entry)
        if entry['pid'] is not None:
            assert entry['pid'] not in receipt_pids, (label, entry)
            receipt_pids.add(entry['pid'])
        receipts[w] = entry
        games_finished = entry['games_completed']
        assert 0 <= games_finished <= 25, (label, entry)
        worker_games = {expected_base + game * workers + w for game in range(games_finished)}
        assert worker_games.isdisjoint(completed), (label, entry)
        completed.update(worker_games)
        assert (entry['records'], entry['last_info_nodes_sum']) == (sum(rows_by_game[g] for g in worker_games),
                sum(nodes_by_game[g] for g in worker_games)), (label, entry)

    assert set(rows) <= completed and len(completed) == m['games_completed'], (label, m['games_completed'])
    log_pins = check_worker_logs(read, sorted(folder.glob('worker*.out')), receipts, commands, expected_nodes,
                                 expected_base, workers, rows_by_game, nodes_by_game, label)

    for game in completed - rows.keys():
        assert random_opening(game).is_game_over(claim_draw=True), (label, game, 'missing seeded game')
    if args.replay:
        for game, moves in rows.items():
            board = random_opening(game)
            for move in moves:
                assert not board.is_game_over(claim_draw=True), (label, game, board.ply(), move)
                board.push_uci(move)
            assert board.ply() == 300 or board.is_game_over(claim_draw=True), (label, game, 'nonterminal game')

    if m['status'] == 'complete':
        assert len(receipt_pids) == log_pins == workers and len(completed) == 25 * workers, label
        assert len(m['engine_ticks']) == workers and {ticks['pid'] for ticks in m['engine_ticks']} == receipt_pids, label
        assert all(ticks['user'] >= 0 and ticks['system'] >= 0 for ticks in m['engine_ticks']), label
        seconds = sum(ticks['user'] + ticks['system'] for ticks in m['engine_ticks']) / m['ticks_per_second']
        close_value(m['engine_cpu_seconds'], seconds, f'{label} engine CPU')
        close_value(m['wall_seconds'], m['monotonic_stop'] - m['monotonic_start'], f'{label} parent wall timer')
        assert m['engine_cpu_seconds'] > 0 and m['wall_seconds'] > 0, label

    return data, {
        'status': m['status'], 'build': expected_build, 'base': expected_base, 'nodes': expected_nodes, 'workers': workers,
        'records': count, 'node_sum': nodes_total, 'record_sha256': digest, 'games_completed': len(completed),
        'zero_search_game_ids': sorted(completed - rows.keys()), 'net_active_worker_logs': log_pins,
        'wall_seconds': m['wall_seconds'], 'engine_cpu_seconds': m['engine_cpu_seconds'],
        'started_utc': m['started_utc'], 'finished_utc': m['finished_utc'],
    }


def first_difference(left, right):
    for i, (a, b) in enumerate(zip_longest(left.splitlines(), right.splitlines()), 1):
        if a != b:
            return {'line': i, 'A': a.decode() if a is not None else None, 'B': b.decode() if b is not None else None}
    return None


def distribution(eligible, field):
    if not eligible:
        return None
    observations = [(block['A'][field], block['B'][field]) for block in eligible]
    ratios = [b / a for a, b in observations]
    count = len(ratios)
    center = mean(ratios)
    halfwidth = T97[count - 1] * stdev(ratios) / sqrt(count) if count > 1 else None
    return {'blocks': count, 'median': median(ratios), 'pooled': sum(b for _, b in observations) / sum(a for a, _ in observations),
            'mean': center, 'interval95': [center - halfwidth, center + halfwidth] if halfwidth is not None else None,
            'df': count - 1 if count > 1 else None, 'blocks_below_1': sum(ratio < 1 for ratio in ratios),
            'block_ratios': ratios}


def grade_interval(summary, comparator=(1.0, 1.0)):
    if summary is None or summary['interval95'] is None:
        return 'NOT DONE'
    low, high = summary['interval95']
    if high < comparator[0]:
        return 'PAYS'
    if low > comparator[1]:
        return 'COSTS'
    return 'NOT SEEN'


def read_stage(stage, args):
    blocks, eligible = {}, []
    prior_end = None
    for n in range(1, SCHEDULE[stage] + 1):
        folder = args.raw / stage / f'block-{n:02d}'
        orientation = ORDER[(n - 1) % len(ORDER)]
        runs, record_data = {}, {}
        for arm in orientation:
            if not (folder / arm / 'run.json').is_file():
                assert not any((folder / arm).glob('*')), (stage, n, arm, 'run.json missing')
                continue
            record_data[arm], runs[arm] = check_run(folder / arm, stage, n, arm, args)
            started = runs[arm]['started_utc']
            assert prior_end is None or started is None or prior_end <= started, (stage, n, arm, prior_end, started)
            prior_end = runs[arm]['finished_utc']
        if not runs:
            continue
        assert list(runs) == list(orientation[:len(runs)]), (stage, n, orientation, list(runs))
        block = {'order': orientation, **runs, 'complete': len(runs) == 2 and all(m['status'] == 'complete' for m in runs.values())}
        if block['complete']:
            same = record_data['A'] == record_data['B']
            block['record_identity'] = same
            if not same:
                block['first_difference'] = first_difference(record_data['A'], record_data['B'])
            if stage == 'C37' or (stage in ('T1', 'P1') and same):
                eligible.append(block)
        blocks[n] = block
    assert sorted(blocks) == list(range(1, len(blocks) + 1)), (stage, blocks.keys())
    wall, cpu = (distribution(eligible, name) for name in ('wall_seconds', 'engine_cpu_seconds'))
    return {'blocks': blocks, 'expected_blocks': SCHEDULE[stage], 'wall': wall, 'engine_cpu': cpu, 'reading_vs_1': grade_interval(wall)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw', type=Path)
    p.add_argument('--stage', choices=SCHEDULE)
    p.add_argument('--workers', type=int)
    p.add_argument('--replay', action='store_true', help='also regenerate and check all played moves')
    p.add_argument('--repo', type=Path)
    p.add_argument('--rev', default='HEAD')
    p.add_argument('--archive', type=Path, default=Path('forge-combo29/sol/job37/raw'))
    args = p.parse_args()
    assert chess.__version__ == '1.11.2', chess.__version__
    results = {stage: read_stage(stage, args) for stage in ([args.stage] if args.stage else SCHEDULE)}
    c37 = results.get('C37')
    if c37 is not None:
        c37['control_pass'] = c37['wall'] is not None and c37['wall']['blocks'] == 4 and c37['wall']['pooled'] > 1.10
    if 'T1' in results and 'P1' in results:
        t1, p1 = results['T1'], results['P1']
        p1_bias = p1['wall']['interval95'] if p1['reading_vs_1'] in ('PAYS', 'COSTS') else None
        t1['noise_comparator'] = p1_bias
        t1['reading_after_noise'] = grade_interval(t1['wall'], p1_bias) if p1_bias is not None else t1['reading_vs_1']
    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
