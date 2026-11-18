#!/usr/bin/env python3
"""Audit the HG guard matches and calculate the predeclared 20k pool."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / 'job32', HERE.parent / 'sol-job32'):
    if (candidate / 'analyze_matches32.py').is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit('Missing adjacent Job 32 analyzer')

import analyze_matches32 as hg
from analyze_matches31 import digest, penta_estimate, pooled_result


HG_SHA = '626cd562ddd9a64364d45adb92f7cd21f5bd8cbae5a24ca5908e8bd5585f8d97'
SCHEDULE = {
    # games, seed, A/B nodes per move, A/B NullMateGuard
    'K23': (50, 7331, 20000, 20000, 0, 0),
    'C23': (100, 7332, 40000, 80000, 0, 0),
    'M7': (2000, 7333, 20000, 20000, 2, 0),
    'M8': (500, 7334, 80000, 80000, 2, 0),
}
CONTROLS = ('K23', 'C23')
MATCHES = ('M7', 'M8')
M6_CHECKPOINT = 'ec0dd36b04e4facc8279371f390a2367973f9ffa'
M6_DIGESTS = {
    'meta': '7362eaf667a107270a3babb88269c0f1ab3de72fa3dc57568b1e831a7755dfdf',
    'out': '6cda909cf6f56a9c64b4ac92b2b1f0b0169e4124c82c2b518e1085567029e8ff',
    'pgn': 'b21f136baf9a26f9d9f752266af654349e55a9b4989edb134b672edb8b4e684c',
}


def read_m6(root, temporary):
    job = root / 'job32'
    raw = job / 'raw'
    pgn = hg.pgn_file(raw, 'M6', None, temporary)
    files = {suffix: raw / f'M6.{suffix}' for suffix in ('meta', 'out')}
    files['pgn'] = pgn
    missing = [suffix for suffix, path in files.items() if not path.is_file()]
    if missing:
        return None, 'missing ' + ', '.join(missing)
    for suffix, path in files.items():
        if digest(path) != M6_DIGESTS[suffix]:
            raise ValueError(f'{path}: SHA-256 differs from M6 checkpoint {M6_CHECKPOINT}')
    receipt = hg.read_manifest(job / 'openings/manifest.json')
    reserved = hg.receipt_aliases(job / 'opening-ep32.json', *receipt)
    return hg.audit(raw, 'M6', receipt, HG_SHA, pgn, reserved['M6'])


def control(name, row, reason, path, parser):
    if row is None or row.status != 'complete' or row.bounds is None:
        raise ValueError(f'{name} gate failed. {reason or hg.status(row)}.')
    if name == 'K23' and (row.pairs, row.same_moves, row.penta, row.elo, row.width) != (25, 25, (0, 0, 25, 0, 0), 0, 0):
        raise ValueError(f'{name} gate failed. Identical 1–1 pairs {row.equal_same}/{row.pairs}, penta {row.penta}.')
    if name == 'C23' and (row.pairs != 50 or row.bounds[1] >= 0):
        raise ValueError(f'{name} gate failed. {row.pairs} pairs and Elo {hg.number(row.elo)} {hg.interval(row.bounds)}.')
    tally = hg.tally_pairs(hg.parse_games(path, parser, exact_moves=True), exact_moves=name == 'K23')
    if tally != ((row.wins, row.losses, row.draws), row.penta, 0):
        raise ValueError(f'{name}: second UCI tally differs or a game ended abnormally')
    _, _, nodes_a, nodes_b, *_ = SCHEDULE[name]
    condition = 'All 25 reversed-color pairs scored 1–1 with identical ordered UCI moves.' if name == 'K23' else 'The upper 95% Elo endpoint is below zero.'
    print(f'{name} PASS. HG with PC20, embedded evaluation, Threads 1, Hash 16, HistoryAgeKeep 1024 and NullMateGuard 0. '
          f'A/B used {nodes_a:,}/{nodes_b:,} nodes per move. {condition} '
          f'A W-L-D {row.wins}-{row.losses}-{row.draws}, pentanomial {row.penta}, Elo {hg.number(row.elo)} {hg.interval(row.bounds)}.')


def read_prediction(path):
    forecasts, disclosures = {}, []
    for line in path.read_text().splitlines():
        match, _, comment = line.partition('#')
        if not match.strip() and comment.strip().lower().startswith('used prior numbers:'):
            disclosures.append(comment.partition(':')[2].strip())
        fields = match.split()
        if not fields:
            continue
        name, low, high, verdict = fields
        low, high = Fraction(low), Fraction(high)
        if name not in MATCHES or name in forecasts or low > high or verdict not in hg.READINGS:
            raise ValueError(f'{path}: invalid prediction {line!r}')
        forecasts[name] = (low, high), verdict
    if forecasts.keys() != set(MATCHES) or len(disclosures) != 1 or not disclosures[0]:
        raise ValueError(f'{path}: both forecasts and a single nonempty "# Used prior numbers:" line are required')
    return forecasts, disclosures[0]


def predictions(rows, readings, path):
    forecasts, disclosure = read_prediction(path)
    print('\n## Prediction grades\n')
    print(f'The frozen forecast disclosed its use of prior results.\n\n> {disclosure}\n')
    print('| Match | Forecast Elo | Observed / grade | Forecast reading | Observed / grade |')
    print('|---|---:|---|---|---|')
    for name, (row, _) in rows.items():
        predicted_range, expected = forecasts[name]
        rating = row.elo if row is not None else None
        verdict = readings[name] if rating is not None else 'unavailable'
        rating_grade = 'ungraded' if rating is None else 'met' if predicted_range[0] <= rating <= predicted_range[1] else 'missed'
        verdict_grade = 'ungraded' if rating is None or verdict == 'unavailable' else 'met' if verdict == expected else 'missed'
        print(f'| {name} | {hg.interval(predicted_range)} | {hg.number(rating)} / {rating_grade} | {expected} | {verdict} / {verdict_grade} |')


def pool20(prior, fresh):
    old, new = prior[0], fresh[0]
    if old is not None and new is not None and {hg.canonical_key(fen) for fen in old.fens} & {hg.canonical_key(fen) for fen in new.fens}:
        raise ValueError('M6 and M7 share a canonical opening')
    return pooled_result(old, new)


def result_table(rows, readings):
    print('\n## Job 33 matches\n')
    print('Both sides used pinned HG, PC20, embedded AL1 s198, Threads 1, Hash 16, HistoryAgeKeep 1024 and OwnBook false. '
          'A set NullMateGuard 2 and B set 0. M7’s reading is POOL20. M8 uses its own interval. The exact sign tests are descriptive.\n')
    print('| Match | Nodes per move | Status | Games | A W-L-D | Pentanomial | Same moves / pairs | Better | Worse | Two-sided exact p | Elo [95%] | Reading |')
    print('|---|---:|---|---:|---|---|---:|---:|---:|---:|---|---|')
    for name, (row, reason) in rows.items():
        nodes = SCHEDULE[name][2]
        verdict = readings[name]
        if row is None or not row.pairs:
            condition = reason if row is None else f'{hg.status(row)}, no complete pair'
            print(f'| {name} | {nodes:,} | {condition} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unavailable |')
            continue
        exact = hg.p_text(hg.sign_test(row.better, row.worse))
        print(f'| {name} | {nodes:,} | {hg.status(row)} | {2 * row.pairs:,} | {row.wins}-{row.losses}-{row.draws} | '
              f'{list(row.penta)} | {row.same_moves}/{row.pairs} | {row.better} | {row.worse} | {exact} | '
              f'{hg.number(row.elo)} {hg.interval(row.bounds)} | **{verdict}** |')


def print_pool(prior, fresh, pool):
    included, penta, elo, bounds, verdict = pool
    observations = (('M6', *prior), ('M7', *fresh))
    omitted = [f'{name} ({reason if row is None else hg.status(row)})' for name, row, reason in observations
               if row is None or row.status != 'complete']
    print('\n## POOL20\n')
    print('The pool adds the paired buckets from completed M6 and M7. A cut or missing match is named and its buckets are excluded. '
          'BETTER requires a wholly positive pooled interval and positive M7 Elo. WORSE requires a wholly negative pooled interval '
          'and negative M7 Elo. All other results are LEVEL.\n')
    print('| Included | Omitted | Pairs | Pentanomial | Elo [95%] | Reading |')
    print('|---|---|---:|---|---|---|')
    print(f'| {", ".join(row.name for row in included) or "none"} | {", ".join(omitted) or "none"} | {sum(penta):,} | '
          f'{list(penta) if penta else "n/a"} | {hg.number(elo)} {hg.interval(bounds)} | **{verdict}** |')
    if prior[0] is not None:
        print(f'\nThe pinned M6 standalone Elo was {hg.number(prior[0].elo)} {hg.interval(prior[0].bounds)}. '
              f'M6 PGN, transcript and sidecar matched the Job 32 checkpoint `{M6_CHECKPOINT}`.')


def compare_astra(path, pool, m8):
    receipt = json.loads(path.read_bytes())
    pools = {item['nodes']: item for item in receipt['pools']}
    if pools.keys() != {20000, 80000} or len(receipt['pools']) != 2:
        raise ValueError(f'{path}: expected one pool per named node budget')
    print('\n## Astra5 pools beside Sol\n')
    print('Astra5’s r15d guard build used PC20 and the corresponding fixed-node guard 2 versus 0 comparison. '
          'The pools are descriptive, with Astra5’s counted pairs kept in its own build and opening samples.\n')
    print('| Nodes per move | Sol Elo [95%] | Astra5 complete cells | Astra5 pairs | Astra5 pentanomial | Astra5 Elo [95%] |')
    print('|---:|---|---|---:|---|---|')
    for nodes, sol in ((20000, (pool[2], pool[3])), (80000, (m8.elo, m8.bounds) if m8 is not None else (None, None))):
        entry = pools[nodes]
        if not entry['cells']:
            print(f'| {nodes:,} | {hg.number(sol[0])} {hg.interval(sol[1])} | No completed cell available | 0 | n/a | n/a |')
            continue
        penta = entry['pentanomial']
        if (len(penta) != 5 or any(type(count) is not int or count < 0 for count in penta)
                or not sum(penta) or 2 * sum(penta) != entry['games']):
            raise ValueError(f'{path}: invalid {nodes:,} Astra5 counts')
        estimate = penta_estimate(tuple(penta), deterministic=True)
        elo, width = estimate if estimate is not None else (None, None)
        bounds = None if elo is None else (elo - width, elo + width)
        print(f'| {nodes:,} | {hg.number(sol[0])} {hg.interval(sol[1])} | {", ".join(entry["cells"])} | {sum(penta):,} | '
              f'{penta} | {hg.number(elo)} {hg.interval(bounds)} |')
    for nodes, entry in sorted(pools.items()):
        if entry.get('excluded'):
            print(f'\nThe Astra5 {nodes:,}-node pool excludes {", ".join(entry["excluded"])}.')
    print(f'\n[Astra5 pool source and archive hashes](sol/job33/{path.name})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--canonical', type=Path)
    parser.add_argument('--match', choices=SCHEDULE)
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--history-root', type=Path)
    parser.add_argument('--astra', type=Path)
    args = parser.parse_args()
    if not args.match and args.history_root is None:
        parser.error('--history-root is required to read the pinned M6 for POOL20')

    with TemporaryDirectory(prefix='sol-job33-joined-') as directory:
        temporary = Path(directory)
        prior = read_m6(args.history_root, temporary) if args.history_root is not None else (None, 'not read in standalone mode')
        # The HG runner and preflight are identical to Job 32. Only the grid and control names change.
        hg.SCHEDULE, hg.CONTROLS = SCHEDULE, CONTROLS
        receipt = hg.read_manifest(args.manifest)
        canonical = args.canonical or args.manifest.parent.parent / 'opening-ep33.json'
        reserved = hg.receipt_aliases(canonical, *receipt)
        rows = {}
        for name in (args.match,) if args.match else SCHEDULE:
            pgn = hg.pgn_file(args.raw, name, None, temporary)
            row, reason = hg.audit(args.raw, name, receipt, HG_SHA, pgn, reserved[name])
            if name in CONTROLS:
                control(name, row, reason, pgn, hg.pgn_module(None))
            else:
                rows[name] = row, reason
        if not rows:
            return
        pool = pool20(prior, rows['M7']) if 'M7' in rows and args.history_root is not None else None
        readings = {name: hg.reading(row) if name == 'M8' else pool[-1] if pool is not None else 'pool pending'
                    for name, (row, _) in rows.items()}
        if args.prediction:
            predictions(rows, readings, args.prediction)
        result_table(rows, readings)
        if pool is not None:
            print_pool(prior, rows['M7'], pool)
        if args.astra:
            if pool is None or 'M8' not in rows:
                parser.error('--astra requires both measured match results and POOL20')
            compare_astra(args.astra, pool, rows['M8'][0])


if __name__ == '__main__':
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error)) from error
