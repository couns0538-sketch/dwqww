#!/usr/bin/env python3
"""mutation_check_s38.py (S38, opus 2026-10-27): planted-bug check. Each mutant is the tool with ONE deliberate bug
(an exact-once text edit); the full test suite must FAIL on every mutant and PASS on the original.
Mutant copies and test scratch go to --scratch (never into the repository). Usage:
  python -I -B mutation_check_s38.py --scratch F:\\opus_scratch\\sol_s38\\mut"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, 'forge_sol_S38_gate_time_audit_20261027.py')
TESTS = os.path.join(HERE, 'test_gate_time_audit.py')
MUTANTS = [
    ('M01 percentile off by one', "return sorted_vals[max(1, math.ceil(p / 100.0 * len(sorted_vals))) - 1]",
     "return sorted_vals[min(len(sorted_vals) - 1, math.ceil(p / 100.0 * len(sorted_vals)))]"),
    ('M02 soft limit ignores the increment', "soft = available // self.soft_div + max(0, inc_ms) * self.inc_pct // 100",
     "soft = available // self.soft_div"),
    ('M03 clock starts at base without the first increment', "(base_ms + inc_ms if base_ms is not None else None)",
     "(base_ms if base_ms is not None else None)"),
    ('M04 loser taken from the wrong side', "return {'1-0': 'b', '0-1': 'w'}.get(result)", "return {'1-0': 'w', '0-1': 'b'}.get(result)"),
    ('M05 first info line instead of the last', "                    st['last'] = rest\n", "                    st['last'] = st['last'] or rest\n"),
    ('M06 nps min-ms filter dropped', "if tms >= min_ms:", "if tms >= 0:"),
    ('M07 time losses counted as crashes', "        return 'tl'\n", "        return 'crash'\n"),
    ('M08 position ply counts the word moves', "return base + (len(rest) - 1 if rest and rest[0] == 'moves' else 0)",
     "return base + (len(rest) if rest and rest[0] == 'moves' else 0)"),
    ('M09 phase band boundary inclusive', "        if ply < b:\n", "        if ply <= b:\n"),
    ('M10 asymmetry threshold doubled', "        if asym > a.asym:\n", "        if asym > a.asym * 2:\n"),
    ('M11 log TL regex broken', "EV_TL = re.compile(r'loses on time', re.I)", "EV_TL = re.compile(r'loses on tiem', re.I)"),
    ('M12 per-game nps not keyed by engine', "games.setdefault((name, st['game']), [])", "games.setdefault(('x', st['game']), [])"),
]


def run_tests(tool, scratch):
    env = dict(os.environ, S38_TOOL=tool, S38_SCRATCH=scratch)
    p = subprocess.run([sys.executable, '-I', '-B', TESTS], env=env, capture_output=True, text=True)
    tail = [l for l in p.stderr.splitlines() if l.startswith(('FAILED', 'OK', 'Ran '))]
    return p.returncode, ' | '.join(tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scratch', required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    src = open(TOOL, encoding='utf-8').read()
    code, tail = run_tests(TOOL, a.scratch)
    print(f'original tool: tests exit {code} ({tail})')
    bad = 0 if code == 0 else 1
    for name, old, new in MUTANTS:
        n = src.count(old)
        if n != 1:
            print(f'{name}: SETUP ERROR, pattern found {n} times')
            bad += 1
            continue
        mp = os.path.join(a.scratch, 'mutant_' + name.split()[0] + '.py')
        with open(mp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.replace(old, new))
        code, tail = run_tests(mp, a.scratch)
        caught = code != 0
        bad += 0 if caught else 1
        print(f'{name}: {"CAUGHT" if caught else "NOT CAUGHT"} (tests exit {code}; {tail})')
    print(f'mutation check: {"PASS" if bad == 0 else "FAIL"} ({len(MUTANTS)} mutants)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
