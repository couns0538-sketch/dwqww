#!/usr/bin/env python3
"""Pure source checks and GNU patch on NEW copies; no compiler/native process."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s12prep', HERE / 'forge_sol_S12_prepare_patch_20261026.py')
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)
PATCH = HERE / 'forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch'
EXPECTED_SHA = '66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d'


def erase_feature_blocks(text):
    """Targeted source erasure, NOT a C++ preprocessor or compiler check."""
    out = []
    skip = 0
    for line in text.splitlines():
        directive = line.strip()
        if not skip and directive == '#if FORGE_NNUE_LAZY_ACC':
            skip = 1
        elif skip:
            if directive.startswith(('#if ', '#ifdef ', '#ifndef ')):
                skip += 1
            elif directive == '#endif':
                skip -= 1
        else:
            out.append(line)
    assert skip == 0
    return '\n'.join(line for line in out if line.strip())


def main():
    result_path = HERE / 'forge_sol_S12_source_checks_20261026.json'
    if result_path.exists():
        raise FileExistsError('sealed source check already exists')
    assert hashlib.sha256(PATCH.read_bytes()).hexdigest() == EXPECTED_SHA
    before = {k: prep.inventory(v) for k, v in prep.BASES.items()}
    runs = []
    for key, base in prep.BASES.items():
        dest = HERE / ('applycheck_' + key)
        dest.mkdir()
        for name in prep.FILES:
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base / name, target)
        for mode in ['dry', 'apply']:
            command = ['patch', '--batch', '--forward', '--fuzz=0', '-p1']
            if mode == 'dry':
                command.append('--dry-run')
            command += ['-i', str(PATCH)]
            proc = subprocess.run(command, cwd=dest, capture_output=True, timeout=20)
            for stream in ['stdout', 'stderr']:
                (HERE / f'forge_sol_S12_apply_{key}_{mode}_{stream}_20261026.txt').write_bytes(getattr(proc, stream))
            runs.append({'base': key, 'mode': mode, 'command': command, 'cwd': str(dest), 'rc': proc.returncode,
                         'stdout_sha256': hashlib.sha256(proc.stdout).hexdigest(),
                         'stderr_sha256': hashlib.sha256(proc.stderr).hexdigest()})
            if proc.returncode != 0:
                raise RuntimeError(f'{key} {mode} failed; original evidence preserved')
        # Source erasure proves new runtime code/state sits inside the OFF
        # guard. This intentionally makes NO compiled-binary identity claim.
        checks = {}
        for name in ['src/search.cpp', 'src/uci.cpp']:
            original = erase_feature_blocks((base / name).read_text())
            patched = erase_feature_blocks((dest / name).read_text())
            checks[name] = original == patched
            if original != patched:
                raise AssertionError('OFF source guard erasure mismatch: ' + key + ' ' + name)
        for name in prep.FILES:
            generated = prep.changed(name, (base / name).read_text())
            assert (dest / name).read_text() == generated, (key, name)
        runs.append({'base': key, 'off_runtime_source_erasure_equal': checks,
                     'patched_input_files': prep.inventory(dest)})
    after = {k: prep.inventory(v) for k, v in prep.BASES.items()}
    assert before == after
    result = {'scope': 'source-only; GNU patch and Python; no native engine/compiler',
              'pass': True, 'patch_sha256': EXPECTED_SHA, 'runs': runs,
              'originals_unchanged': True,
              'original_full_source_inventories': before,
              'native_correctness': 'UNVERIFIED', 'speed': 'UNVERIFIED'}
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'pass': True, 'gnu_patch_runs': 6, 'off_source_erasure_equal': True,
                      'original_counts': {k: len(v) for k, v in before.items()},
                      'receipt': str(result_path)}, indent=2))


if __name__ == '__main__':
    main()
