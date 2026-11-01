#!/usr/bin/env python3
"""Build one plain validation target sequentially; crew LTO+PGO strength is UNPROVEN."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from run_tmfit import resource_guard
import run_tmfit
import resource_governor


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def harness_dependencies():
    return {'builder_snapshot.py': Path(__file__),
            'runner_snapshot.py': Path(run_tmfit.__file__),
            'resource_governor_snapshot.py': Path(resource_governor.__file__)}


def snapshot_harness(out, dependencies=None):
    receipt = {}
    for name, source in (harness_dependencies() if dependencies is None else dependencies).items():
        before = digest(source)
        with (out/name).open('xb') as stream:
            stream.write(source.read_bytes())
        if digest(out/name) != before or digest(source) != before:
            raise RuntimeError('Harness source changed while snapshotting: ' + str(source))
        receipt[name] = dict(source=str(source.resolve()), sha256=before)
    return receipt


def verify_harness(receipt):
    for row in receipt.values():
        if digest(row['source']) != row['sha256']:
            raise RuntimeError('Harness source changed during compilation: ' + row['source'])


def source_units(root, target, referee_source):
    root = Path(root)
    if target == 'engine':
        names = ['bitboard', 'board', 'book', 'eval', 'eval_params', 'nnue', 'search', 'uci']
        # The actual AL1 lock has no datagen unit; the fallback source does.
        if (root/'src/datagen.cpp').is_file():
            names.insert(3, 'datagen')
        units = [root/'src'/f'{name}.cpp' for name in names]
    elif target == 'referee':
        units = [Path(referee_source), root/'src/board.cpp', root/'src/bitboard.cpp']
    elif target == 'numeric':
        units = [root/'tests/tmfit_tests.cpp']
    else:
        raise ValueError('Unknown build target: ' + target)
    if any(not unit.is_file() for unit in units):
        raise ValueError('Missing required translation unit')
    return units


def source_identity(root, base_commit, patch):
    """Hash actual source bytes; an ungitted stage never inherits an ancestor HEAD."""
    root = Path(root).resolve(strict=True)
    has_own_git = (root/'.git').exists()
    if not has_own_git and (not base_commit or patch is None):
        raise ValueError('Ungitted stage requires --base-commit and --patch provenance')
    if base_commit and not re.fullmatch('[0-9a-fA-F]{40}', base_commit):
        raise ValueError('Declared baseline must be a full 40-character commit hash')
    paths = [path for name in ('src', 'include', 'tests') for path in (root/name).rglob('*') if path.is_file()]
    if (root/'CMakeLists.txt').is_file():
        paths.append(root/'CMakeLists.txt')
    if any(not path.resolve().is_relative_to(root) for path in paths):
        raise ValueError('Source symlink escapes declared source root')
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in sorted(paths)}
    if not hashes:
        raise ValueError('Empty source tree')
    head, dirty = None, None
    if has_own_git:
        flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, creationflags=flags).strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all', '--',
                                         'src', 'include', 'tests', 'CMakeLists.txt'],
                                        cwd=root, text=True, creationflags=flags).splitlines()
    return dict(source_root=str(root), source_identity_kind='git_root' if has_own_git else 'ungitted_stage',
                source_git_head=head, source_commit=head if has_own_git and not dirty else None,
                source_dirty_paths=dirty, base_commit_declared=base_commit,
                patch_path=str(Path(patch).resolve()) if patch else None,
                patch_sha256=digest(patch) if patch else None,
                provenance_note='Declared base/patch are provenance; actual source identity is the complete byte hash manifest',
                source_sha256=hashes,
                source_tree_sha256=hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


def below_normal():
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), subprocess.BELOW_NORMAL_PRIORITY_CLASS):
            raise ctypes.WinError(ctypes.get_last_error())


def build_commands(compiler, root, out, units, target, log=False, expose=False):
    options = ['-std=c++20', '-O3', '-march=x86-64-v3', '-ffp-contract=off', '-DNDEBUG',
               '-DFORGE_NNUE_HIDDEN=256', '-I'+str(root/'include'), '-I'+str(root/'src')]
    if log:
        options.append('-DFORGE_TM_LOG=1')
    if expose:
        options.append('-DFORGE_EXPOSE_TUNABLES=1')
    objects = [out/'objects'/f'{index:02d}-{unit.stem}.o' for index, unit in enumerate(units)]
    commands = [[compiler, *options, '-c', str(unit), '-o', str(obj)] for unit, obj in zip(units, objects)]
    filename = {'engine': 'forge.exe', 'referee': 'tmfit_referee.exe', 'numeric': 'tmfit_numeric_tests.exe'}[target]
    binary = out/filename
    commands.append([compiler, '-static', *map(str, objects), '-o', str(binary)])
    return commands, binary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--compiler', default='C:/msys64/ucrt64/bin/g++.exe')
    p.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--base-commit')
    p.add_argument('--patch', type=Path)
    p.add_argument('--source-manifest', type=Path, help='Optional port receipt; preserved as declared provenance')
    p.add_argument('--target', choices=('engine', 'referee', 'numeric'), default='engine')
    p.add_argument('--log', action='store_true')
    p.add_argument('--expose', action='store_true')
    args = p.parse_args()
    below_normal()
    workspace = Path(__file__).resolve().parents[2]
    scratch = workspace.parent/'astra8-scratch'
    root, out = args.source_root.resolve(strict=True), args.out.resolve()
    if not out.is_relative_to(scratch.resolve()):
        p.error('output must be under authorized astra8-scratch')
    identity = source_identity(root, args.base_commit, args.patch)
    units = source_units(root, args.target, Path(__file__).with_name('tmfit_referee.cpp'))
    extra_sources = {str(unit.resolve()): digest(unit) for unit in units if not unit.resolve().is_relative_to(root)}
    resource_guard(scratch)
    out.mkdir(parents=True, exist_ok=False)
    resource_governor.attach(out)
    record = dict(status='UNPROVEN', target=args.target, **identity, extra_source_sha256=extra_sources,
                  priority='BelowNormal' if os.name == 'nt' else 'inherited', compiler_workers=1,
                  run_target=False, governor=resource_governor.snapshot(), steps=[])
    result_code = 1
    try:
        write_new_json(out/'source-manifest.json', identity)
        record['harness_sources'] = snapshot_harness(out)
        for name, row in record['harness_sources'].items():
            record[name+'_sha256'] = row['sha256']
        if args.source_manifest:
            with (out/'declared-port-receipt.json').open('xb') as stream:
                stream.write(args.source_manifest.read_bytes())
            record['declared_port_receipt_sha256'] = digest(out/'declared-port-receipt.json')
        (out/'tmp').mkdir()
        (out/'objects').mkdir()
        env = dict(os.environ)
        env['TMP'] = env['TEMP'] = env['TMPDIR'] = str(out/'tmp')
        env['PATH'] = str(Path(args.compiler).parent) + os.pathsep + env.get('PATH', '')
        flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        commands, binary = build_commands(args.compiler, root, out, units, args.target, args.log, args.expose)
        record['commands'] = commands
        resource_governor.load_governor(start=True)
        version = subprocess.check_output([args.compiler, '--version'], cwd=root, env=env,
                                          text=True, creationflags=flags)
        with (out/'compiler-version.txt').open('x', encoding='utf-8') as stream:
            stream.write(version)
        record['compiler_version'] = version.splitlines()[0]
        with (out/'build.log').open('x', encoding='utf-8') as log:
            for index, command in enumerate(commands):
                resource_guard(scratch)
                log.write(json.dumps(dict(step=index, command=command))+'\n')
                log.flush()
                result = subprocess.run(command, cwd=root, env=env, creationflags=flags, stdout=log, stderr=log)
                record['steps'].append(dict(index=index, exit_code=result.returncode))
                if result.returncode:
                    result_code = result.returncode
                    break
            else:
                after = source_identity(root, args.base_commit, args.patch)
                if after != identity or any(digest(path) != value for path, value in extra_sources.items()):
                    raise RuntimeError('Source/provenance changed during compilation; binary is not qualified')
                verify_harness(record['harness_sources'])
                record['source_unchanged'] = True
                record['binary_sha256'] = digest(binary)
                record['binary_path'] = str(binary)
                result_code = 0
    except BaseException as error:
        record['failure'] = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        record['exit_code'] = result_code
        resource_governor.finish(out)
        record['governor'] = resource_governor.snapshot()
        write_new_json(out/'build.json', record)
        write_new_json(out/'sha256.json', {path.relative_to(out).as_posix(): digest(path)
                       for path in out.rglob('*') if path.is_file() and path != out/'sha256.json'})
    print(json.dumps({key: value for key, value in record.items() if key not in ('source_sha256', 'commands')}))
    return result_code


if __name__ == '__main__':
    sys.exit(main())
