#!/usr/bin/env python3
"""Recount the Job 30 replay JSONL records and verify exact threshold choice."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path
import re


def sha256(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def readback(path, reference, positions):
    meta = json.loads(path.with_suffix('.meta').read_text())
    expected = [json.loads(line) for line in reference.read_text().splitlines()] if reference else None
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == len(positions) == 1200
    assert meta['output_sha256'] == sha256(path) and meta['status'] == 'complete'
    if expected:
        assert len(expected) == 1200 and meta['oracle_sha256'] == sha256(reference)
    prunes = whole = depth = equal = 0
    for index, (row, position) in enumerate(zip(rows, positions), 1):
        assert (row['index'], row['game'], row['ply']) == (index, 1 + (index - 1) // 60, (index - 1) % 60)
        assert row['position'] == position
        info_nodes = int(re.search(r'\bnodes (\d+)\b', row['info']).group(1))
        count, nodes = map(int, re.fullmatch(r'info string HP27 (\d+) (\d+)', row['hp27_line']).groups())
        bestmove = row['bestmove_line'].split()[1]
        assert (info_nodes, count, nodes, bestmove) == (row['nodes'], row['hp27_count'], row['hp27_nodes'], row['bestmove'])
        if expected:
            ref = expected[index - 1]
            assert (ref['index'], ref['nodes'], ref['hp27'], ref['hp27_nodes'], ref['bestmove']) == (
                index, info_nodes, count, nodes, bestmove,
            )
        assert int(row['final_nodes_info'].split()[-1]) == nodes if meta['search'].startswith('go softnodes ') else nodes == 20000
        prunes += count
        whole += nodes
        depth += info_nodes
        equal += info_nodes == nodes
    assert (prunes, whole, depth, equal) == tuple(meta[key] for key in (
        'hp27_count', 'hp27_nodes', 'last_info_nodes', 'matching_info_hp27_nodes',
    ))
    archive = ' and all four Kimi fields' if expected else ''
    print(f'{path.name} verified SHA-256, 1,200 positions and raw output fields{archive}; '
          f'{prunes} HP27 prunes, {whole} HP27 nodes, {depth} last-depth nodes, {equal} equal node fields.')
    return prunes, whole


def closest(member_order, totals, base_count, base_nodes):
    winner = member_order[0]
    numerator = {cap: abs(totals[cap][0] * base_nodes - base_count * totals[cap][1]) for cap in member_order}
    for cap in member_order[1:]:
        if numerator[cap] * totals[winner][1] < numerator[winner] * totals[cap][1]:
            winner = cap
    return winner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay_dir', type=Path)
    parser.add_argument('references', type=Path)
    parser.add_argument('games', type=Path)
    parser.add_argument('--mstar', type=Path)
    args = parser.parse_args()
    positions = []
    for game_line in args.games.read_text().splitlines()[:20]:
        _, fen, moves, _ = game_line.split('\t')
        turns = moves.split()
        assert len(turns) == 60
        positions.extend(f'position fen {fen}' + (' moves ' + ' '.join(turns[:ply]) if ply else '') for ply in range(60))
    soft, hard = ('keep896_soft.jsonl', 'keep896_hard.jsonl')
    totals = {2220: readback(args.replay_dir / soft, args.references / soft, positions)}
    assert totals[2220] == (1567, 4221357)
    assert readback(args.replay_dir / hard, args.references / hard, positions) == (63861, 24000000)
    if not args.mstar:
        return
    chosen = int(args.mstar.read_text().strip())
    order = [2220, 1600, 1200, 900, 600, 400, 250]
    base_count, base_nodes = 11633, 4561961
    for cap in order[1:]:
        totals[cap] = readback(args.replay_dir / f'm{cap}_soft.jsonl', None, positions)
    first_choice = closest(order, totals, base_count, base_nodes)
    small_count, small_nodes = totals[250]
    if first_choice == 250 and 4 * small_count * base_nodes < 3 * base_count * small_nodes:
        for cap in (150, 80):
            totals[cap] = readback(args.replay_dir / f'm{cap}_soft.jsonl', None, positions)
            order.append(cap)
    assert closest(order, totals, base_count, base_nodes) == chosen
    for cap in order:
        filename = 'keep896_soft.meta' if cap == 2220 else f'm{cap}_soft.meta'
        meta = json.loads((args.replay_dir / filename).read_text())
        assert f'setoption name HistoryPruneMultiplier value {cap}' in meta['settings_sent']
        assert 'setoption name HistoryAgeKeep value 896' in meta['settings_sent']
    count, nodes = readback(args.replay_dir / f'm{chosen}_hard.jsonl', None, positions)
    assert nodes == 24000000
    hard_archive = [json.loads(line) for line in (args.references / 'ka2_hard_dfl.jsonl').read_text().splitlines()]
    assert len(hard_archive) == 1200 and all(row['hp27_nodes'] == 20000 for row in hard_archive)
    assert sum(row['hp27'] for row in hard_archive) == 313423
    print(f'Exact integer cross-products independently selected m*={chosen} from {order}; '
          f'selected hard HP27 rate {1000 * count / nodes:.6f} vs archive 13.059292.')


if __name__ == '__main__':
    main()
