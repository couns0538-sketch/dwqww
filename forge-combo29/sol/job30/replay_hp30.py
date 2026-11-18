#!/usr/bin/env python3
"""Run Job 30 HC oracles and select a history-pruning threshold by exact rate."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
for candidate in (ROOT / 'job28', ROOT / 'sol-job28'):
    if (candidate / 'replay_known28.py').is_file():
        sys.path.insert(0, str(candidate))
        break
from replay_known28 import Engine, PC20, key, ordered_rows, parse_row, read_games, sha256, utc_now

ROW_COUNT = 1200
HP_INFO = re.compile(r'info string HP27 (\d+) (\d+)')
SOFT = 'go softnodes 2000'
HARD = 'go nodes 20000'
HC_SHA = '2c664f4e0f6099a4bed0a3db162d2a07fd479d175fedf5ae7c90e4c1ef875875'
BASELINE = (11633, 4561961)
HARD_BASELINE = (313423, 24000000)
CAPS = (2220, 1600, 1200, 900, 600, 400, 250)
EXTENSION_CAPS = (150, 80)
KNOWN = (
    ('keep896_soft', SOFT, 4080162, 1567, 4221357),
    ('keep896_hard', HARD, 16285974, 63861, 24000000),
)


def settings(multiplier):
    pc20 = [(name, str(multiplier) if name == 'HistoryPruneMultiplier' else value) for name, value in PC20]
    return [f'setoption name {name} value {value}' for name, value in (
        ('Threads', '1'), ('Hash', '16'), *pc20, ('HistoryAgeKeep', '896'),
    )]


def run_case(args, games, label, multiplier, search, oracle=None):
    output = args.output / f'{label}.jsonl'
    metadata = output.with_suffix('.meta')
    if output.exists() or metadata.exists():
        raise FileExistsError(f'refusing to overwrite replay output {output}')
    expected = ordered_rows(oracle) if oracle else []
    if oracle and len(expected) != ROW_COUNT:
        raise ValueError(f'{oracle}: expected {ROW_COUNT} source rows')
    meta = {
        'command': sys.argv, 'start_utc': utc_now(), 'exe': str(args.engine), 'exe_sha256': HC_SHA,
        'games': str(args.games), 'games_sha256': sha256(args.games), 'game_count': len(games),
        'settings_sent': settings(multiplier), 'search': search, 'ucinewgame_per_game': True,
        'external_net_file': None, 'oracle': str(oracle) if oracle else None,
        'oracle_sha256': sha256(oracle) if oracle else None,
        'rows': 0, 'hp27_lines': 0, 'last_info_nodes': 0, 'hp27_nodes': 0, 'hp27_count': 0,
        'matching_oracle': 0, 'matching_info_hp27_nodes': 0, 'matching_final_hp27_nodes': 0,
        'hp27_nodes_at_budget': 0, 'status': 'incomplete',
    }
    with output.open('x', encoding='utf-8') as rows:
        try:
            with Engine(args.engine, 15) as engine:
                engine.send('uci')
                uci = engine.until('uciok')
                meta['id_name'] = next(line for line in uci if line.startswith('id name '))
                for name in ('HistoryAgeKeep', 'HistoryPruneMultiplier'):
                    meta[f'uci_option_{name}'] = next(line for line in uci if line.startswith(f'option name {name} '))
                for option in meta['settings_sent']:
                    engine.send(option)
                engine.send('isready')
                engine.until('readyok')
                for game in games:
                    engine.send('ucinewgame')
                    engine.send('isready')
                    engine.until('readyok')
                    for ply in range(len(game.moves)):
                        index = meta['rows'] + 1
                        position = f'position fen {game.fen}'
                        if ply:
                            position += ' moves ' + ' '.join(game.moves[:ply])
                        engine.send(position)
                        engine.send(search)
                        lines = engine.until('bestmove')
                        row = parse_row(index, game.fen, lines, require_counter=True)
                        hp_lines = [line for line in lines if line.startswith('info string HP27 ')]
                        if len(hp_lines) != 1 or not (hp := HP_INFO.fullmatch(hp_lines[0])):
                            raise ValueError(f'row {index}: expected exactly one well-formed HP27 line, saw {hp_lines!r}')
                        count, hp_nodes = map(int, hp.groups())
                        nodes, move = row['nodes'], row['bestmove']
                        raw = {
                            'index': index, 'game': game.index, 'ply': ply, 'position': position,
                            'info': row['info'], 'nodes': nodes, 'bestmove_line': lines[-1], 'bestmove': move,
                            'hp27_line': hp_lines[0], 'hp27_count': count, 'hp27_nodes': hp_nodes,
                            'final_nodes_info': row['final_nodes_info'], 'final_nodes': row['final_nodes'],
                        }
                        rows.write(json.dumps(raw, separators=(',', ':')) + '\n')
                        if oracle:
                            target = expected[index - 1]
                            if key(target) != (index, game.index, ply):
                                raise ValueError(f'{oracle}: wrong row order at {index}')
                            meta['matching_oracle'] += (nodes, move, count, hp_nodes) == (
                                target['nodes'], target['bestmove'], target['hp27'], target['hp27_nodes'],
                            )
                        meta['rows'] = index
                        meta['hp27_lines'] += 1
                        meta['last_info_nodes'] += nodes
                        meta['hp27_nodes'] += hp_nodes
                        meta['hp27_count'] += count
                        meta['matching_final_hp27_nodes'] += row['final_nodes'] == hp_nodes
                        meta['matching_info_hp27_nodes'] += nodes == hp_nodes
                        meta['hp27_nodes_at_budget'] += hp_nodes == 20000
            if meta['rows'] != ROW_COUNT or meta['hp27_lines'] != ROW_COUNT or meta['hp27_nodes'] <= 0:
                raise ValueError(f'{label}: expected {ROW_COUNT} usable HP27 observations')
            meta['status'] = 'complete'
        except Exception as error:
            meta['error'] = f'{type(error).__name__}: {error}'
            raise
        finally:
            rows.flush()
            meta['output_sha256'] = sha256(output)
            meta['end_utc'] = utc_now()
            with metadata.open('x', encoding='utf-8') as receipt:
                json.dump(meta, receipt, indent=2)
                receipt.write('\n')
    return meta


def rate(count, nodes):
    return Fraction(1000 * count, nodes)


def replay_rate(meta):
    return rate(meta['hp27_count'], meta['hp27_nodes'])


def pass_known(meta, case):
    label, search, last_nodes, hp_count, hp_nodes = case
    return (meta['status'], meta['matching_oracle'], meta['last_info_nodes'], meta['hp27_count'], meta['hp27_nodes']) == (
        'complete', ROW_COUNT, last_nodes, hp_count, hp_nodes,
    ) and (search != HARD or meta['hp27_nodes_at_budget'] == ROW_COUNT)


def known_answers(args, games):
    print('## Step 2. HC known-answer replays', flush=True)
    print('\nHC with PC20, Threads 1, Hash 16 and HistoryAgeKeep 896 replayed the first 20 Job 3 games with '
          'one `ucinewgame` and `isready` per game. HP27 and last-depth equality is descriptive.\n', flush=True)
    print('| Replay | Count and move fields matching Kimi | HP27 lines | Last depth nodes | HP27 prunes | '
          'HP27 whole-search nodes | HP27 nodes equal last depth | Gate |', flush=True)
    print('|---|---:|---:|---:|---:|---:|---:|---|', flush=True)
    for case in KNOWN:
        label, search, _, _, _ = case
        meta = run_case(args, games, label, 2220, search, args.references / f'{label}.jsonl')
        passed = pass_known(meta, case)
        print(f'| `{search}` | {meta["matching_oracle"]:,}/{ROW_COUNT:,} | {meta["hp27_lines"]:,} | '
              f'{meta["last_info_nodes"]:,} | {meta["hp27_count"]:,} | {meta["hp27_nodes"]:,} | '
              f'{meta["matching_info_hp27_nodes"]:,}/{ROW_COUNT:,} | {"PASS" if passed else "FAIL"} |', flush=True)
        if not passed:
            return 2
    print('\nThe hard replay reported exactly 20,000 HP27 nodes on all 1,200 rows.')
    return 0


def checked_baseline(args):
    jsonl = args.output / 'keep896_soft.jsonl'
    meta = json.loads(jsonl.with_suffix('.meta').read_text())
    if not (pass_known(meta, KNOWN[0]) and meta['exe_sha256'] == HC_SHA and meta['search'] == SOFT
            and meta['settings_sent'] == settings(2220) and meta['games_sha256'] == sha256(args.games)
            and meta['oracle_sha256'] == sha256(args.references / jsonl.name) and meta['output_sha256'] == sha256(jsonl)):
        raise ValueError('Step 2 soft receipt did not match the pinned m=2220 sweep case')
    return meta


def threshold(args, games):
    baseline = checked_baseline(args)
    r0 = rate(*BASELINE)
    archive = args.references / 'ka2_hard_dfl.jsonl'
    hard_archive = ordered_rows(archive)
    hard_pair = (sum(row['hp27'] for row in hard_archive), sum(row['hp27_nodes'] for row in hard_archive))
    if len(hard_archive) != ROW_COUNT or hard_pair != HARD_BASELINE:
        raise ValueError(f'{archive}: hard baseline does not match the known HP27 totals')
    sweep = {2220: baseline}
    print('## Step 3. Restore the soft whole-search prune rate\n', flush=True)
    print(f'The corrected baseline `r0` is 11,633 / 4,561,961 × 1,000 = {float(r0):.6f}, from the Job 29 '
          'HC1024 soft replay. The denominator is the HP27 whole-search node count.\n', flush=True)
    print('HC used PC20, Threads 1, Hash 16, HistoryAgeKeep 896 and `go softnodes 2000`. The m=2220 row reuses '
          'Step 2 after verifying the binary, settings, search, fixture and raw SHA-256.\n', flush=True)
    print('| Multiplier m | HP27 lines | HP27 prunes | HP27 whole-search nodes | Rate per 1,000 | Absolute difference from r0 |', flush=True)
    print('|---:|---:|---:|---:|---:|---:|', flush=True)
    for cap in CAPS:
        if cap != 2220:
            sweep[cap] = run_case(args, games, f'm{cap}_soft', cap, SOFT)
        print_sweep_row(cap, sweep[cap], r0)
    selected = min(sweep, key=lambda cap: abs(replay_rate(sweep[cap]) - r0))
    extended = selected == 250 and replay_rate(sweep[250]) < Fraction(3, 4) * r0
    if extended:
        for cap in EXTENSION_CAPS:
            sweep[cap] = run_case(args, games, f'm{cap}_soft', cap, SOFT)
            print_sweep_row(cap, sweep[cap], r0)
        selected = min(sweep, key=lambda cap: abs(replay_rate(sweep[cap]) - r0))
    print(f'\n**m* = {selected}.** Exact fraction comparison chose the closest rate. '
          f'The conditional 150 and 80 extension {"ran" if extended else "did not trigger"}.\n', flush=True)
    hard = run_case(args, games, f'm{selected}_hard', selected, HARD)
    if hard['hp27_nodes_at_budget'] != ROW_COUNT:
        raise ValueError('hard replay HP27 node count deviated from the 20,000-node budget')
    print(f'At `go nodes 20000`, HC keep 896 and m={selected} had {hard["hp27_count"]:,} HP27 prunes over '
          f'{hard["hp27_nodes"]:,} HP27 whole-search nodes in {hard["hp27_lines"]:,} lines, '
          f'{float(replay_rate(hard)):.6f} prunes per 1,000 nodes. Kimi5\'s archived keep 1024 hard rate '
          f'was {float(rate(*HARD_BASELINE)):.6f} from 313,423 HP27 prunes over 24,000,000 HP27 nodes. '
          f'Archived `ka2_hard_dfl.jsonl` SHA-256 `{sha256(archive)}`.')
    output = args.output.parent.parent / 'mstar.txt'
    with output.open('x', encoding='utf-8') as receipt:
        receipt.write(f'{selected}\n')
    return 0


def print_sweep_row(cap, meta, baseline_rate):
    observed = replay_rate(meta)
    print(f'| {cap} | {meta["hp27_lines"]:,} | {meta["hp27_count"]:,} | {meta["hp27_nodes"]:,} | '
          f'{float(observed):.6f} | {float(abs(observed - baseline_rate)):.6f} |')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step', choices=('known', 'sweep'))
    parser.add_argument('engine', type=Path)
    parser.add_argument('games', type=Path)
    parser.add_argument('references', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.engine = args.engine.resolve(strict=True)
    args.games = args.games.resolve(strict=True)
    if sha256(args.engine) != HC_SHA:
        raise ValueError('executable did not match the pinned HC SHA-256')
    games = read_games(args.games)[:20]
    if len(games) != 20 or any(len(game.moves) != 60 for game in games):
        raise ValueError('expected the first 20 Job 3 games to have 60 plies each')
    args.output.mkdir(parents=True, exist_ok=True)
    return known_answers(args, games) if args.step == 'known' else threshold(args, games)


if __name__ == '__main__':
    raise SystemExit(main())
