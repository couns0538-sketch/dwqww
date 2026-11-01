#!/usr/bin/env python3
"""Frozen 200-game TM qualification in two disjoint 100-game partial shards.

Two workers each search sequentially at Threads=1: at most two active searches.
No tuning occurs here. All output paths are new and strength remains UNPROVEN.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import run_tmfit as runner


def aggregate(frozen, shards):
    """Fail closed on provenance/pairing errors, then apply the 200-game gate."""
    if len(shards) != 2 or {s['shard_id'] for s in shards} != {0, 1}:
        raise ValueError('Exactly two distinct completed shards are required')
    assignments = frozen['assignments']
    if len(assignments) != 2 or {a['shard_id'] for a in assignments} != {0, 1}:
        raise ValueError('Invalid frozen assignments')
    assigned = [fen for a in assignments for fen in a['openings']]
    if len(assigned) != 100 or len(set(assigned)) != 100 or any(len(a['openings']) != 50 for a in assignments):
        raise ValueError('Need 100 unique openings in two disjoint groups of 50')
    combined = []
    for shard in sorted(shards, key=lambda s: s['shard_id']):
        assignment = next(a for a in assignments if a['shard_id'] == shard['shard_id'])
        manifest = shard['manifest']
        command = manifest['command']
        for key in ('engine_sha256', 'referee_sha256', 'runner_sha256', 'governor_sha256', 'engine_threads', 'option_file_sha256'):
            if manifest.get(key) != frozen[key]:
                raise ValueError('Shard provenance differs: ' + key)
        if manifest['engine_threads'] != 1 or manifest.get('selfplay_design') != 'opposed_modes_colors_swapped':
            raise ValueError('Shard must use Threads=1 and opposed modes with swapped colors')
        if manifest.get('openings_sha256') != assignment['sha256']:
            raise ValueError('Shard opening bytes differ from frozen assignment')
        if command.get('command') != 'smoke-shard' or command.get('games') != 100 or command.get('same_mode'):
            raise ValueError('Unexpected shard command or game count')
        for key in ('seed','base_ms','inc_ms','max_plies'):
            if command.get(key) != frozen[key]:
                raise ValueError('Shard settings differ: ' + key)
        if sorted(command.get('option', [])) != sorted(frozen['options']):
            raise ValueError('Shard options differ from frozen mapping')
        partial = shard['summary']
        if partial.get('status') != 'PARTIAL' or partial.get('qualification_eligible') is not False:
            raise ValueError('A 100-game shard may claim only partial evidence')
        games = shard['games']
        if len(games) != 100:
            raise ValueError('A shard is missing games or complete opening pairs')
        for index, game in enumerate(games):
            if game.get('game') != index or game.get('pair_id') != index // 2:
                raise ValueError('Missing, reordered, or duplicate game/pair index')
            if game.get('opening') != assignment['openings'][index // 2]:
                raise ValueError('Duplicate opening or wrong opening assignment')
            if game.get('result') not in ('checkmate','stalemate','threefold','fifty_move',
                                           'insufficient','ply_cap','illegal','time_loss'):
                raise ValueError('Unknown or failed game outcome')
            players = game.get('players', [])
            if (game.get('mode') != 'paired' or len(players) != 2 or
                    [p.get('color') for p in players] != ['white','black'] or
                    [p.get('mode') for p in players] != [index % 2, 1-index % 2]):
                raise ValueError('Wrong mode/color assignment in opening pair')
            if any(not isinstance(p['moves'], int) or p['moves'] < 1 or
                   not math.isfinite(p['total_wall_ms']) or p['total_wall_ms'] < 0 for p in players):
                raise ValueError('Invalid per-player timing evidence')
            if (sum(p['moves'] for p in players) != game['moves'] or
                    not math.isclose(sum(p['total_wall_ms'] for p in players), game['total_wall_ms'],
                                     rel_tol=1e-9, abs_tol=1e-6)):
                raise ValueError('Game totals disagree with player timing evidence')
        combined.extend(games)
    result = runner.timing_summary(combined, 200, calibration=False)
    result.update(strength='UNPROVEN', games=len(combined), opening_pairs=100, shards=2,
                  illegal_moves=sum(g['result'] == 'illegal' for g in combined),
                  time_losses=sum(g['result'] == 'time_loss' for g in combined))
    result['pass_'] = result['pass_'] and all(s['summary'].get('pass_') is True for s in shards)
    return result


def write_new_json(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def copy_new(source, destination):
    before = runner.digest(source)
    with Path(source).open('rb') as src, Path(destination).open('xb') as dst:
        shutil.copyfileobj(src, dst)
    if runner.digest(source) != before or runner.digest(destination) != before:
        raise ValueError('Input changed while snapshotting: ' + str(source))
    if os.name != 'nt':
        Path(destination).chmod(Path(source).stat().st_mode)
    return before


def read_shard(path, shard_id):
    path = Path(path)
    seals = json.loads((path/'sha256.json').read_text(encoding='utf-8'))
    for name, expected in seals.items():
        target = (path/name).resolve()
        if not target.is_relative_to(path.resolve()) or runner.digest(target) != expected:
            raise ValueError('Changed or invalid shard artifact: ' + name)
    for required in ('manifest.json','summary.json','games.jsonl','runner_snapshot.py','moves.jsonl','transcript.log',
                     'resource_governor_snapshot.py','governor-receipt.json'):
        if required not in seals:
            raise ValueError('Missing sealed artifact: ' + required)
    manifest = json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    if runner.digest(path/'runner_snapshot.py') != manifest['runner_sha256']:
        raise ValueError('Runner snapshot hash mismatch')
    if runner.digest(path/'resource_governor_snapshot.py') != manifest['governor_sha256']:
        raise ValueError('Governor snapshot hash mismatch')
    governor_receipt=json.loads((path/'governor-receipt.json').read_text(encoding='utf-8'))
    if governor_receipt.get('errors',0) != 0:
        raise ValueError('Governor failed; partial evidence cannot qualify')
    return dict(shard_id=shard_id, manifest=manifest,
                summary=json.loads((path/'summary.json').read_text(encoding='utf-8')),
                games=[json.loads(line) for line in (path/'games.jsonl').read_text(encoding='utf-8').splitlines() if line])


def below_normal():
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), subprocess.BELOW_NORMAL_PRIORITY_CLASS):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        os.nice(10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--referee', type=Path, required=True)
    parser.add_argument('--openings', type=Path, required=True)
    parser.add_argument('--scratch-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=2026110110)
    parser.add_argument('--base-ms', type=int, default=8000)
    parser.add_argument('--inc-ms', type=int, default=80)
    parser.add_argument('--max-plies', type=int, default=400)
    parser.add_argument('--option', action='append', default=[])
    args = parser.parse_args()
    below_normal()
    args.out = args.out.resolve()
    args.scratch_root = args.scratch_root.resolve(strict=True)
    if not args.out.is_relative_to(args.scratch_root):
        parser.error('Output must be inside scratch root')
    if args.base_ms <= 0 or args.inc_ms < 0 or args.max_plies < 1:
        parser.error('Invalid time/ply limits')
    options = dict(item.split('=',1) for item in args.option)
    runner.validate_extra_options(options)
    if not {'TmFitA','TmFitB','TmFitLo','TmFitHi'} <= options.keys():
        parser.error('Freeze all four mapping settings explicitly: TmFitA/B/Lo/Hi')
    source_lines = [line for line in args.openings.read_text(encoding='utf-8-sig').splitlines()
                    if line.strip() and not line.startswith('#')]
    positions = runner.read_positions(args.openings, args.seed)
    if len(source_lines) != 100 or len(positions) != 100:
        parser.error('Frozen input must contain exactly 100 unique positions')
    runner.resource_guard(args.scratch_root)
    args.out.mkdir(parents=True, exist_ok=False)
    runner.resource_governor.attach(args.out)
    binary_dir = args.out/'bin'
    binary_dir.mkdir()
    engine = binary_dir/('forge'+args.exe.suffix)
    referee = binary_dir/('referee'+args.referee.suffix)
    runner_path = args.out/'run_tmfit.py'
    frozen = dict(strength='UNPROVEN', phase='frozen_qualification', planned_games=200,
                  planned_opening_pairs=100, active_search_workers=2, engine_threads=1,
                  seed=args.seed, base_ms=args.base_ms, inc_ms=args.inc_ms, max_plies=args.max_plies,
                  started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                  engine_sha256=copy_new(args.exe,engine), referee_sha256=copy_new(args.referee,referee),
                  runner_sha256=copy_new(Path(runner.__file__),runner_path),
                  governor_sha256=copy_new(Path(runner.resource_governor.__file__),args.out/'resource_governor.py'),
                  governor=runner.resource_governor.snapshot(),
                  coordinator_sha256=copy_new(Path(__file__),args.out/'run_parallel_smoke.py'),
                  opening_source_path=str(args.openings.resolve()),
                  opening_source_sha256=copy_new(args.openings,args.out/'opening_source.epd'),
                  option_file_sha256={}, assignments=[])
    source_manifest = args.openings.parent/'manifest.json'
    if source_manifest.is_file():
        frozen['opening_source_manifest_sha256'] = copy_new(source_manifest,args.out/'opening_source_manifest.json')
    for name in ('EvalFile','NNUEFile'):
        if name in options and Path(options[name]).is_file():
            snapshot = binary_dir/(name+Path(options[name]).suffix)
            frozen['option_file_sha256'][name] = copy_new(options[name],snapshot)
            options[name] = str(snapshot)
    frozen['options'] = [name+'='+value for name,value in sorted(options.items())]
    commands = []
    for shard_id in range(2):
        assigned = positions[shard_id*50:(shard_id+1)*50]
        opening_file = args.out/f'shard{shard_id}.epd'
        with opening_file.open('x',encoding='ascii',newline='\n') as stream:
            stream.write('\n'.join(assigned)+'\n')
        frozen['assignments'].append(dict(shard_id=shard_id, openings=assigned,
                                          file=opening_file.name, sha256=runner.digest(opening_file)))
        command = [sys.executable,str(runner_path),'smoke-shard','--exe',str(engine),'--referee',str(referee),
                   '--openings',str(opening_file),'--out',str(args.out/f'shard{shard_id}'),
                   '--scratch-root',str(args.scratch_root),'--seed',str(args.seed),'--games','100',
                   '--base-ms',str(args.base_ms),'--inc-ms',str(args.inc_ms),'--max-plies',str(args.max_plies)]
        for option in frozen['options']:
            command.extend(['--option',option])
        commands.append(command)
    frozen['commands'] = commands
    write_new_json(args.out/'frozen.json',frozen)
    frozen_hash = runner.digest(args.out/'frozen.json')
    runner.resource_guard(args.scratch_root)
    processes, logs = [], []
    try:
        flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        for shard_id, command in enumerate(commands):
            runner.load_governor(start=True)  # Each new shard obeys CR's stricter startup admission.
            log = (args.out/f'shard{shard_id}-driver.log').open('x',encoding='utf-8')
            logs.append(log)
            processes.append(subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=flags))
        # Each bounded child owns/cleans up its engine processes. Wait for both,
        # even if one fails, so the coordinator never abandons a running shard.
        statuses = [process.wait() for process in processes]
        write_new_json(args.out/'child-exits.json',statuses)
        if any(status != 0 for status in statuses):
            raise RuntimeError('Partial shard failed; original child evidence retained')
        if runner.digest(args.out/'frozen.json') != frozen_hash:
            raise ValueError('Frozen configuration changed during qualification')
        for path,expected in ((engine,frozen['engine_sha256']),(referee,frozen['referee_sha256']),
                              (runner_path,frozen['runner_sha256']),
                              (args.out/'resource_governor.py',frozen['governor_sha256']),
                              (args.out/'run_parallel_smoke.py',frozen['coordinator_sha256']),
                              (args.out/'opening_source.epd',frozen['opening_source_sha256'])):
            if runner.digest(path) != expected:
                raise ValueError('Frozen executable/driver changed during qualification')
        for name,expected in frozen['option_file_sha256'].items():
            if runner.digest(options[name]) != expected:
                raise ValueError('Frozen network changed during qualification')
        shards = [read_shard(args.out/f'shard{i}',i) for i in range(2)]
        summary = aggregate(frozen,shards)
        summary['frozen_sha256'] = frozen_hash
        write_new_json(args.out/'summary.json',summary)
        print(json.dumps(summary),flush=True)
        if not summary['pass_']:
            raise RuntimeError('Final 200-game timing qualification failed')
        return 0
    except BaseException as error:
        write_new_json(args.out/'failure.json',dict(type=type(error).__name__,message=str(error)))
        raise
    finally:
        for process in processes:
            if process.poll() is None:
                process.wait()
        for log in logs:
            log.close()
        runner.resource_governor.finish(args.out)
        write_new_json(args.out/'sha256.json',{str(p.relative_to(args.out)):runner.digest(p)
                       for p in args.out.rglob('*') if p.is_file() and p != args.out/'sha256.json'})


if __name__ == '__main__':
    raise SystemExit(main())
