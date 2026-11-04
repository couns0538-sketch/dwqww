#!/usr/bin/env python3
"""Reviewer helper: byte-level checks of the R14-finish files (run with -I -B through opus_lowrun.py --mask 0x4).
For every path given on stdin (one per line, relative to D:/a14): size, CRLF count, bare CR, NUL, non-ASCII bytes,
tab count, trailing-whitespace lines; plus SHA256 of the runtime downloads against the pins in Setup-R14Runtime.ps1."""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path('D:/a14')


def main():
    paths = [line.strip() for line in sys.stdin if line.strip()]
    print(f'{"path":70} {"bytes":>9} {"crlf":>5} {"cr":>4} {"nul":>4} {"nonascii":>8} {"tabs":>5} {"trailws":>7}')
    for rel in paths:
        p = ROOT / rel
        if not p.is_file():
            print(f'{rel:70} MISSING')
            continue
        data = p.read_bytes()
        crlf = data.count(b'\r\n')
        cr = data.count(b'\r') - crlf
        nul = data.count(b'\x00')
        nonascii = sum(1 for b in data if b > 127)
        tabs = data.count(b'\t')
        trailws = len(re.findall(rb'[ \t]+\r?\n', data))
        print(f'{rel:70} {len(data):9d} {crlf:5d} {cr:4d} {nul:4d} {nonascii:8d} {tabs:5d} {trailws:7d}')
    print()
    print('runtime download pins (Setup-R14Runtime.ps1) vs files on disk:')
    pins = {
        'runtime/downloads/python-3.12.10-embed-amd64.zip': ('fe8ef205f2e9c3ba44d0cf9954e1abd3',
                                                            '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3'),
        'runtime/downloads/get-pip.py': ('8bae3e432175fb42da9d41cbe68217b0',
                                         '356e0d0de21cdc348c3394084d90939b85e4246c4d14c76aee6ca4f46646ea98'),
    }
    for rel, (md5_pin, sha_pin) in pins.items():
        p = ROOT / rel
        if not p.is_file():
            print(f'  {rel}: not on disk (cannot verify)')
            continue
        data = p.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        sha = hashlib.sha256(data).hexdigest()
        print(f'  {rel}: md5 {"MATCH" if md5 == md5_pin else "MISMATCH " + md5}; sha256 {"MATCH" if sha == sha_pin else "MISMATCH " + sha}')
    req = ROOT / 'tools/requirements-r14-hashes.txt'
    text = req.read_text(encoding='utf-8')
    lines = [l for l in text.splitlines() if l and not l.startswith('#')]
    bad = [l for l in lines if not re.match(r'^[A-Za-z0-9_.-]+==[0-9][0-9A-Za-z.]* --hash=sha256:[0-9a-f]{64}$', l)]
    print(f'requirements-r14-hashes.txt: {len(lines)} requirement lines, {len(bad)} without a well-formed --hash=sha256 pin')
    for l in bad:
        print('  BAD:', l)
    wheels = ROOT / 'runtime/downloads/wheels'
    if wheels.is_dir():
        for w in sorted(wheels.iterdir()):
            sha = hashlib.sha256(w.read_bytes()).hexdigest()
            print(f'  wheel {w.name}: sha256 {sha} {"(pinned in requirements)" if sha in text else "(NOT in requirements)"}')
    else:
        print('  runtime/downloads/wheels: absent (bootstrap wheels not on disk; the new --no-index path has not run here)')


if __name__ == '__main__':
    main()
