"""Planted-bug check for S27 v2: each mutant re-introduces one fixed defect; test_forge_sol_S27_v2 must FAIL on it.

usage: python -I -B forge_sol_S27_mutants_v2_20261027.py <NEW scratch dir outside git>
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HYG = 'forge_sol_S27_hygiene_v2_20261027.py'
BC = 'forge_sol_S27_buildcompare_v2_20261027.py'
TEST = 'test_forge_sol_S27_v2_20261027.py'
MUTANTS = [
    ('S27-1 GNU apply without --no-backup-if-mismatch', HYG,
     "applied=run(name+'_GNU_F0_apply',['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch','-p1','-i',",
     "applied=run(name+'_GNU_F0_apply',['patch','--batch','--forward','--fuzz=0','-p1','-i',"),
    ('S27-1 per-base error aborts again', HYG,
     "    finding(exc.code,str(exc),exc.path,base=name);result['bases'].append({'name':name,'status':'ERROR','error_code':exc.code})\n",
     "    raise\n"),
    ('S27-2 default pins back to Sol dev base', BC,
     "REFS=REFSETS['AL1']  # v2 default (v1: Sol's dev base 308972/...)\n",
     "REFS=REFSETS['Lprime']\n"),
    ('S27-2 resolve_ref default back to Sol dev base', BC,
     "def resolve_ref(ref='AL1',expected_nodes=None):\n",
     "def resolve_ref(ref='Lprime',expected_nodes=None):\n"),
    ('S27-3 reviewed allowlist ignored', HYG,
     "  if approved and path in approved.get('default_code_allowed',[]):continue\n",
     "  if False:continue\n"),
    ('S27-3 v1 canonical-only --base restored', HYG,
     "  source=Path(os.path.realpath(source))  # v2 S27-3: relative/non-canonical --base accepted (realpath)\n"
     "  if not source.is_dir():raise ValueError('Base must be an existing directory: '+str(source))\n",
     "  source=Path(source).absolute()\n"
     "  if source.is_symlink() or not source.is_dir() or source.resolve()!=source:raise ValueError('Base must be a real canonical directory')\n"),
    ('portability: OS-separator inventory keys restored', HYG,
     "   result[p.relative_to(root).as_posix()]={'bytes':st.st_size,'sha256':sha_file(p)}  # v2: POSIX keys (Windows: patch targets are POSIX)\n",
     "   result[str(p.relative_to(root))]={'bytes':st.st_size,'sha256':sha_file(p)}\n"),
]


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows, ok = [], True
    for i, (name, target, old, new) in enumerate(MUTANTS):
        source = (HERE / target).read_text(encoding='utf-8')
        if source.count(old) != 1:
            raise SystemExit('pattern must occur exactly once: ' + name)
        d = out / ('m%d' % i)
        d.mkdir()
        for sibling in (HYG, BC, 'forge_sol_S27_reviewed_bugfixes_v2_20261027.json', 'forge_sol_S27_known_hashes_20261026.json'):
            (d / sibling).write_bytes((HERE / sibling).read_bytes())  # the module loads these with Path(__file__).with_name
        (d / target).write_text(source.replace(old, new), encoding='utf-8', newline='\n')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        env['S27_HYGIENE' if target == HYG else 'S27_BUILDCOMPARE'] = str(d / target)
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
