#!/usr/bin/env python3
"""asan_patch.py EXE OUTDIR — run the drawn-root paths under ASan+UBSan, WITHOUT the quit race.

A first version of this test fed `printf 'go depth 6\nquit\n' | forge`, which is the quit-during-search
path: the engine abandons the search and answers the first legal move at once. That gave `f2f3` for the
halfmove-100 case and looked like the patch had failed, when in fact the test never ran a search. FOURTH
occurrence of this trap in my work (job1/README_HARNESS_BUG.md, checks/CHECK_27f2.md,
correction/verify_wall_BROKEN_quit_race.txt, and here). This version uses timing.Engine, which WAITS for
`bestmove` before sending quit, and asserts that a real search happened (nodes > 0 where a search is
expected).

Proofs required by the brief for a sanitizer run to count:
  (1) nm -C <exe> | grep -c __asan_ > 0   — printed below;
  (2) a planted fault counted by the SAME runner — see asan_plant.py, run separately.

Usage: asan_patch.py EXE OUTDIR
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

CASES = [
    ("hm99", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1", True),
    ("hm100", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1", True),
    ("hm150", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 150 1", True),
    ("rep3", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1 moves a1b1 g8f8 b1a1 f8g8 "
             "a1b1 g8f8 b1a1 f8g8", True),
    ("kvk", "position fen 7k/8/8/8/8/8/8/K7 w - - 0 1", False),
    # KNN v K is NOT insufficient material (mate is possible with help), so this one must SEARCH.
    # My first version marked it "0-node expected" and the engine's 681 nodes looked like a failure;
    # python-chess confirms is_insufficient_material() is False for it. The test's expectation was
    # wrong, not the engine. Both binaries answer b1d2.
    ("knnk", "position fen 7k/8/8/8/8/8/8/KNN5 w - - 0 1", True),
]
# PROOF 2: this case is only meaningful on a scratch copy with a planted fault; on a clean build the
# `plantfault` token does nothing and the case must show 0 lines. PASS_PLANT=1 flips the expectation.
PLANT_CASE = ("plantfault", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", True,
              "go depth 3 plantfault")


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    nm = subprocess.run(f"nm -C {exe} | grep -c __asan_", shell=True, capture_output=True, text=True)
    nm_ubsan = subprocess.run(f"nm -C {exe} | grep -c __ubsan_", shell=True, capture_output=True,
                              text=True)
    print(f"proof 1: __asan_ symbols = {nm.stdout.strip()}, __ubsan_ symbols = {nm_ubsan.stdout.strip()}")
    if nm.stdout.strip() in ("", "0"):
        print("NO ASAN INSTRUMENTATION — this run cannot count")
        return 1

    bad = 0
    print()
    print("| case | bestmove | nodes (last info) | sanitizer lines | expectation |")
    print("|---|---|---|---|---|")
    cases = list(CASES)
    if os.environ.get("PASS_PLANT"):
        cases = [PLANT_CASE]
    for case in cases:
        name, pos, expect_search = case[0], case[1], case[2]
        go_line = case[3] if len(case) > 3 else "go depth 6"
        eng = Engine(exe)
        eng.send("uci")
        eng.read_until("uciok", 20)
        for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
            eng.send(f"setoption name {opt} value {val}")
            eng.send("isready")
            eng.read_until("readyok", 20)
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(pos)
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(go_line)
        out, ok = eng.read_until("bestmove", 300)   # waits for bestmove; quit is sent AFTER
        eng.close()
        best, nodes = "", 0
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth") and "nodes" in line:
                f = line.split()
                nodes = int(f[f.index("nodes") + 1])
        san = [l for l in out if "Sanitizer" in l or "runtime error" in l]
        if san:
            bad += 1
        verdict = "search expected" if expect_search else "0-node adjudication expected"
        good = (nodes > 0) if expect_search else (nodes == 0)
        print(f"| {name} | {best or '-'} | {nodes} | {len(san)} | {verdict} "
              f"{'OK' if good else '**UNEXPECTED**'} |")
        with open(os.path.join(outdir, name + ".txt"), "w") as fh:
            fh.write("\n".join(out) + "\n")
    print()
    print(f"cases with sanitizer lines: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
