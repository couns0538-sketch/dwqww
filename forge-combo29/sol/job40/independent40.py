#!/usr/bin/env python3
"""Verify the Job 40 archive and recount game-record changes by cell."""

import argparse
from collections import defaultdict
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import sys

import chess


HERE = Path(__file__).resolve().parent
WORK = Path('/workspace/work')
ARCHIVE = Path('forge-combo29/sol/job40')
for prior in (HERE.parent / 'job39', WORK / 'sol-job39'):
    if (prior / 'independent39.py').is_file():
        sys.path.insert(0, str(prior))
        break

from independent39 import (
    CHECKSUM, ENGINE_SHA, FINAL_STATUSES, NET_SHA, PC20_SHA, UCI_MOVE,
    Reader, check_game, check_setup, expected_settings, handoff_table, require,
)


LIMITS = {'N2': (410001, 'hard', 'go nodes 20000'), 'N1': (400001, 'soft', 'go softnodes 2000')}
CONTROLS = {
    'BASE': ('BASE-b', None, 'IDENTICAL'),
    'EvalSwingMax220': ('EvalSwingMax220', ('EvalSwingMax', 220), 'IDENTICAL'),
    'CaptureFutilityMultiplier275': ('CaptureFutilityMultiplier275', ('CaptureFutilityMultiplier', 275), 'IDENTICAL'),
    'LmrQuietBase101': ('LmrQuietBase/PLUS', ('LmrQuietBase', 101), 'DIFFERS'),
}


def design(handoff, local, reader, archive):
    source, _ = handoff_table(handoff)
    columns = 'name\tstart\tmin\tmax\tstep\tminus_variant\tminus\tplus\n'
    expected = [columns]
    cells = []
    substitution = []
    for name, start, low, high, step in source:
        lower = start - step
        if lower < low:
            lower = start + 2 * step
            variant = 'PLUS2'
            substitution.append(name)
        else:
            variant = 'MINUS'
        upper = start + step
        require(low <= lower <= high and low <= upper <= high, f'{name}: option value out of bounds')
        cells.append((name, variant, lower, upper))
        expected.append('\t'.join(map(str, (name, start, low, high, step, variant, lower, upper))) + '\n')
    require(substitution == ['DrawJitter', 'CaptureFutilityBase', 'FailLowContinuationBonus', 'EvalSwingMult'],
            'Wrong PLUS2 substitutions')
    raw = reader.read(local, archive / 'design40.tsv')
    require(raw == ''.join(expected).encode('ascii'), f'{local}: does not match the handoff table')
    return cells, sha256(raw).hexdigest()


def records_by_game(contents, first, label):
    groups = defaultdict(list)
    previous_game = first
    for number, row in enumerate(contents.decode('ascii').splitlines(keepends=True), 1):
        fields = row.split()
        require(len(fields) == 4, f'{label}: malformed row {number}')
        game, ply, move, nodes = fields
        game, ply, nodes = int(game), int(ply), int(nodes)
        require(row == f'{game} {ply} {move} {nodes}\n'
                and previous_game <= game < first + 20 and 8 <= ply < 300
                and UCI_MOVE.fullmatch(move) and nodes >= 0, f'{label}: invalid row {number}')
        preceding = groups[game]
        require(ply == (preceding[-1][0] + 1 if preceding else 8), f'{label}: noncontiguous ply at {number}')
        preceding.append((ply, move, nodes))
        previous_game = game
    return dict(groups)


def read_run(reader, path, tracked, label, limit, option, pc20, check_moves):
    first, mode, search = LIMITS[limit]
    effective = None if option is None else {'name': option[0], 'value': option[1]}
    result = {'run': f'{limit}/{label}', 'build': 'r15d', 'limit': limit, 'search': search,
              'first_game': first, 'last_game': first + 19, 'option': effective}
    wrapper = path.with_name(path.name + '.driver.out')
    wrapper_log = reader.read(wrapper, tracked.with_name(wrapper.name)).decode('utf-8') if wrapper.is_file() else None
    receipt = path / 'run.json'
    if not receipt.is_file() or not receipt.stat().st_size:
        started = wrapper.is_file() or (path.is_dir() and any(path.iterdir()))
        return {**result, 'status': 'unfinalized' if started else 'not played', 'games': 0, 'records': 0, 'nodes': 0}, None, {}
    meta = json.loads(reader.read(receipt, tracked / receipt.name))
    status = meta['status']
    require(status in FINAL_STATUSES, f'{label}: invalid run status')
    require((meta['build'], meta['limit'], meta['mode'], meta['search'], meta['option']) ==
            ('r15d', limit, mode, search, effective), f'{label}: unexpected run identity')
    require((meta['first_game'], meta['last_game'], meta['games_requested']) == (first, first + 19, 20),
            f'{label}: unexpected game range')
    require(meta['python_chess'] == '1.11.2' and meta['max_plies'] == 300 and meta['claim_draw'] is True,
            f'{label}: unexpected chess game settings')
    require(meta['exe_sha256'] == ENGINE_SHA['r15d'] and meta['external_net_sha256'] == NET_SHA
            and meta['external_net_checksum_expected'] == CHECKSUM, f'{label}: incorrect engine or net pin')

    raw = reader.read(path / 'records.txt', tracked / 'records.txt')
    setup = reader.read(path / 'uci-setup.txt', tracked / 'uci-setup.txt')
    hashes = {'records_sha256': sha256(raw).hexdigest(), 'uci_setup_sha256': sha256(setup).hexdigest()}
    require(all(meta[key] == value for key, value in hashes.items()), f'{label}: receipt hash mismatch')
    options = expected_settings(meta['external_net_file'], pc20, () if option is None else (option,))
    ready = check_setup(setup, options, meta, label)
    if status == 'complete':
        require(wrapper_log is not None and meta['active_line'] in wrapper_log, f'{label}: missing active net in wrapper')
    grouped = records_by_game(raw, first, label)
    games = meta['games']
    ids = [game['game'] for game in games]
    require(ids == list(range(first, first + len(games))) and set(grouped) <= set(ids)
            and len(games) == meta['games_completed'] <= 20
            and (status != 'complete' or len(games) == 20), f'{label}: wrong completed games')
    for game in games:
        rows = grouped.get(game['game'], [])
        require(len(rows) == game['plies'], f'{label}: wrong plies in game {game["game"]}')
        if check_moves or not rows:
            check_game(game, rows, f'{label} game {game["game"]}')
    records = sum(map(len, grouped.values()))
    nodes = sum(row[2] for rows in grouped.values() for row in rows)
    require((records, nodes) == (meta['positions_completed'], meta['last_info_nodes_sum'])
            and sum(meta['info_line_kinds'].values()) == records, f'{label}: wrong records or node total')
    result.update(status=status, games=len(games), records=records, nodes=nodes, ready_replies=ready, **hashes)
    return result, raw, grouped


def compare(base, current):
    a, left, before = base
    b, right, after = current
    if a['status'] != 'complete' or b['status'] != 'complete':
        return {'reading': 'NOT PLAYED' if b['status'] == 'not played' else 'INCOMPLETE',
                'games_differ': None, 'differing_games': [], 'first_difference': None}
    changed = sorted(game for game in before.keys() | after.keys() if before.get(game) != after.get(game))
    require((left == right) == (not changed), f'{b["run"]}: raw byte and game decisions disagree')
    first = next((
        {'line': i, 'left': old.decode('ascii') if old is not None else None,
         'right': new.decode('ascii') if new is not None else None}
        for i, (old, new) in enumerate(zip_longest(left.splitlines(), right.splitlines()), 1) if old != new
    ), None)
    return {'reading': 'DIFFERS' if changed else 'IDENTICAL', 'games_differ': len(changed),
            'differing_games': changed, 'first_difference': first}


def verify_limit(limit, cells, reader, args, pc20):
    loaded = {}

    def load(label, option):
        if label not in loaded:
            loaded[label] = read_run(reader, args.raw / limit / label, args.archive / 'raw' / limit / label,
                                     label, limit, option, pc20, args.check_moves)
        return loaded[label]

    base = load('BASE-a', None)
    gate = {}
    for name, (label, option, expected) in CONTROLS.items():
        outcome = compare(base, load(label, option))
        gate[name] = {**outcome, 'expected': expected, 'passes': outcome['reading'] == expected}

    settings = []
    for name, variant, lower, upper in (() if args.gate_only else cells):
        arms = {}
        for side, suffix, value in (('minus', variant, lower), ('plus', 'PLUS', upper)):
            arm = load(f'{name}/{suffix}', (name, value))
            arms[side] = {'variant': suffix, 'value': value, 'run': arm[0]['run'],
                          'status': arm[0]['status'], **compare(base, arm)}
        counts = [arm['games_differ'] for arm in arms.values()]
        if any(count for count in counts if count is not None):
            reading = 'LIVE'
        elif counts == [0, 0]:
            reading = 'NO CHANGE SEEN'
        elif all(arm['status'] == 'not played' for arm in arms.values()):
            reading = 'NOT PLAYED'
        else:
            reading = 'INCOMPLETE'
        settings.append({'name': name, 'reading': reading, **arms})
    return {
        'gate': {'passes': all(check['passes'] for check in gate.values()), 'checks': gate},
        'settings': settings, 'settings_complete': sum(all(row[arm]['status'] == 'complete' for arm in ('minus', 'plus'))
                                                       for row in settings),
        'live': sum(row['reading'] == 'LIVE' for row in settings),
        'no_change_seen': [row['name'] for row in settings if row['reading'] == 'NO CHANGE SEEN'],
        'runs': {result['run']: result for result, _raw, _groups in loaded.values()},
    }


def score_prediction(estimates, outcome, names):
    lower, upper = estimates['live']
    expected = estimates['no_change_seen']
    require(type(lower) is type(upper) is int and 0 <= lower <= upper <= len(names)
            and len(expected) == len(set(expected)) and set(expected) <= names, 'Invalid prediction')
    done = outcome['gate']['passes'] and outcome['settings_complete'] == len(names)
    live, subset = (outcome['live'], outcome['no_change_seen']) if done else (None, None)
    return {
        'live': {'forecast': [lower, upper], 'observed': live,
                 'grade': 'ungraded' if live is None else 'met' if lower <= live <= upper else 'missed'},
        'no_change_seen': {'forecast': expected, 'observed': subset,
                           'grade': 'ungraded' if subset is None else 'met' if set(expected) == set(subset) else 'missed',
                           'forecast_only': None if subset is None else sorted(set(expected) - set(subset)),
                           'observed_only': None if subset is None else sorted(set(subset) - set(expected))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--limit', choices=LIMITS)
    parser.add_argument('--gate-only', action='store_true', help='verify just the four gate comparisons')
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--rev', default='HEAD')
    parser.add_argument('--archive', type=Path, default=ARCHIVE)
    parser.add_argument('--handoff', type=Path, default=WORK / 'sol-job38' / 'opus-reply-39.md')
    parser.add_argument('--pc20', type=Path, default=WORK / 'sol-job2' / 'pc20-options.txt')
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--check-moves', action='store_true')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    require(chess.__version__ == '1.11.2', 'Expected python-chess 1.11.2')
    pc20 = args.pc20.read_bytes()
    require(sha256(pc20).hexdigest() == PC20_SHA, 'PC20 option hash differs')
    with Reader(args.repo, args.rev) as reader:
        cells, design_sha = design(args.handoff, args.raw.parent / 'design40.tsv', reader, args.archive)
        outcomes = {limit: verify_limit(limit, cells, reader, args, pc20.decode('ascii').splitlines())
                    for limit in ((args.limit,) if args.limit else LIMITS)}
        result = {'design_sha256': design_sha, 'limits': outcomes}
        if args.prediction:
            forecast = json.loads(reader.read(args.prediction, args.archive / 'prediction.json'))
            names = {row[0] for row in cells}
            result['prediction'] = {limit: score_prediction(forecast[limit], outcome, names)
                                    for limit, outcome in outcomes.items()}
        result['archive_blobs_verified'] = reader.verified
    output = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.json is not None:
        args.json.write_text(output)
    print(output, end='')


if __name__ == '__main__':
    main()
