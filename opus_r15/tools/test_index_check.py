#!/usr/bin/env python3
"""test_index_check.py OUT_DIR - self-test of index_check.py on copies of the C1 record (the real C1 exe is only read).

Variants of one RESULT.json in their own roots: unchanged -> OK; wrong exe sha256, a failed check, missing ci.json,
red CI, an option the exe does not advertise, an ON value outside the option's range -> FAIL; an empty root -> exit 2.
Exit 0 = every case as expected.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'D:\o15\cands\c1_prunelmrhist'
out = sys.argv[1]
if os.path.exists(out):
    sys.exit(f'refusing existing {out}')
base = json.load(open(os.path.join(SRC, 'RESULT.json'), encoding='utf-8-sig'))
ci = json.load(open(os.path.join(SRC, 'ci.json'), encoding='utf-8-sig'))


def make(name, edit=None, ci_edit=None, with_ci=True):
    root = os.path.join(out, name)
    d = os.path.join(root, 'c1_copy')
    os.makedirs(d)
    r = json.loads(json.dumps(base))
    if edit:
        edit(r)
    json.dump(r, open(os.path.join(d, 'RESULT.json'), 'w'), indent=1)
    if with_ci:
        c = dict(ci)
        if ci_edit:
            ci_edit(c)
        json.dump(c, open(os.path.join(d, 'ci.json'), 'w'))
    return root


cases = [
    ('unchanged', make('unchanged'), 0),
    ('wrong_sha', make('wrong_sha', lambda r: r.update(exe_sha256='0' * 64)), 1),
    ('failed_check', make('failed_check', lambda r: r['checks']['smoke'].update(ok=False)), 1),
    ('missing_ci', make('missing_ci', with_ci=False), 1),
    ('red_ci', make('red_ci', ci_edit=lambda c: c.update(conclusion='failure')), 1),
    ('not_advertised', make('not_advertised', lambda r: r.update(option='NoSuchOption')), 1),
    ('on_out_of_range', make('on_out_of_range', lambda r: r.update(on='5')), 1),
]
os.makedirs(os.path.join(out, 'empty_root'))
cases.append(('empty_root', os.path.join(out, 'empty_root'), 2))
fails = 0
for name, root, want in cases:
    p = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'index_check.py'), '--root', root],
                       capture_output=True, text=True)
    last = (p.stdout.strip().splitlines() or p.stderr.strip().splitlines() or [''])[-1]
    if p.returncode == want:
        print(f'PASS {name} (exit {p.returncode}): {last}')
    else:
        fails += 1
        print(f'FAIL {name}: exit {p.returncode}, want {want}: {p.stdout.strip()[:300]} {p.stderr.strip()[:200]}')
print(f'{len(cases) - fails} / {len(cases)} cases as expected')
print('ALL PASS' if fails == 0 else f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
