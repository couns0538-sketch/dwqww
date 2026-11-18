#!/usr/bin/env python3
"""Recount Astra5's fixed-node guard pools from pinned Git blobs."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import log10, sqrt
from pathlib import Path
import re
import shlex
import subprocess

import chess


ROOT = 'forge-combo29'
VERSION = 'fastchess alpha 1.8.3 20261107-d7b47e8'
FASTCHESS = '202c09fc8291eb7b4d6b946b44448d0d9c9ee481b04243f06fa7158c45689270'
ENGINE = 'ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e'
BOOK = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
NET = 'a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638'
SCHEDULE = (
    (8, 'M2', 20_000, 7314, 800), (9, 'M2b', 20_000, 7324, 800),
    (11, 'M2c', 20_000, 7333, 800), (11, 'M2d', 20_000, 7334, 800),
    (12, 'M3', 80_000, 7343, 600), (12, 'M3b', 80_000, 7344, 600),
    (13, 'M3c', 80_000, 7353, 600), (13, 'M3d', 80_000, 7354, 600),
)
TAG = re.compile(rb'(?m)^\[(\w+) "([^"\r\n]+)"\]\r?$')
EVENT = re.compile(rb'(?m)(?=^\[Event ")')
POINTS = {b'1-0': 2, b'0-1': 0, b'1/2-1/2': 1}


def digest(data):
    return sha256(data).hexdigest()


def pgn_pairs(raw, name, requested):
    rounds = defaultdict(list)
    score_counts = Counter()
    opening_keys = set()
    game_count = 0
    for record in EVENT.split(raw):
        if not record.strip():
            continue
        headers = dict(TAG.findall(record))
        game_count += 1
        round_ = int(headers[b'Round'])
        assert 1 <= round_ <= requested // 2, (name, round_)
        white_a = headers[b'White'] == f'{name}-A'.encode()
        colors = tuple(headers[tag].decode() for tag in (b'White', b'Black'))
        assert set(colors) == {f'{name}-A', f'{name}-B'}, (name, round_, colors)
        fen = headers[b'FEN'].decode()
        fields = fen.split()
        assert len(fields) == 6, (name, round_, fen)
        if fields[3] != '-' and not chess.Board(fen).has_legal_en_passant():
            fields[3] = '-'
        key = ' '.join(fields[:4])
        opening_keys.add(key)
        if headers[b'Result'] == b'*':
            continue
        points = POINTS[headers[b'Result']]
        rounds[round_].append((white_a, key, points if white_a else 2 - points))
    penta = [0] * 5
    complete_keys = set()
    for round_, games in rounds.items():
        if len(games) == 1:
            continue
        assert len(games) == 2, (name, round_)
        a, b = games
        assert a[0] != b[0] and a[1] == b[1] and a[1] not in complete_keys, (name, round_)
        complete_keys.add(a[1])
        penta[a[2] + b[2]] += 1
        score_counts.update((a[2], b[2]))
    assert game_count <= requested, (name, game_count)
    return penta, [score_counts[i] for i in (2, 0, 1)], game_count, opening_keys


def estimate(penta):
    pairs = sum(penta)
    assert pairs
    mean = sum(n * i / 4 for i, n in enumerate(penta)) / pairs
    variance = sum(n * (i / 4 - mean) ** 2 for i, n in enumerate(penta)) / pairs
    distance = 1.959963984540054 * sqrt(variance / pairs)

    def logistic(score):
        return -400 * log10(1 / score - 1)

    center = logistic(mean)
    halfwidth = (logistic(mean + distance) - logistic(mean - distance)) / 2
    return center, center - halfwidth, center + halfwidth


def display(elo):
    center, lower, upper = elo
    return f'{center:+.2f} [{lower:+.2f}, {upper:+.2f}]'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('commit')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()

    def git(*command):
        return subprocess.check_output(['git', '-C', str(args.repo), *command])

    inventory = set(git('ls-tree', '-r', '--name-only', args.commit, '--', ROOT).decode().splitlines())

    def read(path):
        return git('show', f'{args.commit}:{path}') if path in inventory else None

    def required(path):
        raw = read(path)
        if raw is None:
            raise ValueError(f'Missing {args.commit}:{path}')
        return raw

    paths = [f'{ROOT}/REPORT_astra5_job{n}.md' for n in (8, 9, 11, 12, 13)]
    reports = {path: digest(blob) for path in paths if (blob := read(path)) is not None}
    settings = required(f'{ROOT}/astra5/job12/step0/pc20.txt').decode().splitlines()
    options = {f'option.{fields[2]}={fields[4]}' for line in settings if (fields := line.split())}
    assert len(options) == 22
    assert f'{NET}  src/nnue_weights.inc' in required(f'{ROOT}/astra5/job7/step0/r15d.sha256.txt').decode()
    build = required(f'{ROOT}/astra5/job12/build.txt').decode()
    assert all(pin in build for pin in (ENGINE, BOOK, VERSION, FASTCHESS))
    astra_build = f'{ROOT}/astra5/job7/A/build/build.txt'
    compiler_log = required(astra_build)
    assert b'-march=native' in compiler_log and b'-DFORGE_NNUE_V3=1' in compiler_log
    assert 'M3c' in required(f'{ROOT}/astra5/job13/prediction.txt').decode()

    cells = []
    transcripts = []
    pooled_keys = defaultdict(set)
    for job, name, nodes, seed, requested in SCHEDULE:
        source = f'{ROOT}/astra5/job{job}/{name}'
        label = f'job{job}/{name}'
        raw = {ext: read(f'{source}{ext}') for ext in ('.meta', '.pgn', '/elo.txt')}
        seeds = dict(label=label, job=job, match=name, nodes=nodes, seed=seed, games_requested=requested,
                     source=source, git_blobs={ext: digest(blob) for ext, blob in raw.items() if blob is not None})
        cells.append(seeds)
        if raw['.meta'] is None or raw['.pgn'] is None:
            seeds['status'] = 'missing metadata or PGN at pinned tip'
            continue
        details = raw['.meta'].decode()
        assert VERSION in details and f'engine SHA256 {ENGINE}' in details and f'SHA256 {BOOK}' in details
        assert f'A nodes {nodes}, B nodes {nodes}; seed {seed}; target games {requested}' in details
        command = shlex.split(next(line[8:] for line in details.splitlines() if line.startswith('command ')))
        assert set(x for x in command if x.startswith('option.')) == options | {'option.NullMateGuard=0', 'option.NullMateGuard=2'}
        assert f'nodes={nodes}' in command and '-repeat' in command
        assert [x for x in command if x.startswith('option.NullMateGuard=')] == ['option.NullMateGuard=2', 'option.NullMateGuard=0']
        assert all(value in details for value in ('uciok', 'readyok', 'option name NnueFile type string default <empty>',
                                                  'option name NNUEArch type check default false'))
        penta, wld, records, openings = pgn_pairs(raw['.pgn'], name, requested)
        pairs = sum(penta)
        seeds.update(pentanomial=penta, wld=wld, games_in_complete_pairs=2 * pairs, pgn_records=records)
        if pairs * 2 != requested or records != requested or not {'exit 0', 'status ended'} <= set(details.splitlines()):
            seeds['status'] = 'cut or incomplete at pinned tip'
            continue
        assert len(openings) == pairs, (name, len(openings), pairs)
        seeds['normalized_opening_keys'] = len(openings)
        assert not pooled_keys[nodes] & openings, (name, 'overlapping canonical starts')
        pooled_keys[nodes].update(openings)
        seeds['status'] = 'complete'
        seeds['elo_interval'] = estimate(penta)
        if raw['/elo.txt'] is not None:
            published = raw['/elo.txt'].decode()
            assert f'Match {name}; complete' in published and f'games in these complete pairs {requested}' in published
            assert list(map(int, re.search(r'(?m)^Pentanomial \[.*\] (.*)$', published)[1].split())) == penta
            line = re.search(r'Logistic Elo (.*?); fastchess 95% halfwidth (.*)', published)
            center, width = map(float, line.groups())
            assert all(abs(a - b) < 1e-8 for a, b in zip(seeds['elo_interval'], (center, center - width, center + width), strict=True))
            transcripts.append(f'Git blob {args.commit}:{source}/elo.txt\n{published}')

    pools = []
    for nodes in (20_000, 80_000):
        selected = [cell for cell in cells if cell['nodes'] == nodes and cell['status'] == 'complete']
        excluded = [f'{cell["label"]} ({cell["status"]})' for cell in cells if cell['nodes'] == nodes and cell['status'] != 'complete']
        penta = [sum(cell['pentanomial'][index] for cell in selected) for index in range(5)]
        elo = estimate(penta)
        pools.append(dict(nodes=nodes, cells=[cell['label'] for cell in selected], excluded=excluded, pentanomial=penta,
                          games=2 * sum(penta), elo_interval=elo, reading='LEVEL' if elo[1] <= 0 <= elo[2] else 'BETTER' if elo[1] > 0 else 'WORSE'))
    assert pools[0]['pentanomial'] == [29, 253, 1018, 255, 45]

    args.output.mkdir(parents=True, exist_ok=True)
    payload = dict(astra5_commit=args.commit, engine_sha256=ENGINE, embedded_net_sha256=NET,
                   book_sha256=BOOK, fastchess_sha256=FASTCHESS, native_build_log_sha256=digest(compiler_log),
                   report_hashes=reports, within_pool_opening_overlap=0, pools=pools, seeds=cells)
    (args.output / 'astra5-prior33.json').write_text(json.dumps(payload, indent=2) + '\n')
    (args.output / 'astra5-elo-source33.txt').write_text('\n'.join(text.rstrip() + '\n' for text in transcripts))
    table = [
        '## Astra5 comparison pools', '',
        "Astra5 used its r15d guard build with PC20, embedded AL1 s198, Threads 1, Hash 16, UHO openings and guard 2 against 0. Astra5 compiled with `-march=native` and `FORGE_NNUE_V3=1`, while its match preflight shows the alternate NNUE architecture defaults off. HG uses its separate `x86-64-v4` build and sets `HistoryAgeKeep 1024`. The pools stand beside each other as descriptive measurements from the respective builds and openings. [Astra5 build log](https://github.com/couns0538-sketch/dwqww/blob/" + args.commit + f"/{astra_build}) · [HG build](sol/job32/hg-build-receipt.txt)", '',
        "I counted completed pairs directly from the pinned PGNs and checked zero opening overlap within each pool after normalizing unusable en-passant targets. The symmetric 95% intervals use the same paired formula as HG. [Seed and Git blob provenance](sol/job33/astra5-prior33.json) · [Original Astra5 Elo receipts](sol/job33/astra5-elo-source33.txt)", '',
        '| Nodes per move | Astra5 matches included | Excluded | Games | Pentanomial | Elo [95%] | Reading |',
        '|---:|---|---|---:|---|---|---|',
    ]
    for pool in pools:
        table.append(f'| {pool["nodes"]:,} | {", ".join(pool["cells"])} | {", ".join(pool["excluded"]) or "none"} | '
                     f'{pool["games"]:,} | {", ".join(map(str, pool["pentanomial"]))} | {display(pool["elo_interval"])} | {pool["reading"]} |')
    table.extend(('', f'Comparison archived on Astra5 tip `{args.commit}`.'))
    (args.output / 'astra5-pools33.md').write_text('\n'.join(table) + '\n')
    print('\n'.join(table))


if __name__ == '__main__':
    main()
