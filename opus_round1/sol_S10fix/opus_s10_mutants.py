#!/usr/bin/env python3
"""Planted-bug check for the S10fix tools: copy the tools and test_opus_s10fix.py into a fresh folder per mutant,
apply one single-line bug (the pattern must occur exactly once), run the tests and require them to FAIL.
usage: opus_s10_mutants.py --work DIR   (DIR must not exist; nothing outside it is written)"""
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["opus_s10_screen_verdict.py", "opus_s10_wac_flips.py", "opus_s10_hygiene_check.py", "opus_s10_bench_rerun.py",
         "test_opus_s10fix.py"]
MUTANTS = [
    ("guard_sign", "opus_s10_screen_verdict.py", "any(abs(c) > GUARD_LIMIT", "any(c > GUARD_LIMIT"),
    ("wac_boundary", "opus_s10_screen_verdict.py", "elif wac < WAC_FLOOR:", "elif wac <= WAC_FLOOR:"),
    ("lost_gained_swap", "opus_s10_wac_flips.py", "lost = [i for i in ids if i in off_solved and i not in on_solved]",
     "lost = [i for i in ids if i not in off_solved and i in on_solved]"),
    ("dup_groups_singletons", "opus_s10_hygiene_check.py", "if len(g) > 1 and g[0][\"bytes\"] > 0]",
     "if g[0][\"bytes\"] > 0]"),
    ("hash_option", "opus_s10_bench_rerun.py", '("Hash", "16")', '("Hash", "32")'),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True)
    a = ap.parse_args(argv)
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=False)
    survived = 0
    for name, target, old, new in MUTANTS:
        d = work / name
        d.mkdir()
        for f in FILES:
            shutil.copy2(HERE / f, d / f)
        src = (d / target).read_text(encoding="utf-8")
        if src.count(old) != 1:
            raise SystemExit(f"{name}: pattern occurs {src.count(old)} times in {target}")
        (d / target).write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        proc = subprocess.run([sys.executable, "-I", "-B", str(d / "test_opus_s10fix.py")], capture_output=True, text=True)
        failed = [l for l in proc.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
        status = "KILLED" if proc.returncode != 0 else "SURVIVED"
        survived += status == "SURVIVED"
        print(f"{name}: {status} (rc={proc.returncode}); failing tests: {', '.join(failed) or '-'}")
    print(f"{len(MUTANTS) - survived}/{len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
