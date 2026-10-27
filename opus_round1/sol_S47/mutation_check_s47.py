#!/usr/bin/env python3
"""mutation_check_s47.py (S47, opus 2026-10-27): planted-bug check. Each mutant is Part A or Part B with ONE deliberate
bug (an exact-once edit); the full test suite must FAIL on every mutant and PASS on the originals. Mutants and test
scratch go to --scratch (never into the repository). Usage: python -I -B mutation_check_s47.py --scratch <dir>"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = {'S47_PARTA': os.path.join(HERE, 'forge_sol_S47_verify_netonly_tree_20261027.py'),
         'S47_PARTB': os.path.join(HERE, 'forge_sol_S47_autolock_audit_20261027.py')}
MUTANTS = [
    ('S47_PARTA', 'A1 CRLF->LF normalisation dropped', r"hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest())", "hashlib.sha256(b).hexdigest())"),
    ('S47_PARTA', 'A2 net md5 not checked', "        if not net['match']:\n", "        if False:\n"),
    ('S47_PARTA', 'A3 extra candidate files ignored', " + [f'only in candidate: {x}' for x in only_c]", ""),
    ('S47_PARTA', 'A4 Z-1 check off', "        if rb and non_net:\n", "        if False:\n"),
    ('S47_PARTA', 'A5 AUTOLOCK dir layout not detected', "    if os.path.isdir(os.path.join(d, 'source', 'src')):\n", "    if False:\n"),
    ('S47_PARTB', 'B1 pin allow-list accepts any md5', "                    bad.append(f'{f} md5 {md} is neither unchanged nor an allow-listed reviewed diff (edited pin?)')",
     "                    ev.append(f'{f} md5 {md} is neither unchanged nor an allow-listed reviewed diff (edited pin?)')"),
    ('S47_PARTB', 'B2 bench compares only d11/d13', "        elif runs and runs[0] != exp:\n", "        elif runs and runs[0][:2] != exp[:2]:\n"),
    ('S47_PARTB', 'B3 confirm srand reuse not checked', "'confirm reuses the gate srand' if gs == cs else ''", "''"),
    ('S47_PARTB', 'B4 old lock files not re-hashed', "                elif h(p, 'md5' if len(want) == 32 else 'sha256') != want:\n", "                elif False:\n"),
    ('S47_PARTB', 'B5 VOID read as H1', "        return 'VOID'\n    m = re.search(r'\*\*Verdict", "        return 'H1 accepted'\n    m = re.search(r'\*\*Verdict"),
    ('S47_PARTB', 'B6 MISSING counted as pass', "overall = 'FAIL' if 'FAIL' in st else 'INCOMPLETE' if 'MISSING' in st else 'ALL_CHECKS_PASS'",
     "overall = 'FAIL' if 'FAIL' in st else 'ALL_CHECKS_PASS'"),
    ('S47_PARTB', 'B7 orphan lower-n dir check off', "            if orphans:\n", "            if False:\n"),
    ('S47_PARTB', 'B8 tests/ pin tree not compared', "            if td:\n", "            if False:\n"),
]


def run_tests(env_over, scratch):
    env = dict(os.environ, S47_SCRATCH=scratch, **env_over)
    p = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'test_autolock_audit.py')], env=env, capture_output=True, text=True)
    return p.returncode, ' | '.join(l for l in p.stderr.splitlines() if l.startswith(('FAILED', 'OK', 'Ran ')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scratch', required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    code, tail = run_tests({}, a.scratch)
    print(f'originals: tests exit {code} ({tail})')
    bad = 0 if code == 0 else 1
    for env, name, old, new in MUTANTS:
        src = open(TOOLS[env], encoding='utf-8').read()
        n = src.count(old)
        if n != 1:
            print(f'{name}: SETUP ERROR, pattern found {n} times')
            bad += 1
            continue
        mp = os.path.join(a.scratch, f'mutant_{name.split()[0]}.py')
        with open(mp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.replace(old, new))
        code, tail = run_tests({env: mp}, a.scratch)
        bad += 0 if code != 0 else 1
        print(f'{name}: {"CAUGHT" if code != 0 else "NOT CAUGHT"} (tests exit {code}; {tail})')
    print(f'mutation check: {"PASS" if bad == 0 else "FAIL"} ({len(MUTANTS)} mutants)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
