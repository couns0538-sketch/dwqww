"""Fable 2026-11-23, W5: the test of the test. test_worker.py passed on its first run, so it has to show that it
CAN fail: each mutant is a copy of the package with ONE planted change in run/worker.py, and the named checks of
test_worker.py must FAIL on it. A control copy without a change must pass the same cases.

    mutants.py <engine exe> <net file> <serverday folder> <NEW work folder>

Exit 0: the control passes and every mutant is caught by every check named for it. Exit 1 otherwise.
What this does NOT show: that a fault outside these six is caught.
"""
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 5:
    print(__doc__)
    sys.exit(2)
EXE, NET, SD, WORK = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
if WORK.exists():
    print(f"STOP: {WORK} exists already")
    sys.exit(2)

MUTANTS = [
    # name, cases to run, the text that is replaced (must stand exactly once), its replacement, checks that must FAIL
    ("the written position line is not compared with the reservation", "T9",
     'if pos[0].split(" ") != record.position_tokens(moves):', "if False:",
     ["T9 the final writes exchanged between two workers", "T9 plant mvoes:1", "T9 plant cut2:1", "T9 after a restart"]),
    ("a game written but not journalled is not cut off", "T4",
     "f.truncate(end)", "pass",
     ["T4a a half-written third game: pieces byte for byte"]),
    ("no ucinewgame before a game", "T1",
     'if planted != "no_newgame":', "if False:",
     ["T1 six games, each as the known answers"]),
    ("the start-up search is not compared with the known answers", "T6",
     "if got != want:", "if False:",
     ["T6 refused, exit 5, reason named: Hash 32 instead of 16", "T6 refused, exit 5, reason named: a known answer with one node more"]),
    ("the list of sent lines is never emptied", "T1",
     "self.eng.sent.clear()                           # nothing of an earlier game is kept (memory, and A23)", "pass",
     ["T1 no sent line is kept from game to game"]),
    ("a closing that was cut off is not finished", "T4",
     "if end and not piece.exists() and moved.exists() and moved.stat().st_size == end:", "if False:",
     ["T4d ended inside the closing (piece moved, no line in the journal): exit code 0"]),
]


def copy_of(name: str) -> Path:
    dst = WORK / name / "serverday"
    for sub in ("run", "tests", "workloads", "known"):
        shutil.copytree(SD / sub, dst / sub, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def run(sd: Path, cases: str, out: Path):
    p = subprocess.run([sys.executable, "-I", "-B", str(sd / "tests" / "test_worker.py"), EXE, NET, str(sd), str(out), "only=" + cases],
                       capture_output=True, text=True, timeout=1800)
    lines = (p.stdout + p.stderr).splitlines()
    return p.returncode, [ln[5:] for ln in lines if ln.startswith("FAIL ")], lines


bad = 0
sd = copy_of("control")
rc, fails, lines = run(sd, "T1,T4,T6,T9", WORK / "control" / "out")
ok = rc == 0 and not fails
bad += not ok
print(f"{'ok  ' if ok else 'FAIL'} control (no change), cases T1 T4 T6 T9: exit {rc}, {lines[-1] if lines else ''}", flush=True)
for k, (name, cases, old, new, must_fail) in enumerate(MUTANTS, 1):
    sd = copy_of(f"m{k}")
    f = sd / "run" / "worker.py"
    t = f.read_text(encoding="utf-8")
    if t.count(old) != 1:
        print(f"FAIL mutant {k} ({name}): the text to replace stands {t.count(old)} times in worker.py, not once")
        bad += 1
        continue
    f.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
    rc, fails, lines = run(sd, cases, WORK / f"m{k}" / "out")
    missed = [m for m in must_fail if not any(x.startswith(m) for x in fails)]
    ok = rc == 1 and not missed
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} mutant {k} CAUGHT: {name}: cases {cases}, exit {rc}, {len(fails)} checks failed"
          + (f"; NOT failed although named: {missed}" if missed else "") + (f"; last line: {lines[-1][:200]}" if rc != 1 and lines else ""), flush=True)
print("CONTROL PASSES AND ALL 6 MUTANTS ARE CAUGHT" if not bad else f"NOT ALL: {bad} of 7 lines are FAIL")
sys.exit(1 if bad else 0)
