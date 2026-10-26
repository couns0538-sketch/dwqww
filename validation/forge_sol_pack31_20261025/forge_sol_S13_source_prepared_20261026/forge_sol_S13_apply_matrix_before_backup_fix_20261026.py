"""Read-only reference inventories plus private Git/GNU application checks."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import time
from forge_sol_S13_prepare_source_20261026 import NAMES, transform
from forge_sol_S13_source_contract_20261026 import validate_source

ROOT = Path(__file__).resolve().parent
FILES = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES = {
    'L': FILES / '01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
    'Lprime': FILES / '01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
    'B': FILES / '01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src',
}
VIEWS = Path('/tmp/forge_sol_S13_private_views_20261026')
PATCH = ROOT / 'forge_sol_S13_ttprefetch_20261026.patch'


def inventory(root):
    rows = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('symlink reference requires separate treatment')
        if p.is_file():
            data = p.read_bytes()
            rows[str(p.relative_to(root))] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    return rows


def command(argv, cwd, label):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    out = ROOT / (label + '.stdout')
    err = ROOT / (label + '.stderr')
    with out.open('xb') as f:
        f.write(result.stdout)
    with err.open('xb') as f:
        f.write(result.stderr)
    row = {'argv': argv, 'cwd': str(cwd), 'returncode': result.returncode,
           'stdout': str(out), 'stderr': str(err), 'elapsed_seconds': time.monotonic() - start,
           'scope': 'source application only; no compiler or engine'}
    if result.returncode != 0:
        raise RuntimeError(json.dumps(row))
    return row


def main():
    result_path = ROOT / 'forge_sol_S13_apply_matrix_result_20261026.json'
    if result_path.exists():
        raise FileExistsError('preserve previous matrix result')
    before = {name: inventory(path) for name, path in BASES.items()}
    commands = []
    results = []
    for name, source in BASES.items():
        view = VIEWS / (name + '_applied_once')
        shutil.copytree(source, view)
        commands.append(command(['git', '--no-optional-locks', '-c', 'gc.auto=0', 'apply', '--check', str(PATCH)], view, 'forge_sol_S13_' + name + '_git_check_20261026'))
        commands.append(command(['patch', '--dry-run', '--batch', '-p1', '-F0', '-i', str(PATCH)], view, 'forge_sol_S13_' + name + '_gnu_dry_20261026'))
        commands.append(command(['patch', '--batch', '-p1', '-F0', '-i', str(PATCH)], view, 'forge_sol_S13_' + name + '_gnu_apply_20261026'))
        after = inventory(view)
        if set(after) != set(before[name]):
            raise ValueError('private applied file inventory changed')
        changed = sorted(key for key in after if after[key] != before[name][key])
        if changed != sorted(NAMES):
            raise ValueError('unexpected changed source paths: ' + str(changed))
        for path in NAMES:
            expected = transform(path, (source / path).read_bytes().decode('utf-8')).encode('utf-8')
            if (view / path).read_bytes() != expected:
                raise ValueError('applied bytes differ from bounded transformation: ' + path)
        contract = validate_source(view, source)
        results.append({'base': name, 'source': str(source), 'private_view': str(view),
                        'original_files': len(before[name]), 'changed_files': changed,
                        'OFF_source_erasure': contract,
                        'net_sha256': after['src/nnue_weights.inc']['sha256']})
    untouched = {name: inventory(path) for name, path in BASES.items()}
    if before != untouched:
        raise ValueError('reference source changed')
    data = {'status': 'PASS_SOURCE_MATRIX_ONLY', 'commands': commands, 'bases': results,
            'original_inventories': before, 'originals_unchanged': True,
            'native_builds_correctness_speed_strength': 'UNVERIFIED_NOT_RUN'}
    result_path.write_text(json.dumps(data, indent=2) + '\n')
    print('PASS nine Git/GNU source checks; all reference files unchanged; no native execution')


if __name__ == '__main__':
    main()
