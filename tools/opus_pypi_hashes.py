#!/usr/bin/env python3
"""opus_pypi_hashes.py - hash-pin a requirements file for THIS interpreter (R14 finish, CR SHOULD; own code).

For every `name==version` line of --requirements it reads PyPI's JSON metadata for that exact release
(https://pypi.org/pypi/<name>/<version>/json) and keeps the sha256 of every distribution file this interpreter can
install (wheel tags from packaging.tags.sys_tags(), the target runtime's own list); a release without such a wheel
keeps its sdist hash. It prints a --require-hashes requirements file and fails if any line gets no hash.
  python opus_pypi_hashes.py --requirements tools/requirements-r14.txt --out tools/requirements-r14-hashes.txt
Verify the result without touching an installed runtime:
  python -m pip download --require-hashes --no-deps -r tools/requirements-r14-hashes.txt -d <new tmp dir>
"""
import argparse
import json
import re
import sys
import urllib.request

from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

LINE = re.compile(r'^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)$')


def release_files(name, version):
    url = f'https://pypi.org/pypi/{name}/{version}/json'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.load(response)
    if data['info']['version'] != version:
        raise ValueError(f'{name}: PyPI answered version {data["info"]["version"]}, not {version}')
    return data['urls']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--requirements', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    supported = {str(t) for t in sys_tags()}
    out, missing = [], []
    for raw in open(a.requirements, encoding='utf-8'):
        line = raw.strip()
        if not line:
            continue
        m = LINE.match(line)
        if not m:
            raise ValueError(f'not a name==version pin: {line!r}')
        name, version = m.groups()
        hashes, chosen = [], []
        files = release_files(name, version)
        for f in files:
            if f['packagetype'] == 'bdist_wheel':
                _, _, _, tags = parse_wheel_filename(f['filename'])
                if any(str(t) in supported for t in tags):
                    hashes.append(f['digests']['sha256'])
                    chosen.append(f['filename'])
        if not hashes:
            for f in files:
                if f['packagetype'] == 'sdist':
                    hashes.append(f['digests']['sha256'])
                    chosen.append(f['filename'])
        if not hashes:
            missing.append(line)
            continue
        out.append(f'# {name} {version}: ' + ', '.join(chosen))
        out.append(f'{name}=={version} ' + ' '.join(f'--hash=sha256:{h}' for h in hashes))
    if missing:
        sys.exit('no installable distribution for: ' + ', '.join(missing))
    with open(a.out, 'x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(out) + '\n')
    print(f'{len(out) // 2} requirements hash-pinned -> {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
