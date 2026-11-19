#!/usr/bin/env python3
"""Recount Job 39 games, settings, and archived record differences."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from itertools import zip_longest
import json
import os
from pathlib import Path
from random import Random
import re
import subprocess

import chess


ROOT = Path(__file__).resolve().parent
WORK = Path('/workspace/work')
ARCHIVE = Path('forge-combo29/sol/job39')
BUILDS = ('r15d', 'kF')
ENGINE_SHA = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
PC20_SHA = 'e355dbddb98abb000283ca7b37126e4cf71e152ce6df0bec8f1ea11fb715c7af'
CHECKSUM = '30ab43b4ba5db5f3'
CONTROLS = {'K39': 'K39b', 'C39': 'C39', 'L39': 'L39'}
STAGES = (*CONTROLS, 'A', 'B')
FINAL_STATUSES = ('complete', 'cut', 'refused', 'crash', 'hang', 'incomplete')
UCI_MOVE = re.compile(r'[a-h][1-8][a-h][1-8][qrbn]?')
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b', re.I)


def require(condition, context):
    if not condition:
        raise ValueError(context)


class Reader:
    """Read local bytes and optionally compare each input with its tracked blob."""

    def __init__(self, repo, rev):
        self.repo = repo
        self.rev = rev
        self.git = None
        self.verified = 0

    def __enter__(self):
        if self.repo is not None:
            self.git = subprocess.Popen(
                ['git', '-C', str(self.repo), 'cat-file', '--batch'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'},
            )
        return self

    def __exit__(self, *_):
        if self.git is not None:
            self.git.stdin.close()
            self.git.stdout.close()
            self.git.wait()

    def read(self, local, tracked):
        data = local.read_bytes()
        if self.git is not None:
            target = f'{self.rev}:{tracked.as_posix()}'
            self.git.stdin.write(target.encode('utf-8') + b'\n')
            self.git.stdin.flush()
            header = self.git.stdout.readline().split()
            require(len(header) == 3 and header[1] == b'blob', f'{target}: {header!r}')
            blob = self.git.stdout.read(int(header[2]))
            require(self.git.stdout.read(1) == b'\n' and data == blob, f'{target}: archive bytes differ')
            require(len(blob) <= 20_000_000, f'{target}: file over archive size limit')
            self.verified += 1
        else:
            require(len(data) <= 20_000_000, f'{local}: file over archive size limit')
        return data


def handoff_table(path):
    handoff = path.read_text()
    table = handoff.split('### The table', 1)[1].split('(Read across the lines', 1)[0]
    entries = [
        (name, *(int(value) for value in values))
        for name, *values in re.findall(r'([A-Z][A-Za-z0-9]+) +(\d+) +(\d+) +(\d+) +(\d+)', table)
    ]
    require(len(entries) == len({entry[0] for entry in entries}) == 40, f'{path}: malformed option table')
    pins = re.search(r'draw 1 = ([\d\s]+); draw 100 = ([\d\s]+)\. Any other line', handoff)
    require(pins, f'{path}: expected both known-answer vectors')
    return entries, {number: tuple(map(int, value.split())) for number, value in zip((1, 100), pins.groups())}


def check_draws(data, table, known):
    lines = []
    draws = {}
    for draw_id in range(1, 101):
        rng = Random(390000 + draw_id)
        vector = []
        for _, start, low, high, step in table:
            trial = start + step * rng.randrange(-6, 7)
            vector.append(high if trial > high else low if trial < low else trial)
        draws[draw_id] = tuple(vector)
        lines.append('\t'.join(map(str, (draw_id, *vector))) + '\n')
    require(all(draws[index] == vector for index, vector in known.items()), 'Known-answer draw mismatch')
    require(''.join(lines).encode('ascii') == data, 'Draws fixture differs from the handoff calculation')
    return draws


def declared_spins(data, table, context):
    lines = data.splitlines()
    require(lines.count('uciok') == 1, f'{context}: missing or repeated uciok')
    declarations = defaultdict(list)
    for line in lines:
        if match := re.fullmatch(r'option name (\S+) type spin default (-?\d+) min (-?\d+) max (-?\d+)', line):
            name, _default, low, high = match.groups()
            declarations[name].append((int(low), int(high)))
    for name, _start, low, high, _step in table:
        require(declarations[name] == [(low, high)], f'{context}: wrong declared spin bounds for {name}')


def expected_settings(net, pc20, name_value_pairs):
    return [
        'setoption name Threads value 1',
        'setoption name Hash value 16',
        *pc20,
        f'setoption name NNUEArchFile value {net}',
        'setoption name NNUEArch value true',
        *(f'setoption name {name} value {value}' for name, value in name_value_pairs),
    ]


def check_setup(data, expected, meta, context):
    lines = data.decode('utf-8').splitlines()
    option_commands = [line[2:] for line in lines if line.startswith('> setoption ')]
    ready = lines.count('> isready')
    readyok = lines.count('< readyok')
    sent = meta['settings_sent']
    sent_ready = meta['settings_ready_count']
    require(option_commands == expected[:len(option_commands)] and sent == option_commands[:len(sent)],
            f'{context}: setoption order or values differ')
    require(readyok <= sent_ready <= ready <= sent_ready + 1 and len(sent) <= len(option_commands) <= len(sent) + 1,
            f'{context}: readiness receipt disagrees')
    if meta['status'] != 'complete' and readyok < len(expected):
        return readyok
    require(readyok == len(expected) == len(sent), f'{context}: incomplete option handshakes')
    require(lines and lines[0] == '> uci' and lines.count('< uciok') == 1, f'{context}: invalid UCI handshake')
    chunks = lines[lines.index('< uciok') + 1:]
    start = 0
    for command in expected:
        require(chunks[start:start + 2] == ['> ' + command, '> isready'], f'{context}: misplaced ready for {command}')
        end = chunks.index('< readyok', start + 2)
        require(all(chunk.startswith('< ') for chunk in chunks[start + 2:end]), f'{context}: premature command')
        start = end + 1
    require(start == len(chunks) and not any(REFUSAL.search(line[2:]) for line in chunks if line.startswith('< ')),
            f'{context}: trailing UCI setup lines or refusal')
    for phrase, field in (('loaded', 'load_line'), ('active', 'active_line')):
        proof = [line[2:] for line in lines if line.startswith(f'< info string NNUE v3 {phrase}:')]
        if meta['status'] == 'complete' or field in meta:
            require(proof == [meta[field]] and f' checksum {CHECKSUM} ' in proof[0],
                    f'{context}: missing pinned {phrase} line')
    return readyok


@dataclass(frozen=True)
class Plan:
    name: str
    build: str
    draw: int | str
    mode: str
    first: int

    @property
    def search(self):
        return 'go nodes 20000' if self.mode == 'hard' else 'go softnodes 2000'


def parse_records(data, plan):
    groups = defaultdict(list)
    previous_game = plan.first
    for line_no, line in enumerate(data.decode('ascii').splitlines(keepends=True), 1):
        fields = line.split()
        require(len(fields) == 4, f'{plan.name}: malformed record {line_no}')
        game, ply, move, nodes = fields
        game, ply, nodes = int(game), int(ply), int(nodes)
        require(line == f'{game} {ply} {move} {nodes}\n' and UCI_MOVE.fullmatch(move)
                and 0 <= nodes and previous_game <= game < plan.first + 10 and 8 <= ply < 300,
                f'{plan.name}: invalid record {line_no}')
        rows = groups[game]
        require(ply == (rows[-1][0] + 1 if rows else 8), f'{plan.name}: noncontiguous ply at record {line_no}')
        rows.append((ply, move, nodes))
        previous_game = game
    return groups


def opening_seed(game):
    board, rng = chess.Board(), Random(game)
    for _ in range(8):
        legal_moves = tuple(board.legal_moves)
        board.push(legal_moves[rng.randrange(len(legal_moves))])
        if board.outcome(claim_draw=True) is not None:
            break
    return board


def check_game(game, rows, context):
    board = opening_seed(game['game'])
    opening = [move.uci() for move in board.move_stack]
    require((len(opening), opening, len(rows)) == (game['opening_plies'], game['opening_moves'], game['plies']),
            f'{context}: seeded opening or recorded game length differed')
    for ply, move, _nodes in rows:
        require(board.ply() == ply, f'{context}: board and record ply differ')
        board.push_uci(move)
    outcome = board.outcome(claim_draw=True)
    termination = outcome.termination.name.lower() if outcome is not None else '300_ply_limit' if board.ply() == 300 else None
    require(termination == game['termination'], f'{context}: wrong terminal result')


def read_run(reader, raw, archive, plan, names, draws, draws_sha, pc20, check_moves):
    local = raw / plan.name
    tracked = archive / 'raw' / plan.name
    meta_file = local / 'run.json'
    if not meta_file.is_file():
        status = 'unfinalized' if local.is_dir() and any(local.iterdir()) else 'not played'
        return {'status': status, 'games': 0, 'records': 0, 'nodes': 0}, None
    meta = json.loads(reader.read(meta_file, tracked / 'run.json'))
    status = meta['status']
    require(status in FINAL_STATUSES, f'{plan.name}: invalid status {status}')
    require(
        (meta['build'], meta['draw'], meta['mode'], meta['search'], meta['first_game'], meta['last_game'], meta['games_requested'])
        == (plan.build, plan.draw, plan.mode, plan.search, plan.first, plan.first + 9, 10),
        f'{plan.name}: run identity differs from schedule',
    )
    require(meta['python_chess'] == '1.11.2' and meta['max_plies'] == 300 and meta['claim_draw'] is True,
            f'{plan.name}: unexpected chess, max plies, or claim_draw setting')
    require(meta['exe_sha256'] == ENGINE_SHA[plan.build] and meta['external_net_sha256'] == NET_SHA
            and meta['external_net_checksum_expected'] == CHECKSUM, f'{plan.name}: pinned executable or net differs')
    pairs = dict(zip(names, map(str, draws[plan.draw]))) if isinstance(plan.draw, int) else {}
    if plan.name == 'C39':
        pairs['LmrQuietBase'] = '60'
    require(meta['draw_settings'] == pairs and meta['lmr60'] is (plan.name == 'C39'),
            f'{plan.name}: draw options differ from fixture')
    require(meta['draws_sha256'] == (draws_sha if pairs else None), f'{plan.name}: wrong draw SHA')
    data = reader.read(local / 'records.txt', tracked / 'records.txt')
    setup = reader.read(local / 'uci-setup.txt', tracked / 'uci-setup.txt')
    require(sha256(data).hexdigest() == meta['records_sha256'] and sha256(setup).hexdigest() == meta['uci_setup_sha256'],
            f'{plan.name}: artifact SHA differs from receipt')
    ready = check_setup(setup, expected_settings(meta['external_net_file'], pc20, pairs.items()), meta, plan.name)
    wrapper = local.parent / f'{local.name}.driver.out'
    if wrapper.is_file():
        wrapper_log = reader.read(wrapper, tracked.parent / wrapper.name).decode('utf-8')
        if status == 'complete':
            require(meta['active_line'] in wrapper_log, f'{plan.name}: wrapper missing active receipt')
    records = parse_records(data, plan)
    games = meta['games']
    ids = [game['game'] for game in games]
    require(ids == list(range(plan.first, plan.first + len(games))) and set(records) <= set(ids)
            and meta['games_completed'] == len(games) <= 10 and (status != 'complete' or len(games) == 10),
            f'{plan.name}: incorrect game identities or completion count')
    for game in games:
        rows = records.get(game['game'], [])
        require(len(rows) == game['plies'], f'{plan.name}: plies differ in {game["game"]}')
        if check_moves or not rows:
            check_game(game, rows, f'{plan.name} game {game["game"]}')
    count = sum(map(len, records.values()))
    nodes = sum(record[2] for rows in records.values() for record in rows)
    require((count, nodes) == (meta['positions_completed'], meta['last_info_nodes_sum'])
            and sum(meta['info_line_kinds'].values()) == count, f'{plan.name}: record or node total is wrong')
    return {
        'status': status, 'games': len(games), 'records': count, 'nodes': nodes,
        'records_sha256': meta['records_sha256'], 'ready_replies': ready,
        'last_command': meta.get('last_command'), 'last_reply': meta.get('last_reply'),
        'reason': meta.get('error', meta.get('stop_reason')),
    }, data


def compare(left, right):
    a, left_bytes = left
    b, right_bytes = right
    if a['status'] == b['status'] == 'not played':
        return {'reading': 'NOT PLAYED', 'first_difference': None}
    if a['status'] != 'complete' or b['status'] != 'complete':
        return {'reading': 'INCOMPLETE', 'first_difference': None}
    if left_bytes == right_bytes:
        return {'reading': 'IDENTICAL', 'first_difference': None}
    for line, (x, y) in enumerate(zip_longest(left_bytes.splitlines(), right_bytes.splitlines()), 1):
        if x != y:
            return {'reading': 'DIFFERS', 'first_difference': {
                'line': line, 'left': x.decode('ascii') if x is not None else None,
                'right': y.decode('ascii') if y is not None else None,
            }}
    raise ValueError('Unequal archives had no differing record line')


def summarize(stage, get):
    base, mode = (391000, 'hard') if stage == 'A' else (392000, 'soft')
    result = {f'draws_{name}': 0 for name in ('played', 'identical', 'differ', 'incomplete', 'not_played')}
    for field in ('games', 'records', 'nodes'):
        result[field] = dict.fromkeys(BUILDS, 0)
    result['draws'] = []
    counts = Counter()
    for number in range(1, 101):
        arms = [get(Plan(f'{stage}/draw-{number:03d}/{build}', build, number, mode, base + 10 * number)) for build in BUILDS]
        comparison = compare(*arms)
        counts[comparison['reading']] += 1
        for build, (run, _data) in zip(BUILDS, arms):
            for field in ('games', 'records', 'nodes'):
                result[field][build] += run[field]
        result['draws'].append({'draw': number, **comparison})
    result.update(
        draws_played=counts['IDENTICAL'] + counts['DIFFERS'], draws_identical=counts['IDENTICAL'],
        draws_differ=counts['DIFFERS'], draws_incomplete=counts['INCOMPLETE'], draws_not_played=counts['NOT PLAYED'],
    )
    result['reading'] = ('DIFFERS' if counts['DIFFERS'] else 'KEEPS' if counts['IDENTICAL'] == 100
                         else 'NOT PLAYED' if counts['NOT PLAYED'] == 100 else 'INCOMPLETE')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--stage', choices=STAGES)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--rev', default='HEAD')
    parser.add_argument('--archive', type=Path, default=ARCHIVE)
    parser.add_argument('--handoff', type=Path, default=WORK / 'sol-job38' / 'opus-reply-39.md')
    parser.add_argument('--pc20', type=Path, default=WORK / 'sol-job2' / 'pc20-options.txt')
    parser.add_argument('--check-moves', action='store_true', help='replay all completed games and verify terminal results')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    require(chess.__version__ == '1.11.2', 'Need python-chess 1.11.2 for seeded openings')
    table, known = handoff_table(args.handoff)
    names = [row[0] for row in table]
    pc20 = args.pc20.read_bytes()
    require(sha256(pc20).hexdigest() == PC20_SHA, 'PC20 pinned option file differs')
    with Reader(args.repo, args.rev) as reader:
        fixture = reader.read(args.raw.parent / 'draws.tsv', args.archive / 'draws.tsv')
        draws_sha = sha256(fixture).hexdigest()
        draws = check_draws(fixture, table, known)
        for build in BUILDS:
            evidence = Path('pin-evidence') / f'{build}.uci.raw.txt'
            data = reader.read(args.raw.parent / evidence, args.archive / evidence)
            declared_spins(data.decode('utf-8'), table, build)
        runs, cached, controls, comparisons = {}, {}, {}, {}

        def get(plan):
            if plan.name not in cached:
                cached[plan.name] = read_run(reader, args.raw, args.archive, plan, names,
                                             draws, draws_sha, pc20.decode('ascii').splitlines(), args.check_moves)
                runs[plan.name] = cached[plan.name][0]
            return cached[plan.name]

        for stage in (args.stage,) if args.stage else STAGES:
            if stage in CONTROLS:
                left = get(Plan('K39a', 'r15d', 1, 'hard', 390001))
                right = get(Plan(CONTROLS[stage], 'r15d', 'pc20' if stage == 'L39' else 1, 'hard', 390001))
                controls[stage] = compare(left, right)
                controls[stage]['passes'] = controls[stage]['reading'] == ('IDENTICAL' if stage == 'K39' else 'DIFFERS')
            else:
                comparisons[stage] = summarize(stage, get)
        result = {
            'draws_sha256': draws_sha, 'archive_blobs_verified': reader.verified,
            'runs': runs, 'control': controls, 'comparisons': comparisons,
        }
    output = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.json is not None:
        args.json.write_text(output)
    print(output, end='')


if __name__ == '__main__':
    main()
