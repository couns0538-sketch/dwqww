#!/usr/bin/env python3
"""Audit Job 32 fixed-node matches and compare the independent Astra5 trials."""

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from math import hypot
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / 'job31', HERE.parent / 'sol-job31'):
    if (candidate / 'analyze_matches31.py').is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit('Missing the adjacent Job 31 analyzer')

from analyze_matches31 import (
    BOOK_SHA, FASTCHESS_REVISION, FASTCHESS_SHA, FASTCHESS_VERSION, HEX,
    SOURCE_POSITIONS, interval, number, parse_games, pgn_file, pgn_module,
    p_text, sign_test, status, summarize, tally_pairs, unround,
)
from analyze_matches30 import BASE, REFUSAL
from canonical_openings32 import canonical_key, receipt_aliases


SCHEDULE = {
    # games, seed, A/B nodes per move, A/B guard
    'K22': (100, 7321, 2000, 2000, 0, 0),
    'C22': (200, 7322, 1000, 2000, 0, 0),
    'M5': (8000, 7323, 2000, 2000, 2, 0),
    'M6': (2000, 7324, 20000, 20000, 2, 0),
}
CONTROLS = ('K22', 'C22')
MATCHES = ('M5', 'M6')
READINGS = ('BETTER', 'WORSE', 'LEVEL')
GUARD = 'NullMateGuard'
GUARD_OPTION = 'option name NullMateGuard type spin default 0 min 0 max 2'


def read_manifest(path):
    data = path.read_bytes()
    manifest = json.loads(data)
    source = manifest['source']
    if (source['sha256'], source['positions']) != (BOOK_SHA, SOURCE_POSITIONS) or manifest['cells'].keys() != SCHEDULE.keys():
        raise ValueError('The pinned opening source or cell grid differs')
    reserved = set()
    for name, (games, seed, *_) in SCHEDULE.items():
        cell = manifest['cells'][name]
        keys = set(cell['fen_keys_sha256'])
        if (cell['seed'] != seed or cell['count'] != games // 2 or len(keys) != cell['count']
                or reserved & keys or cell['file'] != f'{name}.epd'):
            raise ValueError(f'{name}: opening identity, count or disjointness differs')
        reserved.update(keys)
    return manifest, sha256(data).hexdigest()


def validate_preflight(meta, side, guard):
    options = (*BASE, ('HistoryAgeKeep', '1024'), (GUARD, str(guard)))
    settings = [f'setoption name {name} value {value}' for name, value in options]
    suffix = '' if side == 'a' else '_b'
    uci = meta[f'preflight_uci{suffix}']
    reply = meta[f'preflight_reply{suffix}']
    if (meta[f'settings_{side}'] != settings or meta[f'preflight_settings_sent{suffix}'] != settings
            or GUARD_OPTION not in uci or uci[-1:] != ['uciok'] or reply[-1:] != ['readyok']
            or any(REFUSAL.search(line) for line in (*uci, *reply))):
        raise ValueError(f'{meta["match"]} {side.upper()}: options differ or UCI preflight failed')
    return [f'option.{name}={value}' for name, value in options]


def audit(raw, name, receipt, hg_sha, pgn_path, reserved):
    path = raw / f'{name}.meta'
    if not path.is_file() or not path.stat().st_size:
        if pgn_path.exists() or (raw / f'{name}.out').exists():
            raise ValueError(f'{name}: match evidence exists without a finalized sidecar')
        return None, 'not played'
    meta = json.loads(path.read_bytes())
    manifest, manifest_sha = receipt
    games, seed, nodes_a, nodes_b, guard_a, guard_b = SCHEDULE[name]
    cell = manifest['cells'][name]
    expected = {
        'match': name, 'games_requested': games, 'seed': seed, 'nodes_a': nodes_a, 'nodes_b': nodes_b,
        'concurrency': 4, 'engine_a': 'A', 'engine_b': 'B', 'maxmoves': 300,
        'variant': None if name in CONTROLS else {'name': GUARD, 'value': '2'},
        'exe_sha256': hg_sha, 'exe_sha256_b': hg_sha, 'fastchess_sha256': FASTCHESS_SHA,
        'fastchess_revision': FASTCHESS_REVISION, 'fastchess_version': FASTCHESS_VERSION,
        'evaluation': 'Forge embedded evaluation', 'external_net_file': None,
        'book_sha256': cell['sha256'], 'book_openings_count': cell['count'],
        'book_source_sha256': BOOK_SHA, 'book_source_positions': SOURCE_POSITIONS,
        'book_manifest_sha256': manifest_sha, 'rating_interval_pairs': 1,
    }
    for key, value in expected.items():
        if meta.get(key) != value:
            raise ValueError(f'{name}: {key} recorded {meta.get(key)!r}, expected {value!r}')
    if Path(meta['book']).name != cell['file']:
        raise ValueError(f'{name}: actual opening filename differs from the manifest')
    if meta['status'] not in ('complete', 'interrupted'):
        return None, f'{meta["status"]} ({meta.get("error", "no final match")})'
    if meta['status'] == 'complete' and meta['fastchess_exit'] != 0:
        raise ValueError(f'{name}: complete match has a nonzero fastchess exit')
    argv = [meta['fastchess']]
    for side, engine, nodes, guard in (('a', meta['exe'], nodes_a, guard_a), ('b', meta['exe_b'], nodes_b, guard_b)):
        options = validate_preflight(meta, side, guard)
        argv.extend(('-engine', f'cmd={engine}', f'name={side.upper()}', *options))
        if nodes_a != nodes_b:
            argv.append(f'nodes={nodes}')
    argv.extend(('-each', 'proto=uci'))
    if nodes_a == nodes_b:
        argv.append(f'nodes={nodes_a}')
    argv.extend(('-openings', f'file={meta["book"]}', 'format=epd', 'order=random', '-srand', str(seed),
                 '-rounds', str(games // 2), '-games', '2', '-repeat', '-concurrency', '4', '-maxmoves',
                 '300', '-pgnout', f'file={meta["pgn"]}', '-ratinginterval', '1'))
    if meta['fastchess_command'] != argv:
        raise ValueError(f'{name}: engine, settings, book or node budget differs in the actual command')
    if not meta.get('pgn_sha256') and meta['status'] == 'interrupted' and not pgn_path.exists():
        return None, 'cut without a PGN or a complete pair'
    row = summarize(raw, name, meta, pgn_path)
    if row.status == 'complete' and row.note:
        raise ValueError(f'{name}: no final fastchess summary matches all completed pairs')
    used = set(map(canonical_key, row.fens))
    if not used <= reserved or len(set(map(canonical_key, row.paired_fens))) != row.pairs or (row.status == 'complete' and used != reserved):
        raise ValueError(f'{name}: missing, repeated or unassigned opening')
    return unround(row), ''


def control(name, row, reason, path, parser):
    if row is None or row.status != 'complete' or row.bounds is None:
        raise ValueError(f'{name} gate failed. {reason}.')
    if name == 'K22' and (row.pairs, row.same_moves, row.penta, row.elo, row.width) != (50, 50, (0, 0, 50, 0, 0), 0, 0):
        raise ValueError(f'{name} gate failed. Identical 1–1 pairs {row.equal_same}/{row.pairs}, penta {row.penta}.')
    if name == 'C22' and (row.pairs != 100 or row.bounds[1] >= 0):
        raise ValueError(f'{name} gate failed. {row.pairs} pairs and Elo {number(row.elo)} {interval(row.bounds)}.')
    tally = tally_pairs(parse_games(path, parser, exact_moves=True), exact_moves=name == 'K22')
    if tally != ((row.wins, row.losses, row.draws), row.penta, 0):
        raise ValueError(f'{name}: independent UCI tally differs or a game ended abnormally')
    condition = 'All 50 reversed-color pairs scored 1–1 with identical ordered UCI moves.' if name == 'K22' else 'The upper 95% Elo endpoint is below zero.'
    _, _, nodes_a, nodes_b, *_ = SCHEDULE[name]
    print(f'{name} PASS. HG with PC20, embedded evaluation, Threads 1, Hash 16, Keep 1024 and Guard 0. '
          f'A/B used {nodes_a:,}/{nodes_b:,} nodes per move. {condition} '
          f'A W-L-D {row.wins}-{row.losses}-{row.draws}, pentanomial {row.penta}, Elo {number(row.elo)} {interval(row.bounds)}.')


def reading(row):
    if row is None or row.bounds is None:
        return 'unavailable'
    low, high = row.bounds
    return 'BETTER' if low > 0 else 'WORSE' if high < 0 else 'LEVEL'


def predictions(rows, path):
    forecasts = {}
    for line in path.read_text().splitlines():
        fields = line.partition('#')[0].split()
        if not fields:
            continue
        match, low, high, verdict = fields
        low, high = Fraction(low), Fraction(high)
        if match not in MATCHES or match in forecasts or low > high or verdict not in READINGS:
            raise ValueError(f'{path}: invalid prediction {line!r}')
        forecasts[match] = (low, high), verdict
    if forecasts.keys() != set(MATCHES):
        raise ValueError(f'{path}: both M5 and M6 predictions are required')
    print('\n## Prediction grades\n')
    print('| Match | Forecast Elo | Observed / grade | Forecast reading | Observed / grade |')
    print('|---|---:|---|---|---|')
    for name, (row, _) in rows.items():
        bounds, expected = forecasts[name]
        rating = row.elo if row else None
        verdict = reading(row)
        grade = 'ungraded' if rating is None else 'met' if bounds[0] <= rating <= bounds[1] else 'missed'
        flag = 'ungraded' if verdict == 'unavailable' else 'met' if verdict == expected else 'missed'
        print(f'| {name} | {interval(bounds)} | {number(rating)} / {grade} | {expected} | {verdict} / {flag} |')


def match_table(rows):
    print('\n## Job 32 matches\n')
    print('HG on both sides with PC20, embedded evaluation, Threads 1, Hash 16, HistoryAgeKeep 1024 and OwnBook false. '
          'A used NullMateGuard 2 and B 0. Elo and its symmetric 95% interval use complete pairs. The exact two-sided sign test is descriptive.\n')
    print('| Match | Nodes per move | Status | Games | A W–L–D | Pentanomial | Same moves / pairs | Better | Worse | Exact p | Elo [95%] | Reading |')
    print('|---|---:|---|---:|---|---|---:|---:|---:|---:|---|---|')
    for name, (row, reason) in rows.items():
        nodes = SCHEDULE[name][2]
        if row is None or not row.pairs:
            print(f'| {name} | {nodes:,} | {reason or status(row)} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unavailable |')
            continue
        exact = p_text(sign_test(row.better, row.worse))
        penta = ', '.join(map(str, row.penta))
        print(f'| {name} | {nodes:,} | {status(row)} | {2 * row.pairs:,} | {row.wins}-{row.losses}-{row.draws} | '
              f'{penta} | {row.same_moves}/{row.pairs} | {row.better} | {row.worse} | {exact} | '
              f'{number(row.elo)} {interval(row.bounds)} | **{reading(row)}** |')


def compare(rows, path, manifest_sha):
    receipt = json.loads(path.read_bytes())
    if (receipt['sol_manifest_sha256'] != manifest_sha or len(receipt['rows']) != 6
            or any(prior['opening_overlap'] for prior in receipt['rows'])):
        raise ValueError('Astra5 receipt does not verify disjoint openings against this manifest')
    print('\n## Descriptive comparison with Astra5\n')
    print('Astra5 used its r15d guard build with the same embedded weights, PC20, Guard 2 versus 0, '
          'Threads 1, Hash 16 and fixed nodes on the pinned UHO source. Its native build differs from HG. '
          'I subtract the unrounded Elo estimates and combine paired 95% halfwidths in quadrature for the disjoint samples.\n')
    print('| Nodes | Astra5 job / seed | Astra5 games | Astra5 Elo [95%] | Sol match | Sol Elo [95%] | Sol minus Astra5 [95%] | Shared opening keys |')
    print('|---:|---|---:|---|---|---|---|---:|')
    for prior in receipt['rows']:
        name = 'M5' if prior['nodes'] == 2000 else 'M6'
        if name not in rows:
            continue
        row, _ = rows[name]
        difference = 'unavailable'
        if row is not None and row.elo is not None:
            center = float(row.elo) - prior['elo']
            width = hypot(float(row.width), prior['halfwidth'])
            difference = f'{number(center)} {interval((center - width, center + width))}'
        sol = f'{number(row.elo)} {interval(row.bounds)}' if row is not None else 'unavailable'
        print(f'| {prior["nodes"]:,} | {prior["job"]} / {prior["match"]} ({prior["seed"]}) | {prior["games"]:,} | '
              f'{prior["printed_elo"]} | {name} | {sol} | {difference} | {prior["opening_overlap"]} |')
    print(f'\n[Astra5 data and source hashes](sol/job32/{path.name}) · '
          f'[Job 8](https://github.com/couns0538-sketch/dwqww/blob/{receipt["astra5_commit"]}/forge-combo29/REPORT_astra5_job8.md) · '
          f'[Job 9](https://github.com/couns0538-sketch/dwqww/blob/{receipt["astra5_commit"]}/forge-combo29/REPORT_astra5_job9.md) · '
          f'[Job 11](https://github.com/couns0538-sketch/dwqww/blob/{receipt["astra5_commit"]}/forge-combo29/REPORT_astra5_job11.md)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--hg-sha', required=True)
    parser.add_argument('--match', choices=SCHEDULE)
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--astra', type=Path)
    parser.add_argument('--m5-pgn', type=Path)
    parser.add_argument('--m6-pgn', type=Path)
    args = parser.parse_args()
    if not HEX.fullmatch(args.hg_sha):
        parser.error('--hg-sha must contain the full HG SHA-256')
    receipt = read_manifest(args.manifest)
    reserved = receipt_aliases(args.manifest.parent.parent / 'opening-ep32.json', *receipt)
    explicit = {'M5': args.m5_pgn, 'M6': args.m6_pgn}
    with TemporaryDirectory(prefix='sol-job32-joined-') as temp_path:
        temporary = Path(temp_path)
        rows = {}
        for name in (args.match,) if args.match else SCHEDULE:
            pgn = pgn_file(args.raw, name, explicit.get(name), temporary)
            row, reason = audit(args.raw, name, receipt, args.hg_sha, pgn, reserved[name])
            if name in CONTROLS:
                control(name, row, reason, pgn, pgn_module(None))
            else:
                rows[name] = row, reason
        if rows:
            if args.prediction:
                predictions(rows, args.prediction)
            match_table(rows)
        if args.astra:
            compare(rows, args.astra, receipt[1])


if __name__ == '__main__':
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error)) from error
