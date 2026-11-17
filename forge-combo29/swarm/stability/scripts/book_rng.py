"""Measurement 6: the book RNG, and why the harness pins `OwnBook false`.

Two separate questions, both required before the stability numbers mean anything:

  Q1  Does the book vary run to run, and is the variation the RNG?
      Measured over 40 fresh processes per arm. A "varies" result with no
      variety control would not say WHICH setting to pin.

  Q2  Can a `go depth` search ever reach the book?
      If it can, every stability number in this seat is contaminated by the
      book. If it cannot, `OwnBook false` is belt-and-braces rather than load
      bearing -- and the difference matters, because a correction that is not
      needed is a change to the conditions a later reproducer will copy.

Q2 is answered from the source as well as from the wire: the book gate is
`limits.time_ms >= 0 || limits.movetime_ms >= 0` (uci.cpp:525), and `go depth`
sets neither. The wire test is the confirmation that the source reading bites.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import run_one

FORGE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-stab/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "book_rng.json"
RUNS = 40
out = {}

# ---- Q1: book variety at Threads 1 -----------------------------------
def arm(own_book, variety, threads=1, runs=RUNS):
    moves = Counter()
    bookish = 0
    for _ in range(runs):
        opts = ["setoption name OwnBook value " + ("true" if own_book else "false"),
                f"setoption name Threads value {threads}"]
        if variety is not None:
            opts.append(f"setoption name Book Variety value {variety}")
        r = run_one(FORGE, "position startpos", "go movetime 400", options=opts)
        moves[r["bestmove"]] += 1
        # a book reply carries no info depth line at all
        if r["n_info_depth"] == 0:
            bookish += 1
    return {"own_book": own_book, "variety": variety, "threads": threads,
            "runs": runs, "distinct_moves": len(moves), "move_hist": dict(moves),
            "book_reply_count": bookish}

out["q1_default_variety"] = arm(True, None)
out["q1_variety_0"] = arm(True, 0)
out["q1_ownbook_off"] = arm(False, None)
out["q1_default_variety_T4"] = arm(True, None, threads=4)

# ---- Q2: can go depth reach the book? --------------------------------
DEPTH_RUNS = 20
depth_book = 0
depth_moves = Counter()
for _ in range(DEPTH_RUNS):
    r = run_one(FORGE, "position startpos", "go depth 6",
                options=["setoption name OwnBook value true", "setoption name Threads value 1"])
    if r["n_info_depth"] == 0:
        depth_book += 1
    depth_moves[r["bestmove"]] += 1

# Positive control for the same instrument: a clock search WITH OwnBook true
# must book, so a zero on the depth arm is a real zero rather than a dead check.
ctrl_book = 0
for _ in range(DEPTH_RUNS):
    r = run_one(FORGE, "position startpos", "go movetime 400",
                options=["setoption name OwnBook value true", "setoption name Threads value 1",
                         "setoption name Book Variety value 0"])
    if r["n_info_depth"] == 0:
        ctrl_book += 1

out["q2_depth_book_replies"] = {"runs": DEPTH_RUNS, "bookish": depth_book,
                                "distinct_moves": len(depth_moves),
                                "move_hist": dict(depth_moves)}
out["q2_clock_control_book_replies"] = {"runs": DEPTH_RUNS, "bookish": ctrl_book}
out["source_note"] = ("book gate uci.cpp:525 requires time_ms>=0 or movetime_ms>=0; "
                      "go depth sets neither")

with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
bad = (out["q1_variety_0"]["distinct_moves"] != 1
       or out["q1_ownbook_off"]["distinct_moves"] != 1
       or out["q1_default_variety"]["distinct_moves"] < 2
       or out["q2_depth_book_replies"]["bookish"] != 0
       or out["q2_clock_control_book_replies"]["bookish"] == 0)
print("\nBOOK PROOF", "FAILED" if bad else "OK")
sys.exit(1 if bad else 0)
