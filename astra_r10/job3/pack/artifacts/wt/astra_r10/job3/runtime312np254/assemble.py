"""Separate immutable NumPy2.5.4 runtime revision; preserve the original runtime."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path('D:/a10')
JOB = ROOT / 'wt/astra_r10/job3/runtime312np254'
SOURCE = ROOT / 'job3/runtime312'
TARGET = ROOT / 'job3/runtime312np254'
SOURCE_MANIFEST_SHA = 'a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461'
SOURCE_LOCK_SHA = 'ef9dcb6af1e3e64b9d2bbdbcf2eeac7480f9864a56b5bd96cad1741c50ac9a90'
NUMPY_WHEEL = 'numpy-2.5.4-cp312-cp312-win_amd64.whl'
NUMPY_SHA = 'a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a'
RESERVATION = 1_400_000_000
sys.path.insert(0, str(ROOT / 'wt/astra_r10/job3/runtime312'))
import collect_wheels as previous
safety, need = previous.safety, previous.need


def omitted(relative):
    parts = relative.split('/')
    return (len(parts) >= 2 and parts[0] == 'packages' and parts[1] in
            ('numpy', 'numpy.libs', 'numpy-1.26.4.dist-info', 'numpy-1.26.4-cp312-cp312-win_amd64.whl')) or relative == 'packages/bin/f2py.exe'


def bound(path, expected):
    path = safety.checked_path(path)
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'source receipt identity mismatch')
    return raw, json.loads(raw)


def copy_bound(source, target, expected, size):
    source = safety.checked_path(source); target = safety.checked_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(); count = 0
    with source.open('rb') as src, target.open('xb') as dst:
        before = os.fstat(src.fileno())
        for data in iter(lambda: src.read(1024 * 1024), b''):
            count += len(data); sha.update(data); dst.write(data)
        after = os.fstat(src.fileno())
    identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    need(identity(before) == identity(after) == identity(source.stat()), 'copy source changed while consumed')
    need(sha.hexdigest() == expected and count == size, 'copied bytes differ from fixed source manifest')
    need(safety.digests(target)[0] == expected, 'destination copy identity mismatch')


def write(path, value):
    safety.write_new(path, (json.dumps(value, indent=2) + '\n').encode())


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    process = previous.base.psutil.Process()
    need(process.nice() == previous.base.psutil.IDLE_PRIORITY_CLASS and process.cpu_affinity() == [3], 'Idle CPU3 required')
    need(not TARGET.exists() and not (JOB / 'RUNTIME_FILES.json').exists(), 'fresh runtime revision required')
    safety.disk_budget(RESERVATION)
    workspace = safety.workspace_bytes()
    need(workspace + RESERVATION <= safety.CAP, 'revision reservation exceeds workspace cap')
    manifest_raw, source_manifest = bound(SOURCE / 'RUNTIME_FILES.json', SOURCE_MANIFEST_SHA)
    lock_raw, source_lock = bound(ROOT / 'wt/astra_r10/job3/runtime312/WHEEL_LOCK.json', SOURCE_LOCK_SHA)
    need(source_manifest['status'] == 'RUNTIME_ASSEMBLED' and Path(source_manifest['root']) == SOURCE,
         'fixed original runtime manifest required')
    kept, removed = [], []
    for row in source_manifest['files']:
        relative = safety.relative_name(row['path'])
        need(relative.split('/')[0] in ('python', 'packages', 'bootstrap_packages'), 'source manifest input scope')
        (removed if omitted(relative) else kept).append(row)
    need(removed and any(r['path'] == 'packages/bin/f2py.exe' for r in removed), 'old NumPy-owned inputs must be omitted')
    copy_bytes = sum(r['bytes'] for r in kept)
    need(copy_bytes < 650_000_000, 'source subset exceeds copy bound')
    downloads = TARGET / 'downloads'; downloads.mkdir(parents=True)
    metadata = previous.base.download('https://pypi.org/pypi/numpy/2.5.4/json', downloads / 'numpy-2.5.4.json', 8_000_000)
    data = json.loads(Path(metadata['path']).read_bytes())
    choices = [item for item in data['urls'] if item['filename'] == NUMPY_WHEEL]
    need(len(choices) == 1, 'official NumPy2.5.4 cp312 Windows AMD64 wheel is unavailable')
    official = choices[0]
    need(official['digests']['sha256'] == NUMPY_SHA and official['size'] < 30_000_000, 'official NumPy wheel identity differs')
    wheel = previous.base.download(official['url'], downloads / NUMPY_WHEEL, 30_000_000)
    need(wheel['sha256'] == NUMPY_SHA and wheel['bytes'] == official['size'], 'downloaded NumPy identity differs')
    wheel_info = previous.metadata(Path(wheel['path']))
    need(wheel_info['name'].lower() == 'numpy' and wheel_info['version'] == '2.5.4' and
         wheel_info['expanded_bytes'] <= 200_000_000, 'NumPy wheel name/version/expanded bound')
    measured = copy_bytes + 2 * wheel_info['expanded_bytes'] + 50_000_000
    need(measured + wheel['bytes'] + metadata['bytes'] <= RESERVATION, 'measured revision exceeds reservation')
    safety.disk_budget(measured)
    need(safety.workspace_bytes() + measured <= safety.CAP, 'fresh measured revision exceeds workspace cap')
    for row in kept:
        copy_bound(SOURCE / row['path'], TARGET / row['path'], row['sha256'], row['bytes'])
    for name in ('tmp', 'cache', 'logs'):
        (TARGET / name).mkdir()
    stage = TARGET / 'numpy_target'
    req = JOB / 'NUMPY_REQUIREMENT.txt'
    safety.write_new(req, (Path(wheel['path']).as_uri() + ' --hash=sha256:' + NUMPY_SHA + '\n').encode())
    environment = previous.pip_environment(os.environ)
    environment.update(TEMP=str(TARGET / 'tmp'), TMP=str(TARGET / 'tmp'), TMPDIR=str(TARGET / 'tmp'),
                       PIP_CACHE_DIR=str(TARGET / 'cache'))
    command = [str(TARGET / 'python/python.exe'), '-I', '-B', str(JOB / 'pip_entry.py'), 'install',
               '--no-index', '--no-deps', '--no-cache-dir', '--disable-pip-version-check', '--no-compile',
               '--ignore-installed', '--require-hashes', '--target', str(stage), '--requirement', str(req)]
    write(JOB / 'INSTALL_COMMAND.json', command)
    start = time.monotonic()
    with (TARGET / 'logs/install.stdout').open('xb') as out, (TARGET / 'logs/install.stderr').open('xb') as err:
        child = subprocess.Popen(command, env=environment, cwd=TARGET, stdout=out, stderr=err)
        try:
            while child.poll() is None:
                time.sleep(1)
                need(time.monotonic() - start < 600, 'NumPy install time bound')
                need(previous.tree_size(TARGET) < RESERVATION - 50_000_000, 'revision write reservation exceeded')
                safety.disk_budget(50_000_000)
        except BaseException:
            child.terminate(); child.wait(timeout=15)
            raise
    need(child.returncode == 0, 'new NumPy local install failed; preserve attempt')
    installed_numpy = []
    for folder, dirs, files in os.walk(stage, followlinks=False):
        for name in dirs + files:
            need(not safety.reparse(Path(folder) / name), 'NumPy staging reparse path refused')
        for name in files:
            path = Path(folder) / name
            relative = path.relative_to(stage).as_posix()
            safety.relative_name(relative)
            sha, _, size = safety.digests(path)
            copy_bound(path, TARGET / 'packages' / relative, sha, size)
            installed_numpy.append({'path': 'packages/' + relative, 'bytes': size, 'sha256': sha})
    need(installed_numpy and any(r['path'].startswith('packages/numpy-2.5.4.dist-info/') for r in installed_numpy),
         'installed NumPy2.5.4 distribution missing')
    files = sorted(kept + installed_numpy, key=lambda row: row['path'].casefold())
    need(len({r['path'].casefold() for r in files}) == len(files), 'new runtime path collision')
    actual = set()
    for prefix in ('python', 'packages', 'bootstrap_packages'):
        for folder, dirs, names in os.walk(TARGET / prefix, followlinks=False):
            for name in dirs + names:
                need(not safety.reparse(Path(folder) / name), 'runtime revision reparse path refused')
            actual.update((Path(folder) / name).relative_to(TARGET).as_posix() for name in names)
    need(actual == {r['path'] for r in files}, 'new runtime file inventory differs')
    for row in files:
        need(safety.digests(TARGET / row['path'])[0] == row['sha256'], 'new runtime input drift')
    need((SOURCE / 'RUNTIME_FILES.json').read_bytes() == manifest_raw, 'source manifest changed')
    need(safety.digests(Path(wheel['path']))[0] == NUMPY_SHA, 'replacement wheel changed')
    replacement = dict(wheel_info, path=wheel['path'], filename=NUMPY_WHEEL, bytes=wheel['bytes'],
                       sha256=NUMPY_SHA, official={'url': official['url'], 'sha256': NUMPY_SHA,
                                                 'bytes': wheel['bytes'], 'metadata': metadata})
    lock = {'schema': 1, 'status': 'RUNTIME_REVISION_ASSEMBLED', 'classification': 'UNPROVEN',
            'source_lock': {'path': str(ROOT / 'wt/astra_r10/job3/runtime312/WHEEL_LOCK.json'), 'sha256': SOURCE_LOCK_SHA},
            'wheels': [replacement if r['name'].lower() == 'numpy' else r for r in source_lock['wheels']],
            'replacement_metadata': metadata, 'new_download': wheel,
            'scope': 'Only NumPy archive newly downloaded. Other wheel identities are inherited source receipts; their archives remain at the original D paths.'}
    write(JOB / 'WHEEL_LOCK.json', lock)
    result = {'schema': 1, 'status': 'RUNTIME_ASSEMBLED', 'classification': 'UNPROVEN', 'root': str(TARGET),
              'files': files, 'runtime_file_bytes': sum(r['bytes'] for r in files),
              'installed_versions': dict(source_manifest['installed_versions'], numpy='2.5.4'),
              'source_runtime': {'path': str(SOURCE), 'manifest_sha256': SOURCE_MANIFEST_SHA,
                  'copied_bytes': copy_bytes, 'omitted_old_numpy_files': removed},
              'wheel_lock_sha256': safety.digests(JOB / 'WHEEL_LOCK.json')[0],
              'measured_new_bytes_reservation': measured + wheel['bytes'] + metadata['bytes'],
              'copy_scope': 'Every copied source file consumed and destination bytes verified against original manifest. Original runtime is read-only. Other copied console entrypoints preserve original interpreter paths and are not qualification entrypoints; invoke this runtime python.exe directly.',
              'scope': 'CPU-only dependency assembly. No Torch/NPT import, compiler, training, optimizer update, GPU or regression execution.'}
    safety.disk_budget(0)
    need(safety.workspace_bytes() <= safety.CAP, 'final workspace cap exceeded')
    write(TARGET / 'RUNTIME_FILES.json', result)
    write(JOB / 'RUNTIME_FILES.json', result)
    print(json.dumps({'status': result['status'], 'files': len(files), 'bytes': result['runtime_file_bytes'],
                      'numpy': '2.5.4', 'measured_reservation': result['measured_new_bytes_reservation']}, indent=2))


if __name__ == '__main__':
    main()
