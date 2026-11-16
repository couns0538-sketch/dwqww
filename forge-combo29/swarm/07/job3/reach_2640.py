#!/usr/bin/env python3
"""reach_2640.py EXE_WITH_MARKER OUTDIR

Reads the REACHED-LINE-2640 markers a scratch build writes to stderr and decides whether
search.cpp:2640 ever executes with an empty root_candidates.

The marker line is `REACHED-LINE-2640 root_candidates=<n>` (see the scratch copy at
/tmp/reach/src/search.cpp, built the same way as build-dbg). If the marker string is not
present in the binary at all, this script fails loudly instead of reporting "no markers"
(the mistake seat 19 warned about: parsing a line the engine never prints).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "job2"))
from uci_drive import parse_cases, run_case  # noqa: E402

CASES = os.path.join(HERE, "cases_17sf2.txt")
MARKER = "REACHED-LINE-2640"
PATTERN = re.compile(r"REACHED-LINE-2640 root_candidates=(\d+)")


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    # Precondition: the marker must actually exist in this binary.
    dumped = subprocess.run(["strings", exe], capture_output=True, text=True)
    if dumped.returncode != 0:
        raise SystemExit(f"FAIL 'strings {exe}' failed: cannot verify the instrument exists")
    if MARKER not in dumped.stdout:
        raise SystemExit(f"FAIL {exe} does not contain the marker {MARKER}: "
                         f"a 'no marker found' result would be meaningless")

    zero_sizes, rows = [], []
    for name, lines, about in parse_cases(CASES):
        rec = run_case(exe, name, lines, about, outdir, 60)
        errpath = os.path.join(outdir, name + ".err")
        if not os.path.exists(errpath):
            raise SystemExit(f"FAIL no stderr for {name}")
        text = open(errpath, encoding="utf-8", errors="replace").read()
        sizes = [int(m) for m in PATTERN.findall(text)]
        rows.append((name, rec["bestmoves"][-1] if rec["bestmoves"] else "-", sizes))
        zero_sizes.extend((name, s) for s in sizes if s == 0)
    for name, bm, sizes in rows:
        print(f"{name:34s} bestmove={bm:16s} marker hits={len(sizes)} sizes={sizes}")
    total = sum(len(s) for _, _, s in rows)
    print()
    print(f"total marker hits: {total}")
    if total == 0:
        raise SystemExit("FAIL the marker never fired at all, so this run shows nothing either way")
    if zero_sizes:
        print("RESULT: CONFIRMED - line 2640 was reached with an EMPTY root at:",
              zero_sizes)
        return
    print("RESULT: REFUTED - line 2640 never ran with root_candidates.size()==0 in any case; "
          "every hit had a non-empty root.")


if __name__ == "__main__":
    main()
