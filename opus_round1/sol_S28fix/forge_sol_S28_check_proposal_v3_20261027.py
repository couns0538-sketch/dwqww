"""Check the S28-1 v3 AL1 s198 pin proposal against the observations (PROPOSAL ONLY; nothing is applied).

usage: python -I -B forge_sol_S28_check_proposal_v3_20261027.py PROPOSAL.patch OBSERVATION.json [FORGE_TESTS_STDERR]
PASS requires: only tests/tests.cpp, tools/rerecord_pins.py, README.md, IDEA_SOURCE.md change; the new WAC pin
(move/score/depth 12) and both king pins in tests.cpp and in rerecord_pins.py equal the UCI observation; the
6.4.24 expectations and the KNOWN_FAILURE output text are not removed or changed; and, if given, every
PIN_MISMATCH line of the un-patched forge_tests run reports exactly the proposed values as 'observed'.
"""
import json
import re
import sys
from pathlib import Path

ALLOWED = {'tests/tests.cpp', 'tools/rerecord_pins.py', 'README.md', 'IDEA_SOURCE.md'}


def files_and_lines(patch):
    files, added, removed, cur = set(), {}, {}, None
    for line in patch.splitlines():
        m = re.match(r'^\+\+\+ b/(\S+)', line)
        if m:
            cur = m.group(1)
            files.add(cur)
            continue
        if line.startswith('--- ') or line.startswith('diff --git') or line.startswith('@@'):
            continue
        if line.startswith('+'):
            added.setdefault(cur, []).append(line[1:])
        elif line.startswith('-'):
            removed.setdefault(cur, []).append(line[1:])
    return files, added, removed


def check(patch_text, obs, stderr_text=None):
    problems = []
    o = {c['case']: c for c in obs['cases']}
    w, pw, pb = o['WAC001'], o['promotion_white'], o['promotion_black']
    files, added, removed = files_and_lines(patch_text)
    if files - ALLOWED:
        problems.append('patch touches files outside the pin scope: %s' % sorted(files - ALLOWED))
    t_add = '\n'.join(added.get('tests/tests.cpp', []))
    want = {'documented_wac_move': '"%s"' % w['bestmove'], 'documented_wac_score': str(w['score'])}
    for name, value in want.items():
        m = re.search(r'%s = ([^;]+);' % name, t_add)
        current = m.group(1) if m else None
        if current is None:
            # unchanged line: must already equal the observation in the un-patched tree (f6h5 move)
            if name == 'documented_wac_move' and w['bestmove'] == 'f6h5':
                continue
            problems.append('tests.cpp: %s not re-recorded' % name)
        elif current != value:
            problems.append('tests.cpp: %s = %s, observed %s' % (name, current, value))
    m = re.search(r'documented_king_text = mirrored \? "(\w+)" : "(\w+)";', t_add)
    if not m or (m.group(1), m.group(2)) != (pb['bestmove'], pw['bestmove']):
        problems.append('tests.cpp: king pins %s != observed %s/%s' % (m.groups() if m else None, pb['bestmove'], pw['bestmove']))
    r_add = '\n'.join(added.get('tools/rerecord_pins.py', []))
    cases = dict((c[0], c) for c in re.findall(r"\('(\w+)','[^']*',(\d+),(\d+),'(\w+)',(\w+)\)", r_add))
    exp = {'WAC001': ('12', '8', w['bestmove'], str(w['score'])), 'promotion_white': ('1', '1', pw['bestmove'], 'None'),
           'promotion_black': ('1', '1', pb['bestmove'], 'None')}
    for k, v in exp.items():
        if k not in cases or cases[k][1:] != v:
            problems.append('rerecord_pins.py: %s = %s, observed %s' % (k, cases.get(k), v))
    gone = '\n'.join(sum(removed.values(), []))
    for keep in ('"WAC 001", "2rr3k', 'MateValue - 3', 'c7c8r', 'c2c1r', 'h256_e12 net-evaluation horizon'):
        if keep in gone and keep not in '\n'.join(sum(added.values(), [])):
            problems.append('protected text removed: %s' % keep)
    if stderr_text is not None:
        pins = re.findall(r'^PIN_MISMATCH: (WAC 001|unrestricted promotion) documented (\S+?)/.*?, observed (\w+)/(-?\d+)/d(\d+)/PV=(\w+);',
                          stderr_text, re.M)
        if len(pins) != 3:
            problems.append('expected 3 PIN_MISMATCH lines in the un-patched forge_tests run, found %d' % len(pins))
        for kind, documented, move, score, depth, pv in pins:
            if kind == 'WAC 001':
                ok = (move, int(score), int(depth), pv) == (w['bestmove'], w['score'], 12, w['bestmove'])
            else:
                target = pw if documented == 'c6d7' else pb
                ok = (move, int(score), int(depth), pv) == (target['bestmove'], target['score'], 1, target['bestmove'])
            if not ok:
                problems.append('forge_tests observed %s %s/%s/d%s differs from the UCI observation' % (kind, move, score, depth))
    return problems


def main():
    patch = Path(sys.argv[1]).read_text(encoding='utf-8')
    obs = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    stderr = Path(sys.argv[3]).read_text(encoding='utf-8', errors='replace') if len(sys.argv) > 3 else None
    p = check(patch, obs, stderr)
    print(json.dumps({'status': 'PASS' if not p else 'FAIL', 'problems': p}, indent=1))
    return 0 if not p else 1


if __name__ == '__main__':
    raise SystemExit(main())
