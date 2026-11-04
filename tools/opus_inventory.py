#!/usr/bin/env python3
"""opus_inventory.py - file inventory for the R14 finish report: full PC path, bytes and full md5 of every file the
R14 finish changed or produced (own code, standard library only).

  opus_inventory.py --base 7636122b71ff27a5b4b781b6775757f926f8fdc4 [--extra DIR ...] [--exclude PATH ...] --out F.md
Lists (1) every file in `git diff --name-only <base> HEAD` of D:/a14 (a path missing on disk is listed as deleted),
(2) every file below each --extra directory (outputs kept outside the repository or ignored by git), sorted by path.
--exclude leaves out files that cannot list themselves (the report that embeds this table). The output is a Markdown
table; the tool refuses an existing --out.
"""
import argparse
import hashlib
import os
import subprocess
import sys

ROOT = 'D:/a14'


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', required=True)
    ap.add_argument('--extra', action='append', default=[])
    ap.add_argument('--exclude', action='append', default=[])
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    names = subprocess.run(['git', '-C', ROOT, 'diff', '--name-only', a.base, 'HEAD'], capture_output=True, text=True,
                           check=True).stdout.splitlines()
    paths = {os.path.normpath(os.path.join(ROOT, n)) for n in names if n.strip()}
    for d in a.extra:
        for dp, _, fs in os.walk(d):
            for f in fs:
                paths.add(os.path.normpath(os.path.join(dp, f)))
    skip = {os.path.normcase(os.path.normpath(p)) for p in a.exclude}
    rows, total = [], 0
    for p in sorted(paths, key=lambda x: x.casefold()):
        if os.path.normcase(p) in skip:
            continue
        if os.path.isfile(p):
            size = os.path.getsize(p)
            total += size
            rows.append(f'| {p} | {size} | {md5(p)} |')
        else:
            rows.append(f'| {p} | - | deleted on the branch |')
    with open(a.out, 'x', encoding='utf-8', newline='\n') as stream:
        stream.write('| file (full PC path) | bytes | md5 |\n|---|---|---|\n' + '\n'.join(rows) + '\n')
    print(f'{len(rows)} files, {total} bytes -> {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
