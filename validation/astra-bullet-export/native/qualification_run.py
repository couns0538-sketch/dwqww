#!/usr/bin/env python3
"""Reproduce the unchanged pinned R10 native checks; retain every original result."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

SOURCE = Path('/tmp/forge-astra-r10-buildsrc')
BUILD = Path('/tmp/astra-r10-native')
OUT = Path(__file__).resolve().parent
PIN = '7f79c34901fdd118bc4bf904f4bcaec4006047c6'
EXPECTED = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
COMMANDS = []

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def run(name, args, stdin=None, timeout=900, cwd=BUILD):
    if (OUT / f'{name}.stdout.log').exists():
        raise RuntimeError(f'refusing to overwrite existing evidence: {name}')
    begin = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start = time.monotonic()
    if stdin is not None:
        (OUT / f'{name}.stdin.txt').write_text(stdin)
    with (OUT / f'{name}.stdout.log').open('w') as out, (OUT / f'{name}.stderr.log').open('w') as err:
        result = subprocess.run(args, input=stdin, text=True, stdout=out, stderr=err, timeout=timeout, cwd=cwd)
    COMMANDS.append({'name': name, 'argv': [str(x) for x in args], 'cwd': str(cwd),
                     'started_utc': begin, 'duration_seconds': time.monotonic() - start,
                     'returncode': result.returncode, 'stdin_file': f'{name}.stdin.txt' if stdin is not None else None})
    save('commands.json', COMMANDS)
    return result.returncode, (OUT / f'{name}.stdout.log').read_text()

head = subprocess.check_output(['git', '-C', SOURCE, 'rev-parse', 'HEAD'], text=True).strip()
status = subprocess.check_output(['git', '-C', SOURCE, 'status', '--porcelain'], text=True)
tracked_status = subprocess.check_output(['git', '-C', SOURCE, 'status', '--porcelain', '--untracked-files=no'], text=True)
assert head == PIN and not tracked_status, (head, tracked_status)
tracked = subprocess.check_output(['git', '-C', SOURCE, 'ls-files', 'src', 'include', 'CMakeLists.txt',
                                   'opus_r10/tools/halfka_tool.cpp'], text=True).splitlines()
manifest = {'source_commit': head, 'source_status_porcelain': status,
            'source_tracked_status_porcelain': tracked_status,
            'untracked_note': 'CTest generated Python __pycache__ files before this freeze; retained without deleting.',
            'affinity': sorted(os.sched_getaffinity(0)), 'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
            'cxx_version': subprocess.check_output(['/usr/bin/c++', '--version'], text=True),
            'tracked_source_sha256': {p: sha(SOURCE / p) for p in tracked},
            'files': {str(p): sha(p) for p in [BUILD / 'forge', BUILD / 'libforge_core.a',
                     SOURCE / 'opus_r10/nets/smoke_k32h3_l64.nnue', SOURCE / 'tests/halfka_smoke_expected.txt',
                     SOURCE / 'tests/legal_witness_fixtures.tsv', SOURCE / 'tools/openings/forge-10000.epd']},
            'limitations': ['Linux cloud qualification, not the target Windows PC',
                            'No GPU or live trainer qualification', 'No NPS or playing-strength claim']}
save('frozen_manifest.json', manifest)
for src, name in [(BUILD/'CMakeCache.txt','CMakeCache.txt'),
                  (BUILD/'CMakeFiles/forge_core.dir/flags.make','forge_core_flags.make'),
                  (BUILD/'CMakeFiles/forge.dir/link.txt','forge_link.txt')]:
    shutil.copyfile(src, OUT/name)
tool_cmd = ['/usr/bin/c++', '-std=c++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=znver5',
            '-ffp-contract=off', '-fno-fast-math', '-DFORGE_NNUE_HIDDEN=256', '-pthread', '-Wall', '-Wextra',
            '-I'+str(SOURCE/'include'), str(SOURCE/'opus_r10/tools/halfka_tool.cpp'),
            str(BUILD/'libforge_core.a'), '-o', str(BUILD/'halfka_tool')]
rc, _ = run('halfka_tool_build', tool_cmd)
assert rc == 0, rc
manifest['files'][str(BUILD/'halfka_tool')] = sha(BUILD/'halfka_tool')
save('frozen_manifest.json', manifest)
print('HALFKA_TOOL_READY', str(BUILD/'halfka_tool'), flush=True)
results = {'bench_off': [], 'perft': [], 'fma_instruction_count': {}}
for depth, expected in EXPECTED.items():
    rc, stdout = run(f'bench_off_d{depth}', [str(BUILD/'forge')],
                     f'uci\nsetoption name Threads value 1\nsetoption name OwnBook value false\n'
                     f'setoption name EvalFileHalfKA value <empty>\nisready\nbench {depth}\nquit\n')
    match = re.search(rf'info string bench depth {depth} nodes (\d+) ', stdout)
    nodes = int(match[1]) if match else None
    item = {'depth': depth, 'expected_nodes': expected, 'actual_nodes': nodes, 'returncode': rc,
            'pass': rc == 0 and nodes == expected and 'info string EvalFileHalfKA off' in stdout}
    results['bench_off'].append(item)
    save('results.json', results)
    print('BENCH_OFF', item, flush=True)
for name, position, expected in [('startpos', 'position startpos', 4865609),
    ('kiwipete', 'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 193690690)]:
    rc, stdout = run(f'perft_{name}_d5', [str(BUILD/'forge')], f'{position}\ngo perft 5\nquit\n')
    match = re.search(r'^nodes (\d+)$', stdout, re.MULTILINE)
    nodes = int(match[1]) if match else None
    item = {'position': name, 'depth': 5, 'expected_nodes': expected, 'actual_nodes': nodes,
            'returncode': rc, 'pass': rc == 0 and nodes == expected}
    results['perft'].append(item)
    save('results.json', results)
    print('PERFT', item, flush=True)
for name in ['forge', 'halfka_tool']:
    cmd = ['objdump', '-d', str(BUILD/name)]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    matches = [line for line in proc.stdout.splitlines() if re.search(r'\b(?:v?fmadd|v?fmsub|v?fnmadd|v?fnmsub)', line)]
    (OUT/f'{name}_fma_matches.txt').write_text('\n'.join(matches) + ('\n' if matches else ''))
    results['fma_instruction_count'][name] = {'argv': cmd, 'count': len(matches),
        'disassembly_sha256': hashlib.sha256(proc.stdout.encode()).hexdigest(), 'returncode': proc.returncode,
        'mnemonic_regex': r'\b(?:v?fmadd|v?fmsub|v?fnmadd|v?fnmsub)'}
    save('results.json', results)
    print('FMA', name, len(matches), flush=True)
results['source_status_after'] = subprocess.check_output(['git','-C', SOURCE,'status','--porcelain'],text=True)
results['source_unchanged_after'] = (subprocess.check_output(['git','-C', SOURCE,'status','--porcelain','--untracked-files=no'],text=True) == '')
results['source_hashes_match_after'] = all(sha(SOURCE/p) == h for p,h in manifest['tracked_source_sha256'].items())
results['frozen_hashes_match_after'] = all(sha(p) == h for p,h in manifest['files'].items())
results['pass'] = all(x['pass'] for x in results['bench_off'] + results['perft']) and all(
    x['count'] == 0 for x in results['fma_instruction_count'].values()) and results['source_unchanged_after'] and results['source_hashes_match_after'] and results['frozen_hashes_match_after']
save('results.json', results)
sys.exit(0 if results['pass'] else 1)
