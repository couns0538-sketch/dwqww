"""Planted-bug check for the S06 v2 fix-ups: copy the job folder to a NEW scratch directory, plant one bug
per mutant (a Python str.replace that must match exactly once), run test_forge_sol_S06_v2_fixups.py and
require at least one failing test per mutant. Never touches the job folder itself.
usage: python mutation_check_v2.py --out NEW_SCRATCH_DIR"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MUTANTS = [
    ('S06-1 t-value without sqrt(2) (WDL formula used for pentanomial)', 'forge_sol_S06_statistics_v2.py',
     't0 = math.sqrt(2.0) * e0 / (800.0 / math.log(10))', 't0 = e0 / (800.0 / math.log(10))'),
    ('S06-1 Gaussian LLR drives the Wald decision', 'forge_sol_S06_statistics_v2.py',
     "wald['decision'] = ('accept_h0_diagnostic' if exact <= wald['lower'] else",
     "exact = gaussian\n    wald['decision'] = ('accept_h0_diagnostic' if exact <= wald['lower'] else"),
    ('S06-1 no zero-count regularization', 'forge_sol_S06_statistics_v2.py',
     'regularized = [1e-3 if c == 0 else float(c) for c in counts]', 'regularized = [float(c) for c in counts]'),
    ('S06-1 Elo error from the delta method instead of the score interval', 'forge_sol_S06_statistics_v2.py',
     "result['fastchess_display']['elo_error95'] = _finite((transformed[1] - transformed[0]) / 2.0)",
     "result['fastchess_display']['elo_error95'] = _finite((400.0 / (_LOG10 * mean * (1.0 - mean))) * standard_error * _Z95)"),
    ('S06-2 book moves ignored (fastchess PGN openings unknown)', 'forge_sol_S06_pgn_v2.py',
     'if not depth and moves and value.strip().casefold() == "book":', 'if False:'),
    ('S06-2 orphan game blocks like a broken pair', 'forge_sol_S06_pgn_v2.py',
     'orphan = len(games) == 1 and not round_issues', 'orphan = False'),
    ('S06-2 log summary must equal all finished games', 'forge_sol_S06_logs_v2.py',
     "elif 2 * len(complete) == reported['games'] and complete_wdl == reported['wdl'] and not unknown_pairs:",
     'elif False:'),
    ('S06-2 time losses not compared', 'forge_sol_S06_gatelog_miner_v2.py',
     "comparisons.append(_compare('time_losses', sources(", "(_compare('time_losses', sources("),
    ('S06-3 missing Termination counted as normal', 'forge_sol_S06_pgn_v2.py',
     'return (game["termination"] or "").strip().casefold() == "normal"',
     'return (game["termination"] or "normal").strip().casefold() == "normal"'),
    ('S06-3 second PGN dropped', 'forge_sol_S06_pgn_v2.py',
     'records = [(source, record) for source, text in enumerate(texts) for record in _parse(text)]',
     'records = [(source, record) for source, text in enumerate(texts[:1]) for record in _parse(text)]'),
    ('S06-3 --out guard ignores gate/lock/queue path components', 'forge_sol_S06_gatelog_miner_v2.py',
     'if _PROTECTED_COMPONENT.search(part.strip', 'if False and _PROTECTED_COMPONENT.search(part.strip'),
    ('S06-3 --out guard ignores the default protected roots', 'forge_sol_S06_gatelog_miner_v2.py',
     'roots = list(DEFAULT_PROTECTED) + list(extra_protected)', 'roots = list(extra_protected)'),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(exist_ok=False)
    survivors = 0
    for number, (label, target, old, new) in enumerate(MUTANTS, 1):
        work = args.out / f'mutant_{number:02d}'
        shutil.copytree(HERE, work, ignore=shutil.ignore_patterns('__pycache__', 'logs'))
        path = work / target
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, (label, text.count(old))
        path.write_text(text.replace(old, new), encoding='utf-8')
        run = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_forge_sol_S06_v2_fixups'],
                             cwd=work, capture_output=True, text=True, timeout=600)
        tail = [line for line in run.stderr.splitlines() if line.startswith(('FAILED', 'OK', 'Ran '))]
        failing = sorted({line.split('(')[0].replace('FAIL: ', '').replace('ERROR: ', '').strip()
                          for line in run.stderr.splitlines() if line.startswith(('FAIL:', 'ERROR:'))})
        caught = run.returncode != 0
        survivors += not caught
        print(f"{'CAUGHT ' if caught else 'SURVIVED'} mutant {number:02d}: {label} | {' '.join(tail)} | "
              f"failing: {', '.join(failing)}", flush=True)
    print(f'{len(MUTANTS) - survivors}/{len(MUTANTS)} mutants caught')
    return 1 if survivors else 0


if __name__ == '__main__':
    raise SystemExit(main())
