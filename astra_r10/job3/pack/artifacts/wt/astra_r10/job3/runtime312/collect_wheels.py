"""Collect CPU-only wheels; no package installation, imports, compilation or training."""
from __future__ import annotations
import argparse
import email
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.parse
import zipfile

sys.path.insert(0, str(Path(__file__).parent))
import bootstrap as base
ROOT, JOB, RUNTIME, safety, need = base.ROOT, base.JOB, base.RUNTIME, base.safety, base.need
base.ALLOWED.update({'download.pytorch.org', 'download-r2.pytorch.org'})
TORCH_INDEX = 'https://download.pytorch.org/whl/cpu/torch/'
TORCH_NAME = 'torch-2.9.1+cpu-cp312-cp312-win_amd64.whl'
TOP = ['numpy==1.26.4', 'torchmetrics==1.8.2', 'tyro', 'tensorboard', 'pytest==9.1.1', 'psutil==7.2.2']
RESERVATION = 2_000_000_000
GROWTH_STOP = 1_100_000_000


def pip_environment(inherited):
    env = {key: value for key, value in inherited.items() if not key.upper().startswith('PIP_')}
    env.update(TEMP=str(RUNTIME / 'tmp'), TMP=str(RUNTIME / 'tmp'),
               TMPDIR=str(RUNTIME / 'tmp'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               PIP_CONFIG_FILE='NUL', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_CACHE_DIR='1',
               PIP_CACHE_DIR=str(RUNTIME / 'cache'), PIP_NO_INPUT='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return env


def verify_torch_identity(path, info, sha, size, receipt):
    need(path.name == TORCH_NAME and info['version'] == '2.9.1+cpu', 'CPU Torch identity required')
    need(sha == receipt['sha256'] and size == receipt['bytes'], 'official CPU Torch identity drift')


def tree_size(path):
    total = 0
    for folder, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            item = Path(folder) / name
            need(not safety.reparse(item), 'runtime reparse path refused')
        for name in files:
            total += (Path(folder) / name).stat().st_size
    return total


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(v for k, v in attrs if k == 'href')


def metadata(path):
    total = 0
    folded = set()
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = entry.filename.rstrip('/')
            safety.relative_name(name)
            need(name.casefold() not in folded, 'duplicate wheel filename')
            folded.add(name.casefold())
            need(not (entry.external_attr >> 16) & 0o170000 == 0o120000, 'wheel symlink refused')
            total += entry.file_size
            need(total <= 2_500_000_000, 'single wheel expanded limit')
        names = [n for n in archive.namelist() if len(n.split('/')) == 2 and n.endswith('.dist-info/METADATA')]
        need(len(names) == 1, 'wheel must have exactly one root METADATA')
        need(archive.getinfo(names[0]).file_size < 4_000_000, 'wheel metadata limit')
        info = email.message_from_bytes(archive.read(names[0]))
        return {'name': info['Name'], 'version': info['Version'], 'expanded_bytes': total,
                'license': info.get('License-Expression') or info.get('License'),
                'license_classifiers': [c for c in info.get_all('Classifier', []) if c.startswith('License ::')],
                'license_files': [n for n in archive.namelist() if 'license' in n.lower() or 'copying' in n.lower()],
                'requires_dist': info.get_all('Requires-Dist', [])}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    proc = base.psutil.Process()
    need(proc.nice() == base.psutil.IDLE_PRIORITY_CLASS and proc.cpu_affinity() == [3], 'Idle CPU3 required')
    boot_raw = (JOB / 'BOOTSTRAP.json').read_bytes(); boot = json.loads(boot_raw)
    need(boot['status'] == 'BOOTSTRAP_PASS', 'verified interpreter required')
    python = RUNTIME / 'python/python.exe'
    need(safety.digests(python)[0] == boot['interpreter_sha256'], 'bootstrap interpreter drift')
    lock_path = JOB / 'WHEEL_LOCK.json'
    wheels = RUNTIME / 'downloads/wheels'
    meta_dir = RUNTIME / 'downloads/wheel_metadata'
    need(not wheels.exists() and not meta_dir.exists() and not lock_path.exists(), 'fresh wheel collection only')
    safety.disk_budget(RESERVATION)
    initial_workspace = safety.workspace_bytes()
    need(initial_workspace + RESERVATION <= safety.CAP, 'wheel collection reservation exceeds workspace cap')
    initial_size = tree_size(RUNTIME)
    wheels.mkdir(); meta_dir.mkdir()
    source_records = []
    index = base.download(TORCH_INDEX, meta_dir / 'torch-cpu-index.html', 4_000_000)
    source_records.append(index)
    links = Links(); links.feed(Path(index['path']).read_text(encoding='utf-8'))
    matches = [urllib.parse.urljoin(TORCH_INDEX, link) for link in links.links
               if Path(urllib.parse.unquote(urllib.parse.urlsplit(link).path)).name == TORCH_NAME]
    need(len(matches) == 1, 'one exact official CPU Torch wheel required')
    source_url = matches[0]; parts = urllib.parse.urlsplit(source_url)
    expected = urllib.parse.parse_qs(parts.fragment).get('sha256', [])
    need(len(expected) == 1 and len(expected[0]) == 64, 'official CPU wheel SHA256 anchor required')
    torch = base.download(urllib.parse.urlunsplit(parts._replace(fragment='')), wheels / TORCH_NAME, 500_000_000)
    need(torch['sha256'] == expected[0], 'official CPU Torch SHA256 mismatch')
    torch['official_index'] = index; source_records.append(torch)
    env = pip_environment(os.environ)
    # A local exact CPU Torch wheel participates in dependency resolution. Only
    # PyPI supplies other binary wheels; no extra index or source distribution.
    command = [str(python), '-I', '-B', str(JOB / 'pip_entry.py'), 'download',
               '--only-binary=:all:', '--no-cache-dir', '--disable-pip-version-check',
               '--index-url', 'https://pypi.org/simple', '--dest', str(wheels),
               str(wheels / TORCH_NAME), *TOP]
    command_path = JOB / 'WHEEL_COMMAND.json'
    safety.write_new(command_path, (json.dumps(command, indent=2) + '\n').encode())
    start = time.monotonic()
    with (RUNTIME / 'logs/wheels.stdout').open('xb') as out, (RUNTIME / 'logs/wheels.stderr').open('xb') as err:
        child = subprocess.Popen(command, env=env, stdout=out, stderr=err, cwd=RUNTIME)
        try:
            while child.poll() is None:
                time.sleep(1)
                need(time.monotonic() - start < 1200, 'wheel resolver time bound')
                need(tree_size(RUNTIME) - initial_size <= GROWTH_STOP, 'wheel resolver retained-byte bound')
                safety.disk_budget(500_000_000)
        except BaseException:
            # This one pip process is owned by this adapter. Binary-only download
            # does not launch build subprocesses. Preserve every produced file.
            child.terminate(); child.wait(timeout=15)
            raise
    need(child.returncode == 0, 'official binary wheel resolver failed; retain logs')
    finish_lock(wheels, meta_dir, torch, source_records, boot_raw, boot, initial_workspace)


def finish_lock(wheels, meta_dir, torch, source_records, boot_raw, boot, initial_workspace, recovered=False):
    lock_path = JOB / 'WHEEL_LOCK.json'
    python = RUNTIME / 'python/python.exe'
    records = []
    metadata_bytes = 0
    wheel_files = sorted(wheels.glob('*.whl'))
    need(1 <= len(wheel_files) <= 100, 'bounded wheel inventory required')
    for wheel in wheel_files:
        info = metadata(wheel)
        name = info['name'].lower().replace('_', '-')
        need(not any(bad in name for bad in ('nvidia', 'cuda', 'cudnn', 'directml', 'triton', 'rocm', 'torchvision')),
             'GPU/unrequested package refused')
        sha, _, size = safety.digests(wheel)
        if name == 'torch':
            verify_torch_identity(wheel, info, sha, size, torch)
            official = torch
        else:
            receipt = base.download('https://pypi.org/pypi/' + name + '/' + info['version'] + '/json',
                                    meta_dir / (name + '-' + info['version'] + '.json'),
                                    min(8_000_000, 40_000_000 - metadata_bytes))
            metadata_bytes += receipt['bytes']
            source_records.append(receipt)
            data = json.loads(Path(receipt['path']).read_bytes())
            choices = [f for f in data['urls'] if f['filename'] == wheel.name]
            need(len(choices) == 1, 'wheel absent from official PyPI metadata')
            official = choices[0]
            base.url_allowed(official['url'])
            need(official['digests']['sha256'] == sha and official['size'] == size, 'official PyPI identity mismatch')
            official = {'url': official['url'], 'sha256': sha, 'bytes': size, 'metadata': receipt}
        records.append(dict(info, path=str(wheel), filename=wheel.name, bytes=size, sha256=sha, official=official))
    names = {r['name'].lower().replace('_', '-'): r for r in records}
    need(all(name in names for name in ('torch', 'numpy', 'torchmetrics', 'tyro', 'tensorboard', 'pytest', 'psutil')),
         'all requested dependency roots required')
    need(names['numpy']['version'] == '1.26.4' and names['torchmetrics']['version'] == '1.8.2', 'fixed dependency versions')
    need(sum(r['bytes'] for r in records) < 750_000_000, 'retained wheels exceed reviewed bound')
    need(sum(r['expanded_bytes'] for r in records) < 2_500_000_000, 'expanded dependencies exceed planning bound')
    result = {'schema': 1, 'status': 'WHEELS_COLLECTED_NOT_INSTALLED', 'classification': 'UNPROVEN',
              'python': '3.12.10', 'bootstrap_sha256': hashlib.sha256(boot_raw).hexdigest(),
              'requested': TOP + ['torch==2.9.1+cpu'], 'wheels': records, 'metadata_receipts': source_records,
              'download_bytes': sum(r['bytes'] for r in records),
              'expanded_bytes': sum(r['expanded_bytes'] for r in records),
              'workspace_before': initial_workspace, 'workspace_after': safety.workspace_bytes(),
              'chess': 'separate authorized pure-Python old-runtime copy; no old binary package path imported',
              'metadata_recovery': recovered,
              'scope': 'Official CPU wheels only; no installation/package import/NPT/training/GPU/backend bypass.'}
    for record in records:
        need(safety.digests(Path(record['path']))[0] == record['sha256'], 'wheel changed before lock publication')
    need(safety.digests(python)[0] == boot['interpreter_sha256'], 'interpreter changed during wheel collection')
    safety.write_new(lock_path, (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({k: result[k] for k in ('status', 'download_bytes', 'expanded_bytes', 'workspace_after')}, indent=2))


if __name__ == '__main__':
    main()
