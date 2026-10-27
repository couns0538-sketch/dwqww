"""Planted-bug check for S33 v2: each mutant breaks one rule of the labels tool; the test suite must FAIL on it.

usage: python -I -B forge_sol_S33_mutants_v2_20261027.py <NEW scratch dir outside git>
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = 'forge_sol_S33_labels_v2_20261027.py'
TEST = 'test_forge_sol_S33_labels_v2_20261027.py'
MUTANTS = [
    ('label rule disabled (every table accepted)',
     "        if LABEL in header.lower() or LABEL in caption or 'fastchess-printed' in caption:\n",
     "        if True:\n"),
    ('caption label not searched (header only)',
     "        if LABEL in header.lower() or LABEL in caption or 'fastchess-printed' in caption:\n",
     "        if LABEL in header.lower() or 'fastchess-printed' in caption:\n"),
    ('non-fastchess LLR accepted',
     "                if v.group(1) != figs[gate]['llr']:\n",
     "                if False:\n"),
    ('renderer drops the caption',
     "          'job FILES.txt); only the labels are new (QA fix-up S33-1). Modeled trials only, not played games. No observed '\n"
     "          'gates or concurrency groups pooled.', '', CAPTION, '',\n",
     "          'job FILES.txt); only the labels are new (QA fix-up S33-1). Modeled trials only, not played games. No observed '\n"
     "          'gates or concurrency groups pooled.', '',\n"),
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
        env = dict(os.environ, S33_LABELS_DIR=str(d), PYTHONDONTWRITEBYTECODE='1')
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
