"""Planted-bug check for S48 v2: each mutant re-introduces one fixed defect; the test suite must FAIL on it.

usage: python -I -B forge_sol_S48_mutants_v2_20261027.py <NEW scratch dir outside git>
Each mutant is a copy of forge_sol_S48_gate_guard_v2_20261027.py with exactly one replaced line (the pattern
must occur once); the unchanged test file runs against it via S48_GUARD_DIR. Exit 0 only if every mutant fails.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = 'forge_sol_S48_gate_guard_v2_20261027.py'
TEST = 'test_forge_sol_S48_gate_guard_v2_20261027.py'
MUTANTS = [
    ('S48-1 silent e0/e1 defaults restored',
     "    e0, e1 = _required(gate, 'e0'), _required(gate, 'e1')\n",
     "    e0, e1 = gate.get('e0', 0), gate.get('e1', 10)\n"),
    ('S48-2 cap no longer compared',
     "REQUIRED = ('concurrency', 'tc', 'book_sha256', 'base_exe_sha256', 'core_mask', 'sprt', 'cap_games')\n",
     "REQUIRED = ('concurrency', 'tc', 'book_sha256', 'base_exe_sha256', 'core_mask', 'sprt')\n"),
    ('S48-2 replicate may reuse the openings seed',
     "        elif seed['equal']:\n",
     "        elif False:\n"),
    ('S48-3 hash_mb rejects "64MB" again',
     "    m = re.fullmatch(r'\\s*([0-9]+)\\s*(MB|MIB|M|GB|GIB|G)?\\s*', value.upper())\n",
     "    m = re.fullmatch(r'([0-9]+)()', value)\n"),
    ('S48-3 tc prefix not normalized',
     "    if t.lower().startswith('tc='):\n",
     "    if False:\n"),
    ('S48-4 git guard disabled',
     "    if tree is not None and not allow_git:\n",
     "    if False:\n"),
]


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = (HERE / GUARD).read_text(encoding='utf-8')
    rows, ok = [], True
    for i, (name, old, new) in enumerate(MUTANTS):
        if source.count(old) != 1:
            raise SystemExit('pattern must occur exactly once: ' + name)
        d = out / ('m%d' % i)
        d.mkdir()
        (d / GUARD).write_text(source.replace(old, new), encoding='utf-8', newline='\n')
        env = dict(os.environ, S48_GUARD_DIR=str(d), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([sys.executable, '-I', '-B', str(HERE / TEST)], env=env, capture_output=True, text=True)
        (d / 'test_output.txt').write_text(p.stdout + p.stderr, encoding='utf-8')
        last = [l for l in (p.stdout + p.stderr).splitlines() if l.startswith(('FAILED', 'OK'))]
        caught = p.returncode != 0
        ok &= caught
        rows.append((name, 'CAUGHT' if caught else 'MISSED', last[-1] if last else '?'))
    for r in rows:
        print(' | '.join(r))
    print('MUTANTS %d/%d caught' % (sum(r[1] == 'CAUGHT' for r in rows), len(rows)))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
