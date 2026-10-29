#!/usr/bin/env python3
"""Build the A2 test driver against a verified, already-built A1 Release core.
IDEA_SOURCE: Forge A1 provenance requirements and standard compiler/linker usage.
Does not rebuild or modify the engine. A new output directory is required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--core-build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, build, output = args.repo.resolve(), args.core_build.resolve(), args.out.resolve()
    here = Path(__file__).resolve().parent
    manifest_path = here / 'engine_source_sha256.json'
    manifest = json.loads(manifest_path.read_text())
    cache = {}
    for line in (build / 'CMakeCache.txt').read_text().splitlines():
        if '=' in line and ':' in line.split('=', 1)[0] and not line.startswith(('#', '//')):
            key, value = line.split('=', 1)
            cache[key.split(':', 1)[0]] = value
    if cache.get('CMAKE_BUILD_TYPE') != 'Release':
        raise RuntimeError('this driver build requires the qualified Release archive')
    source = Path(cache['CMAKE_HOME_DIRECTORY']).resolve()
    mismatches = []
    for root in (repo, source):
        for name, expected in manifest['files'].items():
            file = root / name
            if not file.is_file() or sha(file) != expected:
                mismatches.append(str(file))
    if mismatches:
        raise RuntimeError('source/header mismatch against frozen engine source: ' + ', '.join(mismatches))
    flags_path = build / 'CMakeFiles/forge_core.dir/flags.make'
    flag_lines = {}
    for line in flags_path.read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_FLAGS =')):
            key, value = line.split('=', 1)
            flag_lines[key.strip()] = value.strip()
    if flag_lines.get('CXX_DEFINES'):
        raise RuntimeError('unexpected core compile definitions; independently review ABI before using this helper')
    flags = shlex.split(flag_lines['CXX_FLAGS'])
    for flag in ('-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', '-march=x86-64-v3', '-mtune=znver5', '-O3', '-DNDEBUG'):
        if flag not in flags:
            raise RuntimeError('missing qualified compile flag: ' + flag)
    for key in ('FORGE_NNUE_O2', 'FORGE_NNUE_INT16', 'FORGE_NNUE_LAZY_ACC', 'FORGE_PROF', 'FORGE_SPEEDSTACK', 'FORGE_S13_TT_CHILD_PREFETCH', 'FORGE_ENABLE_SANITIZERS'):
        if cache.get(key) != 'OFF':
            raise RuntimeError('unexpected core option: ' + key)
    core = build / 'libforge_core.a'
    if not core.is_file():
        raise RuntimeError('qualified core archive is missing')
    latest_input = max([flags_path.stat().st_mtime_ns] + [(source / name).stat().st_mtime_ns for name in manifest['files']])
    if core.stat().st_mtime_ns < latest_input:
        raise RuntimeError('archive predates a frozen source/build input; rebuild/verify A1 before linking')
    output.mkdir(exist_ok=False)
    driver = here / 'a2_tt_seed_repro.cpp'
    binary = output / 'a2_tt_seed_repro'
    command = [cache['CMAKE_CXX_COMPILER'], *flags, '-I' + str(repo / 'include'), str(driver), str(core), '-pthread', '-o', str(binary)]
    receipt = {'engine_source': manifest['engine_source'], 'source_roots_checked': [str(repo), str(source)],
               'manifest_sha256': sha(manifest_path), 'driver_sha256': sha(driver), 'core_sha256': sha(core),
               'flags_sha256': sha(flags_path), 'command': command,
               'limit': 'matching sources/flags and input timestamps checked; archive provenance also relies on the preserved A1 build evidence'}
    (output / 'build_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(shlex.join(command), flush=True)
    with (output / 'build.log').open('xb') as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    receipt['exit_code'] = completed.returncode
    if completed.returncode == 0:
        receipt['binary_sha256'] = sha(binary)
    (output / 'build_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('compile_exit=' + str(completed.returncode), flush=True)
    return completed.returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, KeyError, ValueError) as error:
        print('BUILD_ERROR ' + str(error), file=sys.stderr)
        sys.exit(2)
