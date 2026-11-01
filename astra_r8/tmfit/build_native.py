#!/usr/bin/env python3
"""Reproduce a plain validation binary, not the crew LTO+PGO gate. UNPROVEN."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from run_tmfit import resource_guard


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--compiler', default='C:/msys64/ucrt64/bin/g++.exe')
    p.add_argument('--log', action='store_true')
    p.add_argument('--expose', action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    scratch = root.parent / 'astra8-scratch'
    out = args.out.resolve()
    if not out.is_relative_to(scratch.resolve()):
        p.error('output must be under authorized astra8-scratch')
    resource_guard(scratch)
    out.mkdir(parents=True, exist_ok=False)
    units = ['bitboard', 'board', 'book', 'datagen', 'eval', 'eval_params', 'nnue', 'search', 'uci']
    command = [args.compiler, '-std=c++20', '-O3', '-march=x86-64-v3', '-ffp-contract=off',
               '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-static', '-Iinclude']
    if args.log:
        command.append('-DFORGE_TM_LOG=1')
    if args.expose:
        command.append('-DFORGE_EXPOSE_TUNABLES=1')
    command += [f'src/{unit}.cpp' for unit in units] + ['-o', str(out/'forge.exe')]
    flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    env = dict(os.environ)
    (out/'tmp').mkdir()
    env['TMP'] = env['TEMP'] = env['TMPDIR'] = str(out/'tmp')
    env['PATH'] = str(Path(args.compiler).parent) + os.pathsep + env.get('PATH', '')
    tracked = subprocess.check_output(['git', 'ls-files', 'src', 'include'], cwd=root, text=True).splitlines()
    hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in tracked}
    record = dict(status='UNPROVEN', command=command, source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), source_sha256=hashes,
        compiler_version=subprocess.check_output([args.compiler, '--version'], text=True).splitlines()[0])
    with (out/'build.log').open('x') as log:
        result = subprocess.run(command, cwd=root, env=env, creationflags=flags, stdout=log, stderr=log)
    record['exit_code'] = result.returncode
    if result.returncode == 0:
        record['binary_sha256'] = hashlib.sha256((out/'forge.exe').read_bytes()).hexdigest()
    (out/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'source_sha256'}))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
