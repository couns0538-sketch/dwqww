"""Fable 2026-11-23, W5: the test of test_transfer.py (it passed on its first run). Each mutant is a copy of the
package with ONE planted change in the packer, the receiver or the record; the named checks must FAIL on it. A
control copy without a change must pass.

    mutants_transfer.py <engine exe> <net file> <converter exe> <serverday folder> <NEW work folder>

Exit 0: the control passes and every mutant is caught by every check named for it. Exit 1 otherwise.
What this does NOT show: that a fault outside these eight is caught.
"""
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 6:
    print(__doc__)
    sys.exit(2)
EXE, NET, CONV, SD, WORK = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4]).resolve(), Path(sys.argv[5]).resolve()
if WORK.exists():
    print(f"STOP: {WORK} exists already")
    sys.exit(2)

MUTANTS = [
    # name, file, cases, the text replaced (exactly once), its replacement, checks that must FAIL
    ("the receiver does not compare the piece built again with the worker's sha256", "home/receiver.py", "P7",
     "if not why and (len(raw) != raw_bytes or sha(raw) != raw_sha):", "if False:",
     ["P7 one wrong final move, every checksum of the packed files correct"]),
    ("the receiver computes no reservation of its own", "home/receiver.py", "P9",
     "bad = record.faults(g, fixed[(n - 1) % len(fixed)] if fixed else reserve(a.root_seed, gid))", "bad = record.faults(g)",
     ["P9 another root seed at the receiver"]),
    ("the receiver credits rows it has credited before", "home/receiver.py", "P4,P13",
     "elif identity in by_identity:", "elif False:",
     ["P4 the same payload under fresh ids", "P13 a pass cut off"]),
    ("the packer offers a piece without its proof", "run/packer.py", "P11",
     "if sha(again) != want:", "if False:",
     ["P11 a converter that writes one position its own way"]),
    ("the packer removes a piece on any confirmation", "run/packer.py", "P10",
     'if not words or words[0] != packed.read_text(encoding="ascii").split()[-1]:', "if False:",
     ["P10 a confirmation that names another sha256"]),
    ("the receiver does not check the checksums of the packed files", "home/receiver.py", "P6",
     "f.stat().st_size != size or sha(f.read_bytes()) != want:", "f.stat().st_size != size:",
     ["P6 one byte changed on the way: asked for again because of the checksum"]),
    ("a record's bind digest is not checked", "run/record.py", "P7,P8,P12",
     'if bind(g["id"], g["sent"], g["rows"], g["end"]) != g["bind"]:', "if False:",
     ["P7 with the piece's own sha256 forged too", "P8 the two results exchanged", "P12 the packer refuses with exit code 3 and offers nothing of it: a record"]),
    ("the receiver confirms although it was told to hold", "home/receiver.py", "P10",
     'f = state / ("held" if a.hold else "confirmed") / (key + ".confirmed")', 'f = state / "confirmed" / (key + ".confirmed")',
     ["P10 confirmations held back"]),
]


def copy_of(name: str) -> Path:
    dst = WORK / name / "serverday"
    for sub in ("run", "home", "tests", "workloads", "known"):
        shutil.copytree(SD / sub, dst / sub, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def run(sd: Path, cases: str, out: Path):
    p = subprocess.run([sys.executable, "-I", "-B", str(sd / "tests" / "test_transfer.py"), EXE, NET, CONV, str(sd), str(out)]
                       + (["only=" + cases] if cases else []), capture_output=True, text=True, timeout=1800)
    lines = (p.stdout + p.stderr).splitlines()
    return p.returncode, [ln[5:] for ln in lines if ln.startswith("FAIL ")], lines


bad = 0
rc, fails, lines = run(copy_of("control"), "", WORK / "control" / "out")
ok = rc == 0 and not fails
bad += not ok
print(f"{'ok  ' if ok else 'FAIL'} control (no change), all cases: exit {rc}, {lines[-1] if lines else ''}", flush=True)
for k, (name, file, cases, old, new, must_fail) in enumerate(MUTANTS, 1):
    sd = copy_of(f"m{k}")
    f = sd / file
    t = f.read_text(encoding="utf-8")
    if t.count(old) != 1:
        print(f"FAIL mutant {k} ({name}): the text to replace stands {t.count(old)} times in {file}, not once")
        bad += 1
        continue
    f.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
    rc, fails, lines = run(sd, cases, WORK / f"m{k}" / "out")
    missed = [m for m in must_fail if not any(x.startswith(m) for x in fails)]
    ok = rc == 1 and not missed
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} mutant {k} CAUGHT: {name}: cases {cases}, exit {rc}, {len(fails)} checks failed"
          + (f"; NOT failed although named: {missed}" if missed else "") + (f"; last line: {lines[-1][:200]}" if rc != 1 and lines else ""), flush=True)
print(f"CONTROL PASSES AND ALL {len(MUTANTS)} MUTANTS ARE CAUGHT" if not bad else f"NOT ALL: {bad} of {len(MUTANTS) + 1} lines are FAIL")
sys.exit(1 if bad else 0)
