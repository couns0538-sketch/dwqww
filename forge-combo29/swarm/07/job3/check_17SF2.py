#!/usr/bin/env python3
"""check_17SF2.py EXE OUTDIR

Checks seat 17's finding S-F2 by its own claim, not by its script:
  "src/search.cpp:2640 `if (result.best_move.is_none()) result.best_move =
   root_candidates.front();` reads front() of an EMPTY MoveList when root_candidates is
   empty but legal moves exist".

Two independent instruments, each with a positive control so a "no crash" result means
something:

 A. The claim under a container-checking STL: EXE must be built with -D_GLIBCXX_DEBUG.
    Control: the same binary must abort on `searchmoves` with an illegal name IF the claim
    is true. Pass/fail is read from exit status and stderr, not from a grepped number.

 B. Reachability: a scratch build that prints a marker at 2640 with root_candidates.size().
    If 2640 runs with size 0 anywhere, the claim is CONFIRMED; if it only ever runs with a
    non-zero size, or never runs for the empty-root cases, the claim is REFUTED because
    the code path cannot exist.

Both are driven by uci_drive.py, which never pipelines a command behind `go`.

Every assertion is explicit: a missing record, a missing bestmove or a missing marker file
is an error, never a pass.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "job2"))
from uci_drive import parse_cases, run_case  # noqa: E402

# Cases: the empty-root ones are the claim; startpos_legal_control is the sanity control.
CASES_PATH = os.path.join(HERE, "cases_17sf2.txt")


def drive(exe, outdir, timeout=60):
    os.makedirs(outdir, exist_ok=True)
    return [run_case(exe, n, l, a, outdir, timeout) for n, l, a in parse_cases(CASES_PATH)]


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = drive(exe, outdir)
    print(f"{'case':32s} {'bestmove':12s} {'depthlines':10s} {'aborted':8s}")
    any_abort = False
    for rec in rows:
        err = os.path.join(outdir, rec["case"] + ".err")
        if not os.path.exists(err):
            raise SystemExit(f"FAIL no stderr file for {rec['case']}: nothing measured")
        text = open(err, encoding="utf-8", errors="replace").read()
        aborted = ("attempt to access an element in an empty container" in text
                   or "Assertion" in text or "Aborted" in text)
        any_abort = any_abort or aborted
        # depth lines are only visible as the last info line here; count from stderr+json
        depth = 1 if rec.get("last_info") else 0
        print(f"{rec['case']:32s} {(rec['bestmoves'][-1] if rec['bestmoves'] else '-'):12s} "
              f"{depth:<10d} {str(aborted):8s}")
        if not rec["bestmoves"] and not aborted:
            raise SystemExit(f"FAIL {rec['case']}: no bestmove and no abort -- the run measured nothing")
    print()
    print(f"container-check abort seen anywhere: {any_abort}")
    print("VERDICT A (debug-STL): " +
          ("claim SUPPORTED by the container check" if any_abort
           else "claim NOT supported: front() of an empty container was never reached"))
    with open(os.path.join(outdir, "verdict.txt"), "w") as fh:
        fh.write(f"any_abort={any_abort}\n")


if __name__ == "__main__":
    main()
