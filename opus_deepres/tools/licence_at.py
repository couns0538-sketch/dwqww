#!/usr/bin/env python3
"""licence_at.py - the LICENSE of a GitHub repo at an exact commit (default: HEAD of the default branch).

usage: python -I -B licence_at.py OWNER/REPO [SHA] [--row]
Prints the commit sha and date, every root file named LICEN[CS]E* / COPYING* / UNLICENSE* at that commit with its
first non-empty lines and a guessed SPDX id, and the licence GitHub detects on the default branch. A repo with no such
file prints "LICENSE absent at <sha>" (exit 0). --row prints one markdown row for opus_deepres/LICENCES.md.
"""
import base64
import json
import re
import subprocess
import sys


def gh(args, allow_fail=False):
    r = subprocess.run(['gh', 'api'] + args, capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        if allow_fail:
            return None
        sys.exit(f'licence_at: gh api {" ".join(args)} failed: {r.stderr.strip()[:300]}')
    return json.loads(r.stdout)


def guess(text):
    t = ' '.join(text.split()).lower()
    if 'gnu affero general public license' in t:
        v = '3.0' if 'version 3' in t else '?'
        return f'AGPL-{v}'
    if 'gnu lesser general public license' in t:
        return 'LGPL'
    if 'gnu general public license' in t:
        v = '3.0' if 'version 3' in t else ('2.0' if 'version 2' in t else '?')
        return f'GPL-{v}'
    if 'permission is hereby granted, free of charge' in t:
        return 'MIT'
    if 'apache license' in t and 'version 2.0' in t:
        return 'Apache-2.0'
    if 'redistribution and use in source and binary forms' in t:
        return 'BSD'
    if 'this is free and unencumbered software released into the public domain' in t:
        return 'Unlicense'
    if 'mozilla public license' in t:
        return 'MPL-2.0'
    return 'unknown (read the text)'


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    row = '--row' in sys.argv
    if not args:
        sys.exit(__doc__)
    repo = args[0]
    meta = gh([f'repos/{repo}'])
    sha = args[1] if len(args) > 1 else gh([f'repos/{repo}/commits/{meta["default_branch"]}'])['sha']
    c = gh([f'repos/{repo}/commits/{sha}'])
    sha = c['sha']
    date = c['commit']['committer']['date'][:10]
    tree = gh([f'repos/{repo}/git/trees/{sha}'])
    names = [e['path'] for e in tree.get('tree', []) if e['type'] == 'blob'
             and re.match(r'(?i)^(licen[cs]e|copying|unlicense)', e['path'])]
    det = gh([f'repos/{repo}/license'], allow_fail=True)
    detected = (det or {}).get('license', {}).get('spdx_id', 'none') if det else 'none'
    found = []
    for n in names:
        blob = gh([f'repos/{repo}/contents/{n}?ref={sha}'])
        text = base64.b64decode(blob['content']).decode('utf-8', 'replace')
        first = [l.strip() for l in text.splitlines() if l.strip()][:3]
        found.append((n, guess(text), first))
    if row:
        if found:
            for n, g, first in found:
                print(f'| {repo} | {sha[:10]} | {date} | {n} | {g} | {first[0][:70] if first else ""} | api: {detected} |')
        else:
            print(f'| {repo} | {sha[:10]} | {date} | absent | no licence (all rights reserved) | - | api: {detected} |')
        return
    print(f'{repo} at {sha} ({date}); default branch {meta["default_branch"]}; GitHub-detected licence: {detected}')
    if not found:
        print(f'LICENSE absent at {sha[:10]} (no LICEN[CS]E* / COPYING* / UNLICENSE* in the root tree)')
    for n, g, first in found:
        print(f'  {n}: guessed {g}')
        for l in first:
            print(f'    | {l[:110]}')


if __name__ == '__main__':
    main()
