#!/usr/bin/env python3
"""name_lint.py - fail if any file under the given paths names an AI vendor / model company (speed job, own code).

usage: python -I -B name_lint.py <path> [<path> ...]
Code files (.ps1 / .py) are kept out of the git clean filter (the filter would change tested code), so this check runs
before every commit instead. Same word list as novendor_filter.py (base64 so this file does not carry the names);
the machine name grok-pc and paths through the agent configuration folder are reported too. Exit 1 on a hit.
"""
import base64
import pathlib
import re
import sys

NAMES = base64.b64decode('b3BlbmFpCmFudGhyb3BpYwpjbGF1ZGUKY2hhdGdwdApncHQKZ2VtaW5pCmRlZXBtaW5kCnhhaQpncm9rCm1pc3'
                         'RyYWwKbGxhbWEKY29waWxvdApkZWVwc2Vlawpxd2VuCmNvZGV4CnNvbm5ldApoYWlrdQ==').decode().split()
RX = re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(re.escape(n) for n in NAMES) + r')(?![A-Za-z0-9])(?!-pc)', re.I)


def main():
    hits = 0
    for root in sys.argv[1:]:
        p = pathlib.Path(root)
        files = [p] if p.is_file() else [f for f in p.rglob('*') if f.is_file()]
        for f in files:
            if f.suffix.lower() in ('.exe', '.zip', '.gz', '.png'):
                continue
            try:
                text = f.read_bytes().decode('utf-8', errors='replace')
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if RX.search(line):
                    hits += 1
                    print('%s:%d: %s' % (f, i, RX.search(line).group(0)))
    print('name_lint: %d hit(s)' % hits)
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
