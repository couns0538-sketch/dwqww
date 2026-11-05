#!/usr/bin/env python3
"""card_lint.py - check research cards against the job's card rules.

usage: python -I -B card_lint.py [FILE ...]   (default: every *.md under opus_deepres/cards except TEMPLATE.md)
Full card: the 8 field headings in order (Source, Licence, Mechanism, Forge fit, Expected gain, Effort, Test plan,
OFF-by-default design), at most 60 lines, "UNPROVEN" inside Expected gain, a gate route (SPRT or ABBA) inside Test
plan, a Status line; PENDING fields are counted, not failed. One-line card: a file whose first line starts with
"ONE-LINE |" (fields separated by "|": idea | source link | licence | source Elo | Forge has it | gate route |
Forge estimate UNPROVEN). Every file: no AI-vendor / model-company names (the machine name grok-pc is allowed), no
licence or copyright header lines. Exit 0 = clean, 1 = findings.
"""
import base64
import glob
import os
import re
import sys

FIELDS = ['Source', 'Licence', 'Mechanism', 'Forge fit', 'Expected gain', 'Effort', 'Test plan',
          'OFF-by-default design']
# AI vendor / model-company terms, base64 so this file does not carry them in clear text
NAMES = base64.b64decode('b3BlbmFpCmFudGhyb3BpYwpjbGF1ZGUKY2hhdGdwdApncHQKZ2VtaW5pCmRlZXBtaW5kCnhhaQpncm9rCm1pc3'
                         'RyYWwKbGxhbWEKY29waWxvdApkZWVwc2Vlawpxd2VuCmNvZGV4CnNvbm5ldApoYWlrdQ==').decode().split()
NAME_RX = re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(NAMES) + r')(?![A-Za-z0-9])', re.I)
ALLOWED = re.compile(r'grok-pc', re.I)
HEADER_RX = re.compile(r'^\s*(//|#|/\*|\*)?\s*(copyright\s+(\(c\)|\d{4})|spdx-license-identifier)', re.I)


def lint(path):
    out = []
    text = open(path, encoding='utf-8', errors='replace').read()
    lines = text.splitlines()
    for i, l in enumerate(lines, 1):
        m = NAME_RX.search(ALLOWED.sub('', l))
        if m:
            out.append(f'{path}:{i}: vendor/model name "{m.group(1)}"')
        if HEADER_RX.search(l):
            out.append(f'{path}:{i}: licence/copyright header line')
    head = ' '.join(lines[:3])
    if lines and len(lines) <= 3 and (lines[0].startswith('MERGED into') or
                                      (lines[0].startswith('Status:') and re.search(r'DUPLICATE|MERGED', head))):
        return out, 0  # merge marker of a duplicate folded into a TABLE.md row (not a card); names / headers still checked
    if lines and lines[0].startswith('ONE-LINE |'):
        parts = [p.strip() for p in lines[0].split('|')]
        if len(parts) < 8:
            out.append(f'{path}:1: one-line card needs 7 fields after ONE-LINE (has {len(parts) - 1})')
        if 'UNPROVEN' not in lines[0]:
            out.append(f'{path}:1: one-line card without UNPROVEN')
        if not re.search(r'SPRT|ABBA', lines[0]):
            out.append(f'{path}:1: one-line card without a gate route (SPRT / ABBA)')
        return out, 0
    if len(lines) > 60:
        out.append(f'{path}: {len(lines)} lines (max 60)')
    if not any(l.startswith('Status:') for l in lines[:4]):
        out.append(f'{path}: no "Status:" line near the top')
    heads = [(i, l[3:].strip()) for i, l in enumerate(lines) if l.startswith('## ')]
    names = [h for _, h in heads]
    pos = -1
    for f in FIELDS:
        if f not in names:
            out.append(f'{path}: missing field "## {f}"')
            continue
        p = names.index(f)
        if p < pos:
            out.append(f'{path}: field "## {f}" out of order')
        pos = p

    def body(field):
        if field not in names:
            return ''
        k = names.index(field)
        a = heads[k][0] + 1
        b = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        return '\n'.join(lines[a:b])
    if 'Expected gain' in names and 'UNPROVEN' not in body('Expected gain'):
        out.append(f'{path}: Expected gain has no UNPROVEN Forge estimate')
    if 'Test plan' in names and not re.search(r'SPRT|ABBA', body('Test plan')):
        out.append(f'{path}: Test plan has no gate route (SPRT / ABBA)')
    pending = sum(1 for f in FIELDS if 'PENDING' in body(f))
    return out, pending


def main():
    files = sys.argv[1:]
    if not files:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cards')
        files = [f for f in glob.glob(os.path.join(root, '**', '*.md'), recursive=True)
                 if os.path.basename(f) != 'TEMPLATE.md']
    bad = 0
    for f in sorted(files):
        findings, pending = lint(f)
        for x in findings:
            print(x)
        bad += len(findings)
        print(f'# {os.path.relpath(f)}: {len(findings)} finding(s), {pending} PENDING field(s)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
