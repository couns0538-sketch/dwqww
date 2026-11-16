#!/usr/bin/env python3
"""check_docs.py — verify the seat-11 documents are structurally sound after many spliced edits.

Checks, per document:
  1. no adjacent duplicated non-structural line (the splice failure I hit once)
  2. no leftover literal placeholders or double articles from a bad replace
  3. every relative path mentioned exists on disk
  4. headings are unique (a duplicated heading usually means a bad splice)
"""
import io
import os
import re
import sys

ROOT = '/agent/repos/dwqww/forge-combo29/swarm/11'
DOCS = [
    'START_HERE.md', 'HAZARD_stale_board.md', 'HAZARD_match_protocol.md',
    'PROBES_THAT_LIED.md', 'PC_SWITCHES.md', 'REVERDICT_file6.md',
    'PCR15_BUILD.md', 'RULE1.md', 'STATUS.md',
]
STRUCTURAL = re.compile(r'^\s*(\||-|#|---|```|\*\(|>|\*\*)')
PATHY = re.compile(r'`((?:checks|opts|positions|patches|job\d[\w]*)/[\w./-]+|[A-Za-z0-9_]+\.(?:md|py|txt|sh|fens|epd))`')

problems = 0
for name in DOCS:
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        print(f'{name}: MISSING')
        problems += 1
        continue
    lines = io.open(path, encoding='utf-8').read().split('\n')

    # 1. adjacent duplicate content lines
    for i in range(1, len(lines)):
        a, b = lines[i - 1].strip(), lines[i].strip()
        if a and a == b and not STRUCTURAL.match(a) and len(a) > 40:
            print(f'{name}:{i+1}: ADJACENT DUPLICATE -> {a[:70]}')
            problems += 1

    # 2. splice artefacts
    for i, line in enumerate(lines, 1):
        for bad in (' apart Two ', '  ', ' , ', ' . ', 'Trap Trap'):
            if bad in line and bad != '  ':
                print(f'{name}:{i}: SPLICE ARTEFACT {bad!r} -> {line.strip()[:70]}')
                problems += 1
                break

    # 3. referenced relative paths exist
    for i, line in enumerate(lines, 1):
        for m in PATHY.finditer(line):
            ref = m.group(1)
            if '*' in ref:
                continue
            # files named in prose that live on OTHER branches (the brief's deepseek6 longK file,
            # the handoff FABLE_TO_swarm_N files) are not expected to be in this folder.
            external = ('FABLE_TO_swarm', 'REPORT_deepseek6', 'REPORT_glmflash',
                        'first200.fens', 'set_G.epd')
            if any(ref.startswith(x) or ref == x for x in external):
                continue
            if not os.path.exists(os.path.join(ROOT, ref)):
                print(f'{name}:{i}: MISSING PATH -> {ref}')
                problems += 1

    # 4. duplicate TOP-LEVEL headings only (## and #). Repeated ### subheads are legitimate
    #    structure in PROBES_THAT_LIED.md, where each trap has "What I saw" / "The general rule".
    heads = [l.strip() for l in lines if l.startswith('## ') or l.startswith('# ')]
    seen = {}
    for h in heads:
        seen[h] = seen.get(h, 0) + 1
    for h, c in seen.items():
        if c > 1:
            print(f'{name}: DUPLICATE HEADING ({c}x) -> {h[:60]}')
            problems += 1

print(f'\n{problems} problem(s) across {len(DOCS)} documents')
sys.exit(0 if problems == 0 else 1)
