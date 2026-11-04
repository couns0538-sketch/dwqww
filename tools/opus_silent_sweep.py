#!/usr/bin/env python3
"""opus_silent_sweep.py - list every place a script swallows an error silently (R14 finish Job 4; own code).

Python (ast): an `except` handler whose body is only `pass`, `...` or `continue` (bare or typed).
PowerShell (text): an empty `catch { }` block, `-ErrorAction SilentlyContinue` / `Ignore`, `trap { continue }`.
  opus_silent_sweep.py [--root D:/a14] [--json out.json]   (skips runtime/, evidence/, .git/, tmp/)
Each finding prints file:line, the kind and the source line; exit 0 always (the list is for review).
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

SKIP = {'runtime', 'evidence', '.git', 'tmp', '__pycache__', '.pytest_cache'}
PS_PATTERNS = [
    ('ps_empty_catch', re.compile(r'catch\s*(\[[^\]]*\]\s*)?\{\s*\}', re.I)),
    ('ps_silently_continue', re.compile(r'-ErrorAction\s+(SilentlyContinue|Ignore)\b', re.I)),
    ('ps_error_action_preference', re.compile(r'\$ErrorActionPreference\s*=\s*[\'"](SilentlyContinue|Ignore)', re.I)),
    ('ps_trap_continue', re.compile(r'trap\s*(\[[^\]]*\]\s*)?\{\s*continue\s*\}', re.I)),
]


def files(root):
    for path in sorted(root.rglob('*')):
        if path.is_file() and not (set(p.name for p in path.parents) & SKIP) and path.suffix.lower() in ('.py', '.ps1', '.psm1'):
            if not any(part in SKIP for part in path.relative_to(root).parts):
                yield path


def python_findings(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [dict(line=exc.lineno or 0, kind='py_syntax_error', source=str(exc))]
    lines = text.splitlines()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            body = node.body
            silent = all(isinstance(s, (ast.Pass, ast.Continue)) or
                         (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis)
                         for s in body)
            if silent:
                kind = 'py_bare_except_silent' if node.type is None else 'py_except_silent'
                out.append(dict(line=node.lineno, kind=kind, source=lines[node.lineno - 1].strip()))
    return out


def powershell_findings(path):
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    out = []
    for kind, pattern in PS_PATTERNS:
        for m in pattern.finditer(text):
            line = text.count('\n', 0, m.start()) + 1
            out.append(dict(line=line, kind=kind, source=text.splitlines()[line - 1].strip()[:200]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default='D:/a14', type=Path)
    ap.add_argument('--json')
    a = ap.parse_args()
    findings, scanned = [], 0
    for path in files(a.root):
        scanned += 1
        found = python_findings(path) if path.suffix == '.py' else powershell_findings(path)
        for f in found:
            f['path'] = str(path)
            findings.append(f)
            print(f"{path}:{f['line']}: {f['kind']}: {f['source']}")
    print(f'scanned {scanned} scripts, {len(findings)} findings')
    if a.json:
        with open(a.json, 'x', encoding='utf-8', newline='\n') as stream:
            json.dump(dict(scanned=scanned, findings=findings), stream, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
