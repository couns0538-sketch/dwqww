"""Planted-bug check for S25 v2: each mutant re-introduces one fixed defect; the test suite must FAIL on it.

usage: python -I -B forge_sol_S25_mutants_v2_20261027.py <NEW scratch dir outside git>
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = 'forge_sol_S25_outcontract_v2_20261027.py'
TEST = 'test_forge_sol_S25_outcontract_v2_20261027.py'
MUTANTS = [
    ('S25-1 UCI skipped after a bench problem (v1 gate)',
     "    uci = inspect_uci(stdout, stderr, code, approved, allow_expose, to)\n",
     "    uci = inspect_uci(stdout, stderr, code, approved, allow_expose, to) if all(b['status'] == 'PASS' for b in benches) else {'status': 'UNVERIFIED', 'errors': []}\n"),
    ('S25-1 pin mismatch counted as PASS',
     "    status = 'FAIL' if errors else ('PIN_MISMATCH' if pin else 'PASS')\n",
     "    status = 'FAIL' if errors else 'PASS'\n"),
    ('S25-1 default pins back to Sol dev base',
     "    p.add_argument('--ref', default='AL1',",
     "    p.add_argument('--ref', default='Lprime',"),
    ('S25-2 L4 no process timeout',
     "        stdout, stderr = child.communicate(stdin, timeout=timeout)\n",
     "        stdout, stderr = child.communicate(stdin)\n"),
    ('S25-2 L5 temp directory not cleaned up',
     "    if not kept:\n        remove_owned(out, token)\n",
     "    if False:\n        remove_owned(out, token)\n"),
    ('S25-2 L6 --allow-expose accepts any option type',
     "        if allow_expose and actual[name]['type'] == 'spin':\n",
     "        if allow_expose:\n"),
]


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = (HERE / MOD).read_text(encoding='utf-8')
    rows, ok = [], True
    for i, (name, old, new) in enumerate(MUTANTS):
        if source.count(old) != 1:
            raise SystemExit('pattern must occur exactly once: ' + name)
        d = out / ('m%d' % i)
        d.mkdir()
        (d / MOD).write_text(source.replace(old, new), encoding='utf-8', newline='\n')
        (d / 'forge_sol_S25_options_v2_20261027.json').write_bytes((HERE / 'forge_sol_S25_options_v2_20261027.json').read_bytes())
        env = dict(os.environ, S25_CHECKER=str(d / MOD), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([sys.executable, '-I', '-B', str(HERE / TEST)], env=env, capture_output=True, text=True)
        (d / 'test_output.txt').write_text(p.stdout + p.stderr, encoding='utf-8')
        failed = sorted({l.split(' ')[1] for l in (p.stdout + p.stderr).splitlines() if l.startswith(('FAIL: ', 'ERROR: '))})
        caught = p.returncode != 0
        ok &= caught
        rows.append((name, 'CAUGHT' if caught else 'MISSED', ','.join(failed) or '-'))
    for r in rows:
        print(' | '.join(r))
    print('MUTANTS %d/%d caught' % (sum(r[1] == 'CAUGHT' for r in rows), len(rows)))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
