#!/usr/bin/env python3
"""Build the offline probe with a fresh Release core and immutable build receipts.

Linux example (GCC must recognize the requested CPU names):
  python3 tools/data/build_probe.py --output /tmp/forge-data-build --cxx g++-14
Windows, from a PowerShell session with MSYS2 UCRT64 tools on PATH:
  py tools/data/build_probe.py --output C:/forge-data-build --cxx g++.exe --static

Windows execution is not implied by successful Linux qualification. This script
never modifies engine files and accepts only a NEW output directory. The source
and binary hashes in build_receipt.json identify the actual inputs and output.
IDEA_SOURCE: user Astra A1 data contract; repository's existing CMake core target.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_hashes(repo: Path) -> dict[str, str]:
    paths = [repo / 'CMakeLists.txt', repo / 'tools/data/forge_data_probe.cpp']
    for directory in ('src', 'include'):
        paths.extend(p for p in (repo / directory).rglob('*')
                     if p.is_file() and p.suffix in ('.cpp', '.h', '.hpp', '.inc', '.cmake'))
    if not (repo / 'include/forge/search.hpp').is_file():
        raise ValueError('repo must contain the Forge public search API')
    return {p.relative_to(repo).as_posix(): sha256(p) for p in sorted(set(paths))}


def clean_environment(environment: dict[str, str]) -> dict[str, str]:
    # CMake consults these on a first configure. No inherited optimization or
    # ABI macro is allowed to supersede the explicitly qualified recipe.
    removed = {'CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS',
               'CMAKE_TOOLCHAIN_FILE', 'CMAKE_GENERATOR', 'CMAKE_GENERATOR_PLATFORM',
               'CMAKE_GENERATOR_TOOLSET', 'CMAKE_PROJECT_TOP_LEVEL_INCLUDES'}
    return {key: value for key, value in environment.items() if key.upper() not in removed}


def count_fma(disassembly: str) -> int:
    # GNU objdump instruction lines only: a symbol or comment mentioning FMA
    # does not count as an instruction. Covers positive and negated add/sub.
    instruction = re.compile(r'^\s*[0-9a-fA-F]+:\s+(?:[0-9a-fA-F]{2}\s+)+([a-zA-Z][a-zA-Z0-9.]*)\b')
    return sum(bool(re.match(r'^v(?:fm(?:add|sub)|fnm(?:add|sub))', match.group(1)))
               for line in disassembly.splitlines()
               if (match := instruction.match(line)))


def executable(value: str, description: str) -> Path:
    found = shutil.which(value)
    if found is None:
        raise ValueError(f'{description} executable not found: {value}')
    return Path(found).resolve()


def write_json(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def run(command: list[str], output: Path, stem: str, receipt: dict,
        environment: dict[str, str]) -> str:
    entry = {'argv': command, 'cwd': str(output), 'stdout': stem + '.stdout',
             'stderr': stem + '.stderr'}
    receipt['commands'].append(entry)
    write_json(output / (stem + '.command.json'), entry)
    started = time.monotonic()
    with (output / (stem + '.stdout')).open('xb') as out, (output / (stem + '.stderr')).open('xb') as err:
        result = subprocess.run(command, cwd=output, env=environment, stdout=out,
                                stderr=err, check=False)
    entry['elapsed_seconds'] = time.monotonic() - started
    entry['returncode'] = result.returncode
    write_json(output / (stem + '.result.json'), entry)
    if result.returncode:
        raise RuntimeError(f'{stem} failed with exit {result.returncode}; see {stem}.stderr')
    return (output / (stem + '.stdout')).read_text(encoding='utf-8', errors='replace')


def build(args: argparse.Namespace, output: Path, receipt: dict) -> None:
    repo = args.repo.resolve()
    environment = clean_environment(dict(os.environ))
    receipt['source_sha256'] = source_hashes(repo)
    receipt['repo'] = str(repo)
    cxx = executable(args.cxx, 'compiler')
    cmake = executable(args.cmake, 'cmake')
    objdump = executable(args.objdump, 'objdump')
    receipt['tools'] = {name: {'path': str(path), 'sha256': sha256(path)}
                        for name, path in (('compiler', cxx), ('cmake', cmake), ('objdump', objdump))}
    for name, path in (('compiler', cxx), ('cmake', cmake), ('objdump', objdump)):
        receipt['tools'][name]['version'] = run([str(path), '--version'], output, name + '_version', receipt, environment)
    compiler_version = receipt['tools']['compiler']['version'].lower()
    if not any(word in compiler_version for word in ('gcc', 'g++', 'clang')):
        raise ValueError('use a GCC-compatible compiler (GCC or Clang, not MSVC cl)')
    git = shutil.which('git')
    if git:
        receipt['git_head'] = run([git, '-C', str(repo), 'rev-parse', 'HEAD'], output, 'git_head', receipt, environment).strip()
        receipt['git_status'] = run([git, '-C', str(repo), 'status', '--porcelain'], output, 'git_status', receipt, environment)
    flags = ['-march=' + args.march, '-mtune=' + args.mtune, '-fno-fast-math',
             '-ffp-contract=off', '-DFORGE_NNUE_HIDDEN=256']
    receipt['strict_fp_flags'] = flags
    cmake_text = (repo / 'CMakeLists.txt').read_text(encoding='utf-8')
    options = sorted(set(re.findall(r'^option\((FORGE_[A-Z0-9_]+)\s', cmake_text, re.MULTILINE)))
    receipt['forge_build_options'] = dict.fromkeys(options, 'OFF')
    core_dir = output / 'core'
    configure = [str(cmake), '-S', str(repo), '-B', str(core_dir), '-G', args.generator,
                 '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF',
                 '-DCMAKE_CXX_COMPILER=' + str(cxx), '-DCMAKE_CXX_FLAGS=' + ' '.join(flags),
                 '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                 '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF', '-DFORGE_NNUE_WEIGHTS_FILE=']
    configure.extend('-D' + name + '=OFF' for name in options)
    run(configure, output, 'configure', receipt, environment)
    run([str(cmake), '--build', str(core_dir), '--config', 'Release', '--target', 'forge_core',
         '--parallel', str(args.jobs)], output, 'build_core', receipt, environment)
    candidates = [p for p in core_dir.rglob('libforge_core.a') if p.is_file()]
    if len(candidates) != 1:
        raise RuntimeError(f'expected one GNU static forge_core archive, found {len(candidates)}')
    core = candidates[0]
    receipt['core_path'] = str(core)
    receipt['core_sha256'] = sha256(core)
    receipt['compile_commands_sha256'] = sha256(core_dir / 'compile_commands.json')
    receipt['cmake_cache_sha256'] = sha256(core_dir / 'CMakeCache.txt')
    probe = output / ('forge_data_probe.exe' if os.name == 'nt' else 'forge_data_probe')
    command = [str(cxx), '-O3', '-DNDEBUG', '-std=gnu++20', *flags,
               '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Wshadow',
               '-I' + str(repo / 'include'), str(repo / 'tools/data/forge_data_probe.cpp'),
               str(core), '-pthread']
    if args.static:
        command.append('-static')
    command.extend(['-o', str(probe)])
    run(command, output, 'link_probe', receipt, environment)
    receipt['probe_path'] = str(probe)
    receipt['probe_sha256'] = sha256(probe)
    disassembly = run([str(objdump), '-d', str(probe)], output, 'disassembly', receipt, environment)
    receipt['fma_instructions'] = count_fma(disassembly)
    if receipt['fma_instructions']:
        raise RuntimeError('FMA instructions found in executable')
    receipt['probe_version'] = json.loads(run([str(probe), '--version'], output, 'probe_version', receipt, environment))
    if receipt['probe_version'].get('protocol') != 'forge-data-probe-v1':
        raise RuntimeError('unexpected probe protocol')
    receipt['source_unchanged'] = source_hashes(repo) == receipt['source_sha256']
    if not receipt['source_unchanged']:
        raise RuntimeError('source changed during the build; output is not qualified')
    receipt['status'] = 'PASS'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True, help='new output directory; never reused')
    parser.add_argument('--cxx', default='g++', help='GNU-compatible C++ compiler, e.g. g++-14 or C:/msys64/ucrt64/bin/g++.exe')
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--objdump', default='objdump')
    parser.add_argument('--generator', default='MinGW Makefiles' if os.name == 'nt' else 'Unix Makefiles')
    parser.add_argument('--march', default='x86-64-v3')
    parser.add_argument('--mtune', default='znver5')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--static', action='store_true', help='link GNU runtime statically (useful for Windows distribution)')
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 64:
        parser.error('jobs must be between 1 and 64')
    if not all(re.fullmatch(r'[A-Za-z0-9_.+-]+', value) for value in (args.march, args.mtune)):
        parser.error('architecture names must be single GCC target names, without whitespace or flags')
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        parser.error('output directory already exists; choose a NEW directory')
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'FAIL', 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'commands': [], 'requested': {key: str(value) if isinstance(value, Path) else value
                                             for key, value in vars(args).items()},
               'platform': sys.platform, 'windows_runtime': 'UNVERIFIED' if os.name != 'nt' else 'build-only',
               'qualification': 'build, protocol version and FMA only; native tests are separate'}
    try:
        build(args, output, receipt)
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'
        print(receipt['error'], file=sys.stderr)
    except KeyboardInterrupt:
        receipt['error'] = 'KeyboardInterrupt: interrupted; outputs retained'
    finally:
        receipt['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_json(output / 'build_receipt.json', receipt)
        artifacts = {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}
        write_json(output / 'SHA256SUMS.json', artifacts)
    print(str(output / 'build_receipt.json'))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
