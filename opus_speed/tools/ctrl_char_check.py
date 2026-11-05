#!/usr/bin/env python3
"""ctrl_char_check.py - find (and with --fix-bell-paths repair) control bytes in text files (speed job, own code).

usage: python -I -B ctrl_char_check.py <path> [<path> ...] [--fix-bell-paths]
Reports every byte below 0x20 other than TAB, LF and CR in .ps1 / .py / .md / .txt / .tsv / .patch files. The Bash tool
on this PC collapses '\\\\' inside heredocs, so '\\a' / '\\b' / '\\f' / '\\n' in a Windows path turned into BEL / BS / FF /
newline bytes (seen 09:4x in abba.ps1: F:\\ospd<BEL>bba<BEL>bba_history.log). --fix-bell-paths turns a BEL between path
characters back into a backslash + 'a' (the only repair this needs). Exit 1 if anything remains.
"""
import pathlib
import re
import sys

EXT = {'.ps1', '.py', '.md', '.txt', '.tsv', '.patch', '.sh', '.json'}
BAD = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def main():
    fix = '--fix-bell-paths' in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith('--')]
    left = 0
    for root in paths:
        p = pathlib.Path(root)
        files = [p] if p.is_file() else [f for f in p.rglob('*') if f.is_file() and f.suffix.lower() in EXT]
        for f in files:
            data = f.read_bytes()
            if fix and b'\x07' in data:
                new = re.sub(rb'(?<=[A-Za-z0-9_])\x07(?=[A-Za-z0-9_])', b'\\\\a', data)
                if new != data:
                    f.write_bytes(new)
                    print('fixed BEL in %s' % f)
                    data = new
            for m in BAD.finditer(data):
                line = data.count(b'\n', 0, m.start()) + 1
                print('%s:%d: control byte 0x%02x' % (f, line, m.group(0)[0]))
                left += 1
    print('ctrl_char_check: %d control byte(s) left' % left)
    return 1 if left else 0


if __name__ == '__main__':
    sys.exit(main())
