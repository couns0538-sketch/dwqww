#!/usr/bin/env python3
"""net_ready.py <RESULT.json> <control .nnue2> - checks of the GPU-trained v2 nets (2026-11-04): is a packaged net ready?
Reads RESULT.json (json, not grep): all_checks_passed must be true, the .nnue2 it names must exist, its sha256 must equal
the recorded one, and its size must equal the control net's (same bucket layout). Prints the facts and the fnv1a from
the recorded `info` line. Exit 0 = ready, 1 = not ready, 2 = no RESULT.json yet. Read-only, standard library."""
import hashlib
import json
import os
import re
import sys


def main():
    if len(sys.argv) != 3:
        print('usage: net_ready.py <RESULT.json> <control .nnue2>')
        return 2
    rj, control = sys.argv[1], sys.argv[2]
    if not os.path.isfile(rj):
        print(f'not ready: no {rj}')
        return 2
    try:
        with open(rj, encoding='utf-8-sig') as f:
            r = json.load(f)
    except (OSError, ValueError) as e:
        print(f'not ready: {rj} unreadable ({e})')
        return 2
    ok = True
    passed = r.get('all_checks_passed') is True
    print(f'all_checks_passed: {r.get("all_checks_passed")!r}')
    ok &= passed
    net = r.get('net', '')
    exists = os.path.isfile(net)
    print(f'net: {net} exists={exists}')
    ok &= exists
    if exists:
        h = hashlib.sha256()
        with open(net, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        sha = h.hexdigest()
        same = sha == r.get('sha256')
        print(f'sha256 {sha} recorded {r.get("sha256")} equal={same}')
        ok &= same
        size, csize = os.path.getsize(net), os.path.getsize(control)
        print(f'size {size} control {os.path.basename(control)} {csize} equal={size == csize}')
        ok &= size == csize
    m = re.search(r'fnv1a ([0-9a-f]+)', r.get('info', ''))
    print(f'info fnv1a: {m.group(1) if m else "n/a"}; exe_sha256 {r.get("exe_sha256")}; bench_on {r.get("bench_on")}')
    print('READY' if ok else 'NOT READY')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
