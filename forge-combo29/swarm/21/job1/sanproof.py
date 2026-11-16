#!/usr/bin/env python3
"""sanproof.py EXE OUTDIR

THE SANITIZER PROOF required by the brief, run through THE SAME RUNNER (run_fen.py).
(1) nm on the exe: __asan_ and __ubsan_ counts are recorded in the .meta the runner writes.
(2) A scratch copy with ONE planted, input-controlled fault must be counted by the same
    runner. Here the scratch copy has two planted faults behind input-controlled FEN text:
      - a heap over-read when the FEN contains the rank text "7777777"
      - a signed overflow when the FEN contains "1234567"
    The proof passes only when the runner counts sanitizer lines for the planted build.

Usage: sanproof.py  (writes sanproof_input.tsv and drives run_fen.py twice)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def build_input():
    rows = []
    good = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    rows.append(("1", "P", "plant_as", "append rank 7777777",
                 "rnbqkbnr/pppppppp/8/7777777/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "0"))
    rows.append(("2", "P", "plant_ub", "append 1234567 in ep field",
                 "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq 1234567 0 1", "0"))
    rows.append(("3", "P", "clean", "unmutated control", good, "1"))
    for i in range(4, 12):
        rows.append((str(i), "P", "clean", "unmutated control", good, "1"))
    path = os.path.join(HERE, "sanproof_input.tsv")
    with open(path, "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    return path


def main():
    inp = build_input()
    asan = os.path.expanduser("~/b/asan/forge")
    planted = os.path.expanduser("~/b/asan_planted/forge")
    for label, exe in (("proof_real", asan), ("proof_planted", planted)):
        outdir = os.path.join(HERE, "out_proof_" + label)
        subprocess.run([sys.executable, os.path.join(HERE, "run_fen.py"), exe, inp, outdir, label],
                       check=True)
        print("---- %s ----" % label)
        print(open(os.path.join(outdir, label + "_summary.txt")).read())


if __name__ == "__main__":
    main()
