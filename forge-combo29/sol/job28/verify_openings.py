"""Read back Job 28's actual scratch EPDs against the tracked PGNs and UHO."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import combinations
from json import loads
from pathlib import Path
from random import Random
from subprocess import check_output

ARCHIVE = Path('forge-combo29/sol')
PIN = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
CELLS = {'K17': (50, 7281), 'K18': (50, 7282), 'M1': (2000, 7283), 'M2': (1000, 7284)}
REQUIRED_JOB27 = {'job27/raw/K16.pgn', 'job27/raw/D2s.part01.pgn', 'job27/raw/D2s.part02.pgn'}


def position_keys(row):
    fields = tuple(row.split())
    assert len(fields) == 6, row
    return fields, fields[:4]


def git_paths(repo):
    tracked_files = check_output(
        ['git', 'ls-tree', '-r', '--name-only', 'HEAD', '--', ARCHIVE], cwd=repo, text=True,
    )
    paths = set()
    for name in tracked_files.splitlines():
        relative = Path(name).relative_to(ARCHIVE)
        if relative.suffix == '.pgn' and int(relative.parts[0].removeprefix('job')) < 28:
            assert relative.parts[1] == 'raw', name
            paths.add(relative.as_posix())
    assert REQUIRED_JOB27 <= paths
    return paths


def archived_openings(repo, paths, manifest):
    counts = Counter()
    inventory = {}
    for name in sorted(paths):
        raw = (repo / ARCHIVE / name).read_bytes()
        family = Counter()
        for line in raw.splitlines():
            if line.startswith(b'[FEN '):
                assert line.startswith(b'[FEN "') and line.endswith(b'"]'), line
                family[position_keys(line[6:-2])] += 1
        counts.update(family)
        inventory[name] = {'path': name, 'sha256': sha256(raw).hexdigest(), 'fen_tags': sum(family.values())}
    assert len(paths) == manifest['pgn_count']
    assert inventory == {entry['path']: entry for entry in manifest['files']}
    assert sum(counts.values()) == manifest['fen_tags']
    keys = tuple({entry[key_type] for entry in counts} for key_type in range(2))
    assert len(keys[0]) == manifest['distinct_exact']
    assert len(keys[1]) == manifest['distinct_first_four']
    print(f'Tracked pre-Job-28 PGNs {len(paths)}, FEN tags {sum(counts.values())}, '
          f'distinct exact {len(keys[0])}, distinct first-four {len(keys[1])}.')
    for name in sorted(REQUIRED_JOB27):
        print(f'Included {name}, {inventory[name]["fen_tags"]} FEN tags, SHA-256 {inventory[name]["sha256"]}.')
    return keys


def read_book(source, positions, wanted):
    digest = sha256()
    samples = {}
    with source.open('rb') as book:
        for ordinal, row in enumerate(book, 1):
            digest.update(row)
            if ordinal in wanted:
                samples[ordinal] = row.rstrip(b'\r\n')
    assert ordinal == positions and digest.hexdigest() == PIN and samples.keys() == wanted
    return samples


def verify(args):
    manifest_path = args.openings / 'manifest.json'
    manifest_data = manifest_path.read_bytes()
    manifest = loads(manifest_data)
    assert manifest['source']['sha256'] == PIN
    assert manifest['selection_order'] == list(CELLS)
    assert manifest['cells'].keys() == CELLS.keys()
    prior_exact, prior_first_four = archived_openings(args.repo, git_paths(args.repo), manifest['historical'])
    positions = manifest['source']['positions']
    ordinals = {}
    for cell, (count, seed) in CELLS.items():
        spec = manifest['cells'][cell]
        assert (spec['count'], spec['seed'], spec['sampled_ordinals']) == (count, seed, 2 * count + 32)
        ordinals[cell] = Random(seed).sample(range(1, positions + 1), spec['sampled_ordinals'])
    sample_rows = read_book(args.source, positions, {n for candidates in ordinals.values() for n in candidates})
    assigned = {}
    used = prior_first_four.copy()
    for cell, (count, _) in CELLS.items():
        selected = []
        for ordinal in ordinals[cell]:
            key = position_keys(sample_rows[ordinal])[1]
            if key not in used:
                used.add(key)
                selected.append(ordinal)
            if len(selected) == count:
                break
        spec = manifest['cells'][cell]
        assert selected == spec['source_line_numbers']
        contents = (args.openings / f'{cell}.epd').read_bytes()
        assert contents == b''.join(sample_rows[ordinal] + b'\n' for ordinal in selected)
        assert sha256(contents).hexdigest() == spec['sha256']
        entries = [position_keys(row) for row in contents.splitlines()]
        exact_keys = {entry[0] for entry in entries}
        first_four = {entry[1] for entry in entries}
        assert len(exact_keys) == len(first_four) == count
        assert not (exact_keys & prior_exact or first_four & prior_first_four)
        assert spec['fen_keys_sha256'] == [sha256(b' '.join(key)).hexdigest() for _, key in entries]
        assigned[cell] = (exact_keys, first_four)
        print(f'{cell} {count} distinct source rows and zero prior overlaps on both keys. SHA-256 {spec["sha256"]}.')
    for left, right in combinations(assigned, 2):
        assert all(not (a & b) for a, b in zip(assigned[left], assigned[right], strict=True))
        print(f'{left} / {right} overlap zero on both keys.')
    print(f'{positions} pinned source rows. Manifest SHA-256 {sha256(manifest_data).hexdigest()}.')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('repo', type=Path)
    parser.add_argument('openings', type=Path)
    verify(parser.parse_args())
