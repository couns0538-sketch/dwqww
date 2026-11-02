"""Bounded official NuGet CPython3.12 + PyPI pip bootstrap, D-only and CPU-only."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('D:/a10')
JOB = ROOT / 'wt/astra_r10/job3/runtime312'
RUNTIME = ROOT / 'job3/runtime312'
ALLOWED = {'www.nuget.org', 'api.nuget.org', 'globalcdn.nuget.org', 'pypi.org', 'files.pythonhosted.org'}
PYTHON_META = "https://www.nuget.org/api/v2/Packages(Id='python',Version='3.12.10')"
PYTHON_URL = 'https://api.nuget.org/v3-flatcontainer/python/3.12.10/python.3.12.10.nupkg'
PIP_META = 'https://pypi.org/pypi/pip/25.3/json'
sys.path.insert(0, str(ROOT / 'pydeps'))
import psutil
sys.path.insert(0, str(ROOT / 'wt/skills/gate-handover-pack/scripts'))
import seal_evidence as safety


def need(ok, message):
    if not ok:
        raise ValueError(message)


def url_allowed(url):
    parts = urllib.parse.urlsplit(url)
    need(parts.scheme == 'https' and parts.hostname in ALLOWED and not parts.username and not parts.password,
         'only official HTTPS NuGet/PyPI sources are allowed')


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        url_allowed(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def download(url, target, limit):
    url_allowed(url)
    need(not target.exists(), 'preserve existing download')
    request = urllib.request.Request(url, headers={'User-Agent': 'Forge-R10-runtime-audit/1.0'})
    opener = urllib.request.build_opener(OfficialRedirect())
    sha = hashlib.sha256(); sha512 = hashlib.sha512(); size = 0
    with opener.open(request, timeout=60) as response, target.open('xb') as stream:
        url_allowed(response.url)
        if response.headers.get('Content-Length'):
            need(int(response.headers['Content-Length']) <= limit, 'download Content-Length exceeds bound')
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            size += len(chunk)
            need(size <= limit, 'download exceeds bound')
            sha.update(chunk); sha512.update(chunk); stream.write(chunk)
        stream.flush(); os.fsync(stream.fileno())
        final_url = response.url
    return {'url': url, 'final_url': final_url, 'path': str(target), 'bytes': size,
            'sha256': sha.hexdigest(), 'sha512_base64': base64.b64encode(sha512.digest()).decode()}


def inspect_archive(path):
    total = 0
    folded = set()
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            name = item.filename.replace('\\', '/')
            rel = PurePosixPath(name)
            need(not rel.is_absolute() and all(p not in ('', '.', '..') for p in rel.parts)
                 and ':' not in name and '\x00' not in name, 'unsafe ZIP path')
            need(name.casefold() not in folded, 'duplicate Windows ZIP path')
            folded.add(name.casefold())
            need(not stat.S_ISLNK(item.external_attr >> 16), 'ZIP symlink refused')
            total += item.file_size
            need(total <= 256_000_000, 'expanded bootstrap archive exceeds bound')
    return total, folded


def extract(path, destination, *, nuget=False):
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            parts = PurePosixPath(item.filename.replace('\\', '/')).parts
            if nuget and parts[0].lower() == 'tools':
                target = RUNTIME / 'python' / Path(*parts[1:])
            elif nuget:
                target = RUNTIME / 'nuget_metadata' / Path(*parts)
            else:
                target = destination / Path(*parts)
            target = safety.checked_path(target)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, target.open('xb') as out:
                    for chunk in iter(lambda: source.read(1024 * 1024), b''):
                        out.write(chunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    proc = psutil.Process()
    need(proc.nice() == psutil.IDLE_PRIORITY_CLASS and proc.cpu_affinity() == [3], 'Idle CPU3-only bootstrap required')
    need(not RUNTIME.exists() and not (JOB / 'BOOTSTRAP.json').exists(), 'fresh runtime312 required; preserve prior attempts')
    safety.disk_budget(500_000_000)
    used = safety.workspace_bytes()
    need(used + 500_000_000 <= safety.CAP, 'workspace cap cannot fit bootstrap reservation')
    downloads = RUNTIME / 'downloads/bootstrap'
    downloads.mkdir(parents=True)
    records = []
    py_meta = download(PYTHON_META, downloads / 'python-3.12.10.nuget.xml', 4_000_000); records.append(py_meta)
    meta = ET.fromstring(Path(py_meta['path']).read_bytes())
    ns = '{http://schemas.microsoft.com/ado/2007/08/dataservices}'
    expected = meta.find('.//' + ns + 'PackageHash')
    algorithm = meta.find('.//' + ns + 'PackageHashAlgorithm')
    need(expected is not None and algorithm is not None and algorithm.text.upper() == 'SHA512',
         'official NuGet package SHA512 metadata required')
    python = download(PYTHON_URL, downloads / 'python.3.12.10.nupkg', 40_000_000); records.append(python)
    need(python['sha512_base64'] == expected.text, 'NuGet package SHA512 mismatch')
    py_size, members = inspect_archive(Path(python['path']))
    for name in ('tools/python.exe', 'tools/include/python.h', 'tools/libs/python312.lib', 'tools/license.txt'):
        need(name in members, 'official runtime lacks required development file: ' + name)
    pip_meta = download(PIP_META, downloads / 'pip-25.3.pypi.json', 4_000_000); records.append(pip_meta)
    metadata = json.loads(Path(pip_meta['path']).read_bytes())
    choices = [entry for entry in metadata['urls'] if entry['filename'] == 'pip-25.3-py3-none-any.whl']
    need(len(choices) == 1, 'exact pip universal wheel missing')
    pip_file = choices[0]
    pip = download(pip_file['url'], downloads / pip_file['filename'], 10_000_000); records.append(pip)
    need(pip['sha256'] == pip_file['digests']['sha256'], 'PyPI pip wheel SHA256 mismatch')
    pip_size, _ = inspect_archive(Path(pip['path']))
    need(sum(item['bytes'] for item in records) <= 64_000_000 and py_size + pip_size <= 256_000_000,
         'combined bootstrap bounds exceeded')
    safety.disk_budget(py_size + pip_size + 20_000_000)
    need(safety.workspace_bytes() + py_size + pip_size + 20_000_000 <= safety.CAP, 'expanded bootstrap cap')
    extract(Path(python['path']), RUNTIME / 'python', nuget=True)
    extract(Path(pip['path']), RUNTIME / 'bootstrap_packages')
    for name in ('tmp', 'cache', 'logs'):
        (RUNTIME / name).mkdir()
    env = dict(os.environ, TEMP=str(RUNTIME / 'tmp'), TMP=str(RUNTIME / 'tmp'),
               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', PIP_CONFIG_FILE='NUL',
               PIP_CACHE_DIR=str(RUNTIME / 'cache'), PIP_DISABLE_PIP_VERSION_CHECK='1')
    command = [str(RUNTIME / 'python/python.exe'), '-I', '-B', '-c',
               "import sys,sysconfig,json;from pathlib import Path;assert sys.version_info[:3]==(3,12,10);p=Path(sys.prefix);assert (p/'include/Python.h').is_file();assert (p/'libs/python312.lib').is_file();print(json.dumps({'version':sys.version,'prefix':sys.prefix,'include':sysconfig.get_path('include')}))"]
    completed = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    safety.write_new(RUNTIME / 'logs/bootstrap-python.stdout', completed.stdout)
    safety.write_new(RUNTIME / 'logs/bootstrap-python.stderr', completed.stderr)
    need(completed.returncode == 0, 'official Python development runtime check failed')
    result = {'schema': 1, 'status': 'BOOTSTRAP_PASS', 'classification': 'UNPROVEN', 'python': '3.12.10',
              'runtime': str(RUNTIME), 'downloads': records, 'expanded_bytes': py_size + pip_size,
              'interpreter_sha256': safety.digests(RUNTIME / 'python/python.exe')[0],
              'development_headers_and_import_library': True, 'python_command': command,
              'pip_version': '25.3', 'pip_license': metadata['info'].get('license_expression') or metadata['info'].get('license'),
              'python_license': 'PSF; original LICENSE.txt retained inside extracted runtime and NuGet archive',
              'scope': 'Official isolated interpreter/pip only. Torch/dependencies not installed; no NPT import/training/GPU/config edits.'}
    safety.write_new(JOB / 'BOOTSTRAP.json', (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({'status': result['status'], 'download_bytes': sum(r['bytes'] for r in records),
                      'expanded_bytes': result['expanded_bytes'], 'python': result['python']}, indent=2))


if __name__ == '__main__':
    main()
