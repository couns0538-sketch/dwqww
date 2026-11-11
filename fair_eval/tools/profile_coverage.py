#!/usr/bin/env python3
"""profile_coverage.py - JOB D (own code, 2026-11-11).

Proof of which evaluator ran while a PGO profile was recorded, read from the merged profile itself.

  profile_coverage.py --profdata FILE --tool-dir LLVM_BIN --out JSON
                      [--must-run REGEX ...] [--must-be-zero REGEX ...] [--report REGEX ...]

`llvm-profdata show --all-functions` lists every instrumented function with its entry count. Names are
demangled with llvm-cxxfilt and matched (re.search) against the patterns. A --must-run pattern passes when
at least one matching function has a non-zero entry count; a --must-be-zero pattern passes when every
matching function has count 0 (a pattern that matches nothing fails either way: the name list is wrong).
Exit 0 = all patterns pass, 1 = a pattern fails, 2 = the tools could not be run.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profdata', required=True)
    ap.add_argument('--tool-dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--must-run', nargs='*', default=[])
    ap.add_argument('--must-be-zero', nargs='*', default=[])
    ap.add_argument('--report', nargs='*', default=[])
    a = ap.parse_args()
    show = subprocess.run([os.path.join(a.tool_dir, 'llvm-profdata.exe'), 'show', '--all-functions', a.profdata],
                          capture_output=True, text=True)
    if show.returncode != 0:
        print(show.stderr, file=sys.stderr)
        return 2
    raw = []  # (profile name, count)
    name = None
    for line in show.stdout.splitlines():
        m = re.match(r'^  (\S.*):$', line)
        if m:
            name = m.group(1)
            continue
        m = re.match(r'^\s+Function count:\s+(\d+)', line)
        if m and name is not None:
            raw.append((name, int(m.group(1))))
            name = None
    # internal-linkage functions carry a "file;" or "file:" prefix before the mangled name
    mangled = [re.sub(r'^.*[;:](?=_Z)', '', n) for n, _ in raw]
    filt = subprocess.run([os.path.join(a.tool_dir, 'llvm-cxxfilt.exe')], input='\n'.join(mangled) + '\n',
                          capture_output=True, text=True)
    demangled = filt.stdout.splitlines() if filt.returncode == 0 else mangled
    if len(demangled) != len(raw):
        demangled = mangled
    funcs = [(d, c) for d, (_, c) in zip(demangled, raw)]
    result = {'profdata': a.profdata, 'functions_in_profile': len(funcs),
              'functions_with_nonzero_count': sum(1 for _, c in funcs if c > 0), 'checks': [], 'pass': True}

    def check(pattern, kind):
        hits = [(d, c) for d, c in funcs if re.search(pattern, d)]
        if kind == 'must_run':
            ok = any(c > 0 for _, c in hits)
        elif kind == 'must_be_zero':
            ok = bool(hits) and all(c == 0 for _, c in hits)
        else:
            ok = True
        result['checks'].append({'kind': kind, 'pattern': pattern, 'pass': ok,
                                 'matches': [{'function': d, 'entry_count': c} for d, c in hits]})
        if not ok:
            result['pass'] = False
        for d, c in hits:
            print(f'{kind:13s} {"PASS" if ok else "FAIL"} count {c:>12d}  {d[:110]}')
        if not hits:
            print(f'{kind:13s} {"PASS" if ok else "FAIL"} no function matches {pattern}')

    for p in a.must_run:
        check(p, 'must_run')
    for p in a.must_be_zero:
        check(p, 'must_be_zero')
    for p in a.report:
        check(p, 'report')
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1)
    print(f'coverage: {"PASS" if result["pass"] else "FAIL"}; {result["functions_with_nonzero_count"]} of '
          f'{result["functions_in_profile"]} profiled functions ran')
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
