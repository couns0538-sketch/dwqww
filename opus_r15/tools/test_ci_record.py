#!/usr/bin/env python3
"""test_ci_record.py OUT_DIR - self-test of ci_record.py (needs gh and the branch's CI history; --dry-run only, so
nothing is written outside OUT_DIR). Cases: the newest green run ties the real C1 record (exit 0); a copy of the C1
record whose patch_sha256 was changed is refused (exit 1); a record naming a patch that is not in the run's commit is
refused (exit 1); a cancelled run is refused (exit 2). Exit 0 = every case as expected.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
if os.path.exists(out):
    sys.exit(f'refusing existing {out}')
os.makedirs(out)
src = json.load(open(r'D:\o15\cands\c1_prunelmrhist\RESULT.json', encoding='utf-8-sig'))


def root_with(name, rec):
    d = os.path.join(out, name, rec['name'])
    os.makedirs(d)
    json.dump(rec, open(os.path.join(d, 'RESULT.json'), 'w'))
    return os.path.join(out, name)


good = root_with('good', dict(src))
bad_sha = root_with('bad_sha', dict(src, patch_sha256='0' * 64))
missing = root_with('missing', dict(src, name='c9_not_in_branch'))
runs = json.loads(subprocess.run(['gh', 'run', 'list', '--branch', 'opus-r15-20261103', '--limit', '30', '--json',
                                  'databaseId,conclusion,status'], cwd=r'D:\o15\wt', capture_output=True, text=True).stdout)
cancelled = [str(r['databaseId']) for r in runs if r['conclusion'] == 'cancelled']
cases = [('green_run_ties_c1', ['--root', good], 0), ('changed_patch_sha_refused', ['--root', bad_sha], 1),
         ('patch_not_in_commit_refused', ['--root', missing], 1)]
if cancelled:
    cases.append(('cancelled_run_refused', ['--root', good, '--run', cancelled[0]], 2))
fails = 0
for name, args, want in cases:
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'ci_record.py'), '--dry-run',
                        '--evidence-dir', out] + args, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1]
    if r.returncode == want:
        print(f'PASS {name} (exit {r.returncode}): {last[:120]}')
    else:
        fails += 1
        print(f'FAIL {name}: exit {r.returncode}, want {want}: {r.stdout.strip()[:300]} {r.stderr.strip()[:200]}')
print(f'{len(cases) - fails} / {len(cases)} cases as expected')
print('ALL PASS' if fails == 0 else f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
