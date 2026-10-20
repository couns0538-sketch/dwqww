#!/usr/bin/env python3
"""Original fixed 8-pair clock pilot; never an Elo/SPRT acceptance test."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fen(line):
    return ' '.join(line.split()[:4])


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def counters():
    result = {}
    for name in ('cpu.max', 'cpu.stat', 'cpu.pressure', 'cpuset.cpus.effective'):
        path = Path('/sys/fs/cgroup') / name
        result[name] = path.read_text() if path.exists() else None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--repo', default='/workspace/dwqww', type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve()
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'src', 'include', 'CMakeLists.txt'],
                   cwd=repo, check=True, stdout=subprocess.DEVNULL)
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    runner = Path('/workspace/.cloud-setup/fastchess/fastchess').resolve(strict=True)
    inputs = {'baseline': args.baseline.resolve(strict=True),
              'candidate': args.candidate.resolve(strict=True), 'fastchess': runner,
              'openings': repo / 'tools/openings/forge-10000.epd',
              'pgn_checker': repo / 'tools/match/pgn_stats.py',
              'protocol_runner': Path(__file__).resolve()}
    for name in ('baseline', 'candidate', 'fastchess'):
        if inputs[name].read_bytes()[:4] != b'\x7fELF':
            parser.error(f'{name} must be a native ELF executable, not a proxy')
    # Include prior selected files and separate A/A/audit fixtures, even ignored files.
    paths = subprocess.check_output(['rg', '--files', '--hidden', '--no-ignore',
                                    '-g', '*.epd', '-g', '!**/.git/**', '/workspace'], text=True)
    excluded, exclusion_files = set(), {}
    for item in paths.splitlines():
        path = Path(item)
        if path == inputs['openings']:
            continue
        if path.name == 'selected.epd' or 'aa' in path.stem.lower() or any(
                part.startswith('aa') for part in path.parts) or 'clock-audit' in path.parts:
            excluded.update(fen(line) for line in path.read_text().splitlines() if line.strip())
            exclusion_files[str(path)] = digest(path)
    positions = [fen(line) for line in inputs['openings'].read_text().splitlines() if line.strip()]
    if len(positions) != len(set(positions)):
        parser.error('opening corpus contains duplicate four-field FENs')
    seed = 20261019
    selected = sorted(set(positions) - excluded,
                      key=lambda item: hashlib.sha256(f'{seed}\n{item}'.encode()).digest())[:8]
    if len(selected) != 8:
        parser.error('fewer than eight unused unique openings remain')
    out.mkdir(parents=True, exist_ok=False)
    opening_path = out / 'selected.epd'
    opening_path.write_text('\n'.join(selected) + '\n')
    inputs['selected'] = opening_path
    command = [str(runner), '-config', 'outname=state.json',
               '-engine', f'cmd={inputs["candidate"]}', 'name=Candidate', 'option.OwnBook=false',
               '-engine', f'cmd={inputs["baseline"]}', 'name=Baseline', 'option.OwnBook=false',
               '-each', 'proto=uci', 'tc=10+0.1', 'option.Threads=1', 'option.Hash=32',
               'option.Move Overhead=100', 'restart=on',
               '-openings', f'file={opening_path}', 'format=epd', 'order=sequential',
               '-rounds', '8', '-games', '2', '-concurrency', '1', '-srand', str(seed),
               '-report', 'penta=true', '-ratinginterval', '2', '-autosaveinterval', '2',
               '-pgnout', 'file=games.pgn', 'append=false', 'notation=uci', 'nodes=true', 'timeleft=true',
               '-log', 'file=fastchess.log', 'level=trace', 'engine=true', 'realtime=false',
               'append=false', '-strict']
    hashes = {name: {'path': str(path), 'sha256': digest(path)} for name, path in inputs.items()}
    protocol = {'kind': 'fixed infrastructure pilot; no Elo or SPRT claim',
                'candidate_source_commit': source_commit,
                'source_precondition': 'src, include and CMakeLists.txt match the recorded commit',
                'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pairs': 8, 'games': 16, 'tc': '10+0.1', 'threads': 1, 'hash_mib': 32,
                'ownbook': False, 'overhead_ms': 100, 'concurrency': 1, 'seed': seed,
                'affinity_inherited': sorted(os.sched_getaffinity(0)),
                'platform': platform.platform(), 'python': platform.python_version(),
                'cgroup_before': counters(), 'inputs': hashes,
                'excluded_files': exclusion_files, 'excluded_unique_fens': len(excluded),
                'selected_fens': selected, 'command': command,
                'prerequisite': 'Caller stopped owned builds, benchmarks and Wine jobs; A/A completed',
                'acceptance': '16 normal games; eight unique swapped pairs; native pentanomial agreement; unchanged inputs'}
    write(out / 'protocol.json', protocol)
    write(out / 'command.json', command)
    write(out / 'input-hashes.json', hashes)
    result = {'status': 'running', 'valid_strength_evidence': False, 'elo_claim': None}
    write(out / 'result.json', result)
    started = time.monotonic()
    try:
        with (out / 'console.txt').open('x') as log:
            completed = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
        result['exit_code'] = completed.returncode
        if completed.returncode:
            raise RuntimeError(f'Fastchess exited {completed.returncode}; entire pilot failed')
        spec = importlib.util.spec_from_file_location('pilot_pgn_stats', inputs['pgn_checker'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stats = module.summarize((out / 'games.pgn').read_text())
        if stats['games'] != 16 or stats['pairs'] != 8 or stats['unique_openings'] != 8:
            raise RuntimeError('pilot must contain exactly 16 normal games / eight unique pairs')
        played = {fen(tags['FEN']) for tags, _ in module.games((out / 'games.pgn').read_text())}
        if played != set(selected):
            raise RuntimeError('played openings do not match frozen selection')
        console = re.sub(r'\x1b\[[0-9;]*m', '', (out / 'console.txt').read_text())
        penta = re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]', console)
        if not penta or [int(value.strip()) for value in penta[-1].split(',')] != stats['pentanomial_0_half_1_1half_2']:
            raise RuntimeError('missing/disagreeing native pentanomial counts')
        for name, path in inputs.items():
            if digest(path) != hashes[name]['sha256']:
                raise RuntimeError(f'input hash changed: {name}')
        write(out / 'stats.json', stats)
        result.update(status='passed_infrastructure_pilot', statistics=stats)
    except (Exception, KeyboardInterrupt) as error:
        result.update(status='failed_or_interrupted', error=str(error))
    finally:
        result.update(elapsed_seconds=time.monotonic() - started, cgroup_after=counters())
        write(out / 'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed_infrastructure_pilot' else 1


if __name__ == '__main__':
    raise SystemExit(main())
