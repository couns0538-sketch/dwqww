#!/usr/bin/env python3
"""path_sweep.py <file.md> [...] - Opus 30-h job: every Windows path a document cites must exist (own code).
Finds drive paths (C:\\..., D:\\..., F:\\...) in the text, trims trailing punctuation, skips templates (<...>, *, ...,
$var, {x}) and prints one line per path: ok / MISSING. Relative branch paths (a/..., opus_30h/...) are checked against
the branch root given by --root (default D:\\o30\\wt\\opus_30h) when they appear in backticks and end in a file
suffix. Exit 1 if anything is missing."""
import argparse
import os
import re
import sys

WIN = re.compile(r'[A-Z]:\\[^\s`|"\'<>*]+')
REL = re.compile(r'`((?:opus_30h/)?(?:a|b|tools|mcp|kit25|skills)/[A-Za-z0-9_./-]+\.(?:py|sh|ps1|md|patch|json|csv|cpp|bat|rs|txt))`')


def clean(p):
    p = p.rstrip('.,;:)]}')
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--root', default=r'D:\o30\wt\opus_30h')
    ap.add_argument('--allow', action='append', default=[], help='a path that may be missing (e.g. D:\\o30\\WINDOW.md: '
                                                                 'written only if the GPU is released)')
    a = ap.parse_args()
    seen, missing = set(), 0
    for f in a.files:
        text = open(f, encoding='utf-8').read()
        for m in WIN.finditer(text):
            p = clean(m.group(0))
            if any(t in p for t in ('...', '$', '{', '}', '%')) or p.endswith('\\') or text[m.end():m.end() + 1] == '<':
                continue   # templates: `...\<name>\x`, `selftest_<n>`
            sm = re.fullmatch(r'(.+)\.(\w+)/\.(\w+)', p)   # shorthand `x.pos/.hce` = x.pos and x.hce
            if sm:
                seen.update({f'{sm.group(1)}.{sm.group(2)}', f'{sm.group(1)}.{sm.group(3)}'})
                continue
            seen.add(p)
        for m in REL.finditer(text):
            rel = m.group(1)
            rel = rel[len('opus_30h/'):] if rel.startswith('opus_30h/') else rel
            seen.add(os.path.join(a.root, rel.replace('/', '\\')))
    allowed = {x.lower() for x in a.allow}
    for p in sorted(seen):
        ok = os.path.exists(p)
        if not ok and p.lower() in allowed:
            print('allowed ' + p)
            continue
        missing += not ok
        print(('ok      ' if ok else 'MISSING ') + p)
    print(f'path_sweep: {len(seen)} paths, {missing} missing')
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
