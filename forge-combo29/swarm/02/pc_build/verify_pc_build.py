#!/usr/bin/env python3
"""S02: verify the PC r15 build against the three bench rows of FABLE_TO_swarm_5.md, and record the thread rule.

File 5's table (measured on the PC's own exe):
  settings                                 bench 11   bench 13   bench 16   go perft 5
  none (no setoption at all)               312866     862329     3024920    4865609
  S14 (the 14 settings of file 1)          242796     656517     -          -
  PC20 = S14 + the six below               278024     587276     -          -

A build that misses any stated number is not used. Every line is a FRESH process (a bench in a second process is
cold, so this satisfies both the pin regime and seat 10's warm-search rule).

THREADS: every run here sends `setoption name Threads value 1` explicitly, because seat 04 measured that scores
above Threads 1 are not reproducible (+2576 / mate 13 / mate 18 / mate 16 on four runs of one position at
Threads 4, against +2207 four times at Threads 1). S14 does not set Threads, and PC20 does not either, so the
engine default (1) applies; I set it explicitly anyway so the record cannot be misread.

usage: verify_pc_build.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_pc"

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]
PC20_EXTRA = [
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true",
    "setoption name OwnBook value false",
]
THREADS1 = "setoption name Threads value 1"
HASH16 = "setoption name Hash value 16"
EXPECT = {
    "none": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609},
    "S14": {"bench11": 242796, "bench13": 656517},
    "PC20": {"bench11": 278024, "bench13": 587276},
}
BAD = ("unknown option", "invalid value", "ERROR")


def run(exe, setoptions, command):
    """One FRESH process per measurement."""
    lines = ["uci"]
    for s in setoptions:
        lines.append(s)
    lines += ["isready", "ucinewgame", "isready", command, "quit"]
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True, env=env)
    out = p.stdout + p.stderr
    for bad in BAD:
        if bad in out:
            sys.exit("FAIL: a setoption was refused (%r) for %r under %r. Output:\n%s"
                     % (bad, command, setoptions, out[-900:]))
    return out


def bench_nodes(out, depth):
    m = re.search(r"info string bench depth %d nodes (\d+)" % depth, out)
    if not m:
        sys.exit("FAIL: no bench depth %d line in the engine output. Output:\n%s" % (depth, out[-700:]))
    return int(m.group(1))


def perft_nodes(out):
    m = re.search(r"^nodes (\d+)\s*$", out, re.MULTILINE)
    if not m:
        sys.exit("FAIL: no perft `nodes` line. Output:\n%s" % out[-700:])
    return int(m.group(1))


def main():
    os.makedirs(OUT, exist_ok=True)
    regimes = {
        # the "none" row is DEFAULT options: Threads 1 and Hash 16 are the defaults, set explicitly for the record
        "none": [THREADS1, HASH16],
        "S14": [THREADS1, HASH16] + S14,
        "PC20": [THREADS1, HASH16] + S14 + PC20_EXTRA,
    }
    results = {}
    rows = []
    for name, opts in regimes.items():
        got = {}
        for depth in (11, 13, 16):
            key = "bench%d" % depth
            if key in EXPECT[name]:
                got[key] = bench_nodes(run(EXE, opts, "bench %d" % depth), depth)
        if name == "none":
            got["perft5"] = perft_nodes(run(EXE, opts, "go perft 5"))
        results[name] = got
        print("%-6s %s" % (name, json.dumps(got)))

    print()
    print("| settings | measurement | got | file 5 states | verdict |")
    print("|---|---|---|---|---|")
    all_ok = True
    for name, exp in EXPECT.items():
        for key, want in exp.items():
            have = results[name].get(key)
            ok = have == want
            all_ok = all_ok and ok
            label = key if key != "perft5" else "perft 5"
            print("| %s | %s | %s | %s | %s |" % (name, label, have, want, "PASS" if ok else "FAIL"))
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1,
               "threads_note": "Threads 1 set explicitly on every run; seat 04 measured scores above Threads 1 "
                               "as not reproducible",
               "options": regimes, "results": results, "expected": EXPECT},
              open(os.path.join(OUT, "results.json"), "w"), indent=1)
    print()
    if all_ok:
        print("ALL STATED NUMBERS MATCH -> this PC build is usable")
    else:
        sys.exit("MISMATCH: the PC build does not reproduce file 5's numbers; per file 5 it must not be used")


if __name__ == "__main__":
    main()
