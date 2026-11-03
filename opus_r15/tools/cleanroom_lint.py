#!/usr/bin/env python3
"""cleanroom_lint.py - Opus R15: clean-room checks for engine patches and commit messages (standard library only).

usage: python -I -B cleanroom_lint.py [--patch P ...] [--message-file F ...] [--commits RANGE --git-dir DIR]
                                      [--terms] [--json OUT]

Rules (Couns, R15): no vendor / model-company / other-engine names and no licence headers in any patched file, comment
or commit message; uci.cpp's `id author` line, tools/openings and LICENSE stay untouched.
  1. Added patch lines and commit messages: no term of the name list or the licence list (case-insensitive, whole
     words). The lists are stored base64-encoded below so the branch itself does not carry the names; --terms
     prints them decoded.
  2. Patches: no hunk adds or removes a line containing `id author`; no path under tools/openings/, no LICENSE* file.
  3. Added patch lines: ASCII only, no CR, no tab-free control characters (LF patches; the lock tree is LF).
Exit 0 = clean, 1 = findings (each printed as path:line: rule: text), 2 = usage / unreadable input.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys

NAMES_B64 = ('b3BlbmFpCmFudGhyb3BpYwpjbGF1ZGUKY2hhdGdwdApncHQKZ2VtaW5pCmdvb2dsZQpkZWVwbWluZAp4YWkKZ3JvawptaXN0cmFs'
             'CmxsYW1hCmNvcGlsb3QKbWljcm9zb2Z0CnN0b2NrZmlzaAprb21vZG8KbGVlbGEKbGMwCmV0aGVyZWFsCmJlcnNlcmsKb2JzaWRpYW4K'
             'cGxlbnR5Y2hlc3MKa29pdmlzdG8Kd2Vpc3MKcnViaWNoZXNzCmNhaXNzYQpzZWVyCnZpcmlkaXRoYXMKaWdlbApjcmFmdHkKcnlia2EK'
             'aG91ZGluaQpzaHJlZGRlcgpjcml0dGVyCmZpc2h0ZXN0CnRvcmNoCmFsdGFpcgpoYWxvZ2VuCg==')
LICENCE_B64 = ('Y29weXJpZ2h0CmxpY2Vuc2UKbGljZW5jZQpzcGR4CmdwbApsZ3BsCmFncGwKYWxsIHJpZ2h0cyByZXNlcnZlZAptaXQgbGljZW5zZQph'
               'cGFjaGUgbGljZW5zZQpic2QgbGljZW5zZQpwZXJtaXNzaW9uIGlzIGhlcmVieSBncmFudGVkCg==')


def terms(b64):
    return [t for t in base64.b64decode(b64).decode('ascii').splitlines() if t.strip()]


def term_regex(words):
    # whole words: a letter / digit may not touch the term on either side ("gpt" in "gpt-4", not in "egypt")
    return re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(re.escape(w) for w in words) + r')(?![A-Za-z0-9])', re.I)


NAME_RX = term_regex(terms(NAMES_B64))
LICENCE_RX = term_regex(terms(LICENCE_B64))
CTRL_RX = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]')


def scan_text(where, text, findings):
    for i, line in enumerate(text.splitlines(), 1):
        for rx, rule in ((NAME_RX, 'name'), (LICENCE_RX, 'licence')):
            m = rx.search(line)
            if m:
                findings.append(f'{where}:{i}: {rule} term "{m.group(1)}": {line.strip()[:120]}')


def scan_patch(path, findings):
    try:
        raw = open(path, 'rb').read()
    except OSError as e:
        print(f'cleanroom_lint: cannot read {path}: {e}', file=sys.stderr)
        sys.exit(2)
    if b'\r' in raw:
        findings.append(f'{path}:0: format: CR bytes in the patch (the lock tree is LF; write patches with LF)')
    text = raw.decode('utf-8', errors='replace')
    current = None
    files = 0
    for i, line in enumerate(text.split('\n'), 1):
        if line.startswith('diff --git '):
            files += 1
            m = re.match(r'diff --git a/(\S+) b/(\S+)', line)
            current = m.group(2) if m else line
            if re.match(r'(tools/openings/|LICENSE)', current) or os.path.basename(current).startswith('LICENSE'):
                findings.append(f'{path}:{i}: protected path: {current} must stay untouched')
            continue
        if line.startswith(('+++', '---')):
            continue
        if line.startswith(('+', '-')) and 'id author' in line and current and current.endswith('uci.cpp'):
            findings.append(f'{path}:{i}: protected line: uci.cpp `id author` must stay untouched: {line.strip()[:100]}')
        if not line.startswith('+'):
            continue
        body = line[1:]
        for rx, rule in ((NAME_RX, 'name'), (LICENCE_RX, 'licence')):
            m = rx.search(body)
            if m:
                findings.append(f'{path}:{i}: {rule} term "{m.group(1)}" in an added line of {current}: {body.strip()[:120]}')
        if any(ord(c) > 126 for c in body):
            findings.append(f'{path}:{i}: format: non-ASCII character in an added line of {current}')
        if CTRL_RX.search(body.replace('\t', '')):
            findings.append(f'{path}:{i}: format: control character in an added line of {current}')
    if files == 0:
        findings.append(f'{path}:0: format: no "diff --git" header (not a git-style patch)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--patch', action='append', default=[])
    ap.add_argument('--message-file', action='append', default=[])
    ap.add_argument('--commits', default='')
    ap.add_argument('--git-dir', default='.')
    ap.add_argument('--terms', action='store_true')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    if a.terms:
        print('names:', ', '.join(terms(NAMES_B64)))
        print('licence:', ', '.join(terms(LICENCE_B64)))
        return 0
    if not (a.patch or a.message_file or a.commits):
        print('cleanroom_lint: nothing to check (--patch / --message-file / --commits)', file=sys.stderr)
        return 2
    findings = []
    for p in a.patch:
        scan_patch(p, findings)
    for f in a.message_file:
        try:
            scan_text(f, open(f, encoding='utf-8', errors='replace').read(), findings)
        except OSError as e:
            print(f'cleanroom_lint: cannot read {f}: {e}', file=sys.stderr)
            return 2
    if a.commits:
        r = subprocess.run(['git', '-C', a.git_dir, 'log', '--format=%H%n%B%n--END--', a.commits],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            print(f'cleanroom_lint: git log failed: {r.stderr.strip()}', file=sys.stderr)
            return 2
        for block in r.stdout.split('--END--'):
            lines = block.strip().splitlines()
            if lines:
                scan_text(f'commit {lines[0][:12]}', '\n'.join(lines[1:]), findings)
    for f in findings:
        print(f)
    verdict = 'CLEAN' if not findings else f'FINDINGS {len(findings)}'
    print(f'cleanroom_lint: {verdict} (patches {len(a.patch)}, message files {len(a.message_file)}, commits '
          f'{a.commits or "-"})')
    if a.json:
        with open(a.json, 'w', newline='\n') as fh:
            json.dump({'tool': 'cleanroom_lint.py', 'verdict': verdict, 'findings': findings, 'patches': a.patch,
                       'commits': a.commits}, fh, indent=1)
            fh.write('\n')
    return 0 if not findings else 1


if __name__ == '__main__':
    sys.exit(main())
