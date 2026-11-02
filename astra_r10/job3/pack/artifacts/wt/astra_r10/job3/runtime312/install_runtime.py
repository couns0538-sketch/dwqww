"""Install only the reviewed local wheel lock and a hash-bound pure-Python chess copy."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile
import collect_wheels as collect

ROOT, JOB, RUNTIME, safety, need = collect.ROOT, collect.JOB, collect.RUNTIME, collect.safety, collect.need
OLD_HASHES = ROOT / 'wt/astra_r10/job3/RUNTIME_CURRENT_HASHES.json'
OLD_HASH = 'c20358958646d3ccf6372fda39548c9c9840626f8dfd93fcc531219d2d16bba6'
OLD_RUNTIME = ROOT / 'job3/runtime'


def verified_json(path, expected):
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'input JSON hash differs: ' + str(path))
    return raw, json.loads(raw)


def verify_bootstrap_archives(boot):
    # Bind the actual pip execution files and official interpreter files, not
    # merely the archived wheel or python.exe. No package code is imported here.
    for row in boot['downloads']:
        path = safety.checked_path(row['path'])
        need(safety.digests(path)[0] == row['sha256'], 'bootstrap archive drift')
        if path.suffix not in ('.nupkg', '.whl'):
            continue
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                if path.suffix == '.nupkg':
                    if not item.filename.lower().startswith('tools/'):
                        continue
                    target = RUNTIME / 'python' / item.filename[6:]
                else:
                    target = RUNTIME / 'bootstrap_packages' / item.filename
                target = safety.checked_path(target)
                need(hashlib.sha256(archive.read(item)).hexdigest() == safety.digests(target)[0],
                     'extracted bootstrap file drift: ' + str(target))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--lock-sha256', required=True)
    args = parser.parse_args()
    p = collect.base.psutil.Process()
    need(p.nice() == collect.base.psutil.IDLE_PRIORITY_CLASS and p.cpu_affinity() == [3], 'Idle CPU3 required')
    lock_path = JOB / 'WHEEL_LOCK.json'
    lock_raw, lock = verified_json(lock_path, args.lock_sha256.lower())
    need(lock['status'] == 'WHEELS_COLLECTED_NOT_INSTALLED', 'official collection required')
    boot_raw, boot = verified_json(JOB / 'BOOTSTRAP.json', lock['bootstrap_sha256'])
    verify_bootstrap_archives(boot)
    packages = safety.checked_path(RUNTIME / 'packages')
    need(not packages.exists() and not (RUNTIME / 'RUNTIME_FILES.json').exists()
         and not (JOB / 'RUNTIME_FILES.json').exists(), 'fresh installation only')
    wheel_rows = lock['wheels']
    need(isinstance(wheel_rows, list) and 1 <= len(wheel_rows) <= 100, 'bounded wheel list required')
    observed_expanded = 0
    requirements = []
    seen = set()
    for row in wheel_rows:
        path = safety.checked_path(row['path'])
        need(path.parent == RUNTIME / 'downloads/wheels' and path.suffix == '.whl', 'locked wheel directory required')
        need(path.name.casefold() not in seen, 'duplicate locked wheel')
        seen.add(path.name.casefold())
        sha, _, size = safety.digests(path)
        need(sha == row['sha256'] and size == row['bytes'], 'locked wheel drift')
        info = collect.metadata(path)
        need(info['expanded_bytes'] == row['expanded_bytes'], 'expanded wheel size drift')
        observed_expanded += info['expanded_bytes']
        requirements.append(path.as_uri() + ' --hash=sha256:' + sha)
    need(observed_expanded == lock['expanded_bytes'], 'combined expanded bytes differ')
    # pip --target temporarily installs into its own D temp scheme before moving
    # into the new target. Reserve both copies plus bounded metadata/chess/logs.
    reservation = observed_expanded * 2 + 100_000_000
    need(reservation <= 4_000_000_000, 'measured installation exceeds reviewed4GB maximum')
    safety.disk_budget(reservation)
    before_workspace = safety.workspace_bytes()
    need(before_workspace + reservation <= safety.CAP, 'measured installation exceeds workspace cap')
    original_runtime_size = collect.tree_size(RUNTIME)
    old_raw, old = verified_json(OLD_HASHES, OLD_HASH)
    chess_rows = [r for r in old['files'] if r['relative'].startswith(('packages/chess/', 'packages/chess-1.11.2.dist-info/'))
                  and '/__pycache__/' not in r['relative'] and not r['relative'].endswith('.pyc')]
    need(chess_rows and any(r['relative'].endswith('/LICENSE.txt') for r in chess_rows), 'chess source and license required')
    for row in chess_rows:
        rel = safety.relative_name(row['relative'])
        need(not rel.lower().endswith(('.pyd', '.dll', '.exe', '.so')), 'chess copy must be pure Python')
        src = safety.checked_path(OLD_RUNTIME / rel)
        need(safety.digests(src)[0] == row['sha256'], 'historically bound chess input drift')
    req_path = JOB / 'INSTALL_REQUIREMENTS.txt'
    safety.write_new(req_path, ('\n'.join(requirements) + '\n').encode())
    python = RUNTIME / 'python/python.exe'
    command = [str(python), '-I', '-B', str(JOB / 'pip_entry.py'), 'install',
               '--no-index', '--no-deps', '--no-cache-dir', '--disable-pip-version-check',
               '--no-compile', '--require-hashes', '--ignore-installed', '--target', str(packages),
               '--requirement', str(req_path)]
    safety.write_new(JOB / 'INSTALL_COMMAND.json', (json.dumps(command, indent=2) + '\n').encode())
    start = time.monotonic()
    with (RUNTIME / 'logs/install.stdout').open('xb') as out, (RUNTIME / 'logs/install.stderr').open('xb') as err:
        child = subprocess.Popen(command, env=collect.pip_environment(os.environ), stdout=out, stderr=err, cwd=RUNTIME)
        try:
            while child.poll() is None:
                time.sleep(1)
                need(time.monotonic() - start < 1200, 'local wheel install time bound')
                need(collect.tree_size(RUNTIME) - original_runtime_size <= reservation - 50_000_000,
                     'local wheel install retained-byte bound')
                safety.disk_budget(50_000_000)
        except BaseException:
            child.terminate(); child.wait(timeout=15)
            raise
    need(child.returncode == 0, 'local wheel install failed; preserve all output')
    for row in chess_rows:
        source = safety.checked_path(OLD_RUNTIME / row['relative'])
        target = safety.checked_path(RUNTIME / row['relative'])
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        need(safety.digests(source)[0] == row['sha256'] == safety.digests(target)[0], 'chess source/copy mismatch')
    # Capture exactly the runtime file sets the regression runner will bind.
    rows = []
    for prefix in ('python', 'packages', 'bootstrap_packages'):
        for folder, dirs, files in os.walk(RUNTIME / prefix, followlinks=False):
            for name in dirs + files:
                need(not safety.reparse(Path(folder) / name), 'assembled runtime reparse path refused')
            for name in sorted(files):
                path = safety.checked_path(Path(folder) / name)
                sha, _, size = safety.digests(path)
                rows.append({'path': path.relative_to(RUNTIME).as_posix(), 'bytes': size, 'sha256': sha})
    rows.sort(key=lambda row: row['path'].casefold())
    result = {'schema': 1, 'status': 'RUNTIME_ASSEMBLED', 'classification': 'UNPROVEN', 'root': str(RUNTIME),
              'files': rows, 'wheel_lock_sha256': args.lock_sha256.lower(),
              'bootstrap_sha256': hashlib.sha256(boot_raw).hexdigest(),
              'installed_versions': {r['name']: r['version'] for r in wheel_rows} | {'chess': '1.11.2'},
              'chess_current_source_manifest': {'path': str(OLD_HASHES), 'sha256': OLD_HASH,
                    'scope': 'Existing D-only copied runtime current identities; not a new original upstream receipt.'},
              'chess_copy': chess_rows, 'measured_install_reservation': reservation,
              'workspace_before': before_workspace, 'runtime_file_bytes': sum(r['bytes'] for r in rows),
              'scope': 'CPU-only assembly; no Torch/NPT import, compiler, training, optimizer update or GPU execution. Regression unrun.'}
    need(hashlib.sha256(lock_path.read_bytes()).hexdigest() == args.lock_sha256.lower(), 'wheel lock changed')
    need(hashlib.sha256(OLD_HASHES.read_bytes()).hexdigest() == OLD_HASH, 'chess source manifest changed')
    verify_bootstrap_archives(boot)
    for row in wheel_rows:
        need(safety.digests(Path(row['path']))[0] == row['sha256'], 'wheel changed during install')
    for row in rows:
        need(safety.digests(RUNTIME / row['path'])[0] == row['sha256'], 'runtime changed before publication')
    safety.disk_budget(0)
    need(safety.workspace_bytes() <= safety.CAP, 'final workspace cap exceeded')
    manifest_bytes = (json.dumps(result, indent=2) + '\n').encode()
    safety.write_new(RUNTIME / 'RUNTIME_FILES.json', manifest_bytes)
    safety.write_new(JOB / 'RUNTIME_FILES.json', manifest_bytes)
    print(json.dumps({'status': result['status'], 'files': len(rows), 'bytes': result['runtime_file_bytes'],
                      'reservation': reservation, 'versions': result['installed_versions']}, indent=2))


if __name__ == '__main__':
    main()
