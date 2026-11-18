#!/usr/bin/env python3
"""Verify all observable T2 fields and preserve any absent last-info count."""

from collections import Counter
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path


RAW = Path('raw')
BUILD_HASHES = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
NET_HASH = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'


def load(build):
    original = RAW / f'T2-{build}.records.txt'
    observed = RAW / f'T2-observed-{build}.records.txt'
    previous = json.loads(original.with_suffix('.txt.meta').read_bytes())
    replay = json.loads(observed.with_suffix('.txt.meta').read_bytes())
    raw = observed.read_bytes()
    assert raw.startswith(original.read_bytes()), f'{build}: a completed strict-prefix record changed'
    assert sha256(raw).hexdigest() == replay['records_sha256']
    assert replay['exe_sha256'] == BUILD_HASHES[build] and replay['external_net_sha256'] == NET_HASH
    for field in ('search', 'settings_sent', 'book_sha256', 'first_line', 'last_line', 'max_plies', 'claim_draw',
                  'load_line', 'active_line'):
        assert replay[field] == previous[field], (build, field)
    assert replay['status'] == 'complete' and replay['games_completed'] == 200
    assert [entry['book_line'] for entry in replay['games']] == list(range(2001, 2201))

    games = Counter()
    node_sum = 0
    missing = []
    rows = raw.decode('ascii').splitlines()
    for line in rows:
        number, ply, move, nodes = line.split()
        number, ply = int(number), int(ply)
        assert ply == games[number]
        games[number] += 1
        if nodes == 'NA':
            missing.append((number, ply, move))
        else:
            node_sum += int(nodes)
    assert {entry['book_line']: entry['plies'] for entry in replay['games']} == games
    assert (len(rows), node_sum) == (replay['positions_completed'], replay['last_info_nodes_sum'])
    assert len(missing) == replay['missing_info_count'] == len(replay['missing_info'])
    for (book, ply, move), evidence in zip(missing, replay['missing_info'], strict=True):
        assert (book, ply) == (evidence['book_line'], evidence['ply'])
        assert evidence['received'][-1].split()[:2] == ['bestmove', move]
        assert all(not line.startswith('info ') for line in evidence['received'])
    print(f'| {build} | {replay["games_completed"]} | {len(rows):,} | {len(missing)} | {node_sum:,} | `{replay["records_sha256"]}` |')
    return raw, rows, missing


def main():
    print('## Full T2 diagnostic readback\n')
    print('Both passes used the exact original hard-node protocol and settings. NA marks a missing info line. '
          'The node sum includes only values emitted by the engine.\n')
    print('| Build | Games | Records | Missing node fields | Sum of emitted node fields | SHA-256 |')
    print('|---|---:|---:|---:|---:|---|')
    left, left_rows, left_missing = load('r15d')
    right, right_rows, right_missing = load('kF')
    if left == right:
        print('\nThe diagnostic streams match byte for byte. The missing fields stayed explicitly unavailable.\n')
    else:
        delta = next((pair for pair in zip_longest(left_rows, right_rows) if pair[0] != pair[1]), None)
        print(f'\nThe diagnostic streams differ. First different rows are {delta!r}.\n')
    for name, positions in (('r15d', left_missing), ('kF', right_missing)):
        for book, ply, move in positions:
            print(f'- {name} book line {book}, ply {ply}, `{move}`, last-info nodes unavailable.')


if __name__ == '__main__':
    main()
