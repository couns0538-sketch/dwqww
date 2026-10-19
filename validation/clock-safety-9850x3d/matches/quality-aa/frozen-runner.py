#!/usr/bin/env python3
"""Preregistered fixed-node search-quality test, never an equal-clock strength test."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
PIN = '60d7a7a26c6b0582a15c112fb29a1829bef2adb3'
ZIP_SHA = '98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d'
CANDIDATE_SOURCE = 'fab979c9cc1c08bd1e89f1d0dabcfe300432a903'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def fen(line):
    return ' '.join(line.split()[:4])


def cgroup():
    return {name: (Path('/sys/fs/cgroup') / name).read_text()
            for name in ('cpu.max', 'cpu.stat', 'cpu.pressure', 'cpuset.cpus.effective')
            if (Path('/sys/fs/cgroup') / name).exists()}


def console_text(out):
    path = out / 'console.txt'
    return re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(errors='replace')) if path.exists() else ''


def progress(out, started):
    console = console_text(out)
    pgn = out / 'games.pgn'
    return {'elapsed_seconds': time.monotonic() - started,
            'finished_game_messages': len(re.findall(r'^Finished game ', console, re.M)),
            'latest_llr_lines': [line for line in console.splitlines() if 'LLR:' in line][-2:],
            'pgn_bytes': pgn.stat().st_size if pgn.exists() else 0,
            'cgroup_current': cgroup()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default='/workspace/.cloud-setup/forge-original-6.4-build/forge')
    parser.add_argument('--candidate', type=Path, default='/workspace/.cloud-setup/forge-clock-build/forge')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default='/workspace/dwqww')
    parser.add_argument('--aa-only', action='store_true', help='four pairs / eight games, baseline versus itself, no SPRT')
    args = parser.parse_args()
    repo, out = args.repo.resolve(strict=True), args.out.resolve()
    runner = Path('/workspace/.cloud-setup/fastchess/fastchess').resolve(strict=True)
    baseline = args.baseline.resolve(strict=True)
    candidate = baseline if args.aa_only else args.candidate.resolve(strict=True)
    inputs = {'baseline': baseline, 'candidate': candidate, 'fastchess': runner,
              'corpus': repo / 'tools/openings/forge-10000.epd',
              'original_zip': repo / 'chess-engine-forge-6.4.0.zip',
              'pgn_checker': repo / 'tools/match/pgn_stats.py',
              'protocol_runner': Path(__file__).resolve()}
    if sha(inputs['original_zip']) != ZIP_SHA:
        parser.error('original ZIP checksum mismatch')
    for name in ('baseline', 'candidate', 'fastchess'):
        if inputs[name].read_bytes()[:4] != b'\x7fELF':
            parser.error(f'{name} must be a native ELF executable')
    runner_commit = subprocess.check_output(['git', '-C', str(runner.parent), 'rev-parse', 'HEAD'], text=True).strip()
    runner_version = subprocess.check_output([str(runner), '-version'], text=True).strip()
    if runner_commit != PIN or PIN[:7] not in runner_version:
        parser.error('Fastchess source/version does not match preregistered pin')
    files = subprocess.check_output(['rg', '--files', '--hidden', '--no-ignore',
                                    '-g', '*.epd', '-g', '!**/.git/**', '/workspace'], text=True)
    excluded, exclusions = set(), {}
    for item in files.splitlines():
        path = Path(item)
        if path == inputs['corpus']:
            continue
        if path.name == 'selected.epd' or 'aa' in path.stem.lower() or any(
                part.startswith('aa') for part in path.parts) or 'clock-audit' in path.parts:
            excluded.update(fen(line) for line in path.read_text().splitlines() if line.strip())
            exclusions[str(path)] = sha(path)
    corpus = [fen(line) for line in inputs['corpus'].read_text().splitlines() if line.strip()]
    if len(corpus) != len(set(corpus)):
        parser.error('corpus has duplicate positions')
    pairs, seed = (4 if args.aa_only else 500), 20261019
    # Native SPRT stops in-flight games without finishing their opening pairs.
    # Serial SPRT avoids retaining an orphan first game from another pair.
    concurrency = 2 if args.aa_only else 1
    selected = sorted(set(corpus) - excluded,
                      key=lambda value: hashlib.sha256(f'{seed}\n{value}'.encode()).digest())[:pairs]
    if len(selected) != pairs:
        parser.error('not enough fresh unique openings')
    out.mkdir(parents=True, exist_ok=False)
    inputs['selected'] = out / 'selected.epd'
    inputs['selected'].write_text('\n'.join(selected) + '\n')
    command = [str(runner), '-config', 'outname=state.json',
               '-engine', f'cmd={candidate}', 'name=Candidate', 'option.OwnBook=false',
               '-engine', f'cmd={baseline}', 'name=Baseline', 'option.OwnBook=false',
               '-each', 'proto=uci', 'tc=inf', 'nodes=10000', 'option.Threads=1',
               'option.Hash=32', 'restart=on', '-openings', f'file={inputs["selected"]}',
               'format=epd', 'order=sequential', '-rounds', str(pairs), '-games', '2',
               '-concurrency', str(concurrency), '-srand', str(seed), '-report', 'penta=true',
               '-ratinginterval', '2', '-autosaveinterval', '2',
               '-pgnout', 'file=games.pgn', 'append=false', 'notation=uci', 'nodes=true',
               '-log', 'file=fastchess.log', 'level=trace' if args.aa_only else 'level=warn', 'engine=true',
               'realtime=false', 'append=false', '-strict']
    if not args.aa_only:
        command += ['-sprt', 'elo0=0', 'elo1=20', 'alpha=0.05', 'beta=0.05', 'model=logistic']
    hashes = {key: {'path': str(path), 'sha256': sha(path)} for key, path in inputs.items()}
    protocol = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'kind': 'fixed-node A/A calibration' if args.aa_only else 'fixed-node search-quality SPRT',
                'scope': '10,000-node search quality only; no equal-clock, Ryzen, Windows or Stockfish claim',
                'source_identity_declared': {'baseline_zip_sha256': ZIP_SHA, 'candidate_commit': None if args.aa_only else CANDIDATE_SOURCE,
                                            'limitation': 'Source-to-binary build provenance must also be retained by caller'},
                'nodes_per_move': 10000, 'tc': 'inf', 'threads': 1, 'hash_mib': 32,
                'ownbook': False, 'restart': True, 'concurrency': concurrency, 'max_pairs': pairs,
                'concurrency_reason': 'A/A finishes fixed schedule; serial SPRT prevents native boundary stop orphaning another opening pair',
                'sprt': None if args.aa_only else {'elo0': 0, 'elo1': 20, 'alpha': .05, 'beta': .05,
                                                   'model': 'logistic', 'bounds': [-math.log(19), math.log(19)]},
                'seed': seed, 'platform': platform.platform(), 'python': platform.python_version(),
                'affinity_inherited': sorted(os.sched_getaffinity(0)), 'cgroup_before': cgroup(),
                'fastchess_commit': runner_commit, 'fastchess_version': runner_version,
                'inputs': hashes, 'excluded_files': exclusions, 'selected_fens': selected,
                'command': command, 'pooling': 'No prior failed attempts or A/A outcomes are pooled',
                'prerequisite': 'A/A passed before SPRT; caller stopped owned builds/benchmarks/Wine',
                'acceptance': 'Complete normal unique color-swapped pairs; independent native-penta agreement; immutable inputs; explicit native SPRT acceptance with finite likelihood or cap inconclusive'}
    write(out / 'protocol.json', protocol)
    write(out / 'command.json', command)
    write(out / 'input-hashes.json', hashes)
    result = {'status': 'running', 'quality_gain_established': False, 'equal_clock_gain_established': False}
    started, process = time.monotonic(), None
    write(out / 'result.json', result)
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'received signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with (out / 'console.txt').open('x') as log:
            process = subprocess.Popen(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
            result['pid'] = process.pid
            while True:
                result['progress'] = progress(out, started)
                write(out / 'result.json', result)
                try:
                    result['exit_code'] = process.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    pass
        if result['exit_code']:
            raise RuntimeError(f'Fastchess exited {result["exit_code"]}')
        spec = importlib.util.spec_from_file_location('quality_pgn_stats', inputs['pgn_checker'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = (out / 'games.pgn').read_text()
        stats = module.summarize(text, require_identical_pairs=args.aa_only)
        if not 1 <= stats['pairs'] <= pairs:
            raise RuntimeError('invalid complete pair count')
        played = {fen(tags['FEN']) for tags, _ in module.games(text)}
        if not played <= set(selected):
            raise RuntimeError('unexpected opening')
        console = console_text(out)
        penta = re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]', console)
        if not penta or [int(value.strip()) for value in penta[-1].split(',')] != stats['pentanomial_0_half_1_1half_2']:
            raise RuntimeError('missing/disagreeing native pentanomial counts')
        for key, path in inputs.items():
            if sha(path) != hashes[key]['sha256']:
                raise RuntimeError(f'input changed: {key}')
        write(out / 'stats.json', stats)
        result['statistics'] = stats
        if args.aa_only:
            if stats['pairs'] != pairs:
                raise RuntimeError('A/A requires exactly four complete pairs')
            result.update(status='aa_passed', sprt_decision='not_applicable')
        else:
            accepted = re.findall(r'SPRT[^\n]*completed - (H[01]) was accepted', console)
            finite_llr = re.findall(r'LLR:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)', console)
            if accepted:
                if not finite_llr or not math.isfinite(float(finite_llr[-1])):
                    raise RuntimeError('native acceptance missing finite likelihood')
                decision = accepted[-1] + '_accepted'
                result.update(status='completed', sprt_decision=decision,
                              quality_gain_established=decision == 'H1_accepted')
            elif stats['pairs'] == pairs:
                result.update(status='completed', sprt_decision='inconclusive_at_pair_cap')
            else:
                raise RuntimeError('stopped before cap without native acceptance')
    except (Exception, KeyboardInterrupt) as error:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        result.update(status='failed_or_interrupted', error=str(error), quality_gain_established=False)
    finally:
        result['progress'] = progress(out, started)
        result['final_input_hashes'] = {key: sha(path) if path.exists() else None for key, path in inputs.items()}
        result['outputs_sha256'] = {path.name: sha(path) for path in out.iterdir()
                                   if path.is_file() and path.name != 'result.json'}
        write(out / 'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] in ('completed', 'aa_passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
