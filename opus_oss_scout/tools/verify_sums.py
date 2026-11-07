#!/usr/bin/env python3
"""verify_sums.py - OSS scout: re-hash every entry of every trials/*/SHA256SUMS (paths relative to the scout base
folder, `sha256sum` format "<hex> *<path>" or "<hex>  <path>"; other lines are notes) and report mismatches / missing.

usage: python -I -B verify_sums.py <trials dir> [--base C:/opus_5h/oss_scout]
Exit 0 when every listed file exists and matches, 1 otherwise.
"""
import hashlib
import os
import re
import sys

LINE = re.compile(r'^([0-9a-fA-F]{64}) [ *](.+)$')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    trials = argv[0]
    base = argv[argv.index('--base') + 1] if '--base' in argv else 'C:/opus_5h/oss_scout'
    bad = ok = 0
    for root, _, files in os.walk(trials):
        if 'SHA256SUMS' not in files:
            continue
        for line in open(os.path.join(root, 'SHA256SUMS'), encoding='utf-8'):
            m = LINE.match(line.strip())
            if not m:
                continue
            want, rel = m.group(1).lower(), m.group(2).strip()
            p = rel if os.path.isabs(rel) or rel.startswith('/c/') else os.path.join(base, rel)
            if p.startswith('/c/'):
                p = 'C:/' + p[3:]
            if not os.path.exists(p):
                print(f'MISSING {os.path.basename(root)}: {rel}')
                bad += 1
                continue
            got = sha256(p)
            if got != want:
                print(f'DIFF    {os.path.basename(root)}: {rel} want {want[:12]} got {got[:12]}')
                bad += 1
            else:
                ok += 1
    print(f'verified {ok} entries, {bad} problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
