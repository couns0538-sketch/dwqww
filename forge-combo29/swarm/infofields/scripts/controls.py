"""Planted-fault controls.

Brief rule 3: a control that silently does nothing is worse than no control.
Every checker used in the audit is fed a deliberate fault here, and the run
fails loudly if the checker does not fire.

Each case builds a fake `info` line (or fake sequence) containing one known
fault, runs the same predicate the audit uses, and asserts the verdict flips.
The clean line is included as the negative control, so a checker that always
says "bad" is caught too.
"""

import sys

import uci

FAILURES = []


def check(name, predicate, clean, fault, expect_fault=True):
    got_clean = predicate(clean)
    got_fault = predicate(fault)
    ok = (got_clean is False) and (got_fault is expect_fault)
    print("%-42s clean=%-5s fault=%-5s %s" % (name, got_clean, got_fault,
                                              "FIRES" if ok else "SILENT -- CHECKER BROKEN"))
    if not ok:
        FAILURES.append(name)


# ---------------------------------------------------------------- depth
def depth_le_seldepth(rec):
    """seldepth must be >= depth on every line."""
    return rec["seldepth"] < rec["depth"]


# ---------------------------------------------------------------- nps
def nps_not_nodes_over_time(rec):
    if rec["time"] == 0:
        return False  # time 0 is a separate, reported condition
    return rec["nps"] != rec["nodes"] * 1000 // rec["time"]


# ---------------------------------------------------------------- hashfull
def hashfull_out_of_range(rec):
    return not (0 <= rec["hashfull"] <= 1000)


# ---------------------------------------------------------------- score
def score_sign_wrong(rec):
    """For a White-to-move search where White is a rook up, score must be > 0."""
    return rec["stm"] == "white" and rec["white_is_up"] and rec["score_cp"] <= 0


# ---------------------------------------------------------------- nodes
def nodes_decreases(seq):
    return any(b < a for a, b in zip(seq, seq[1:]))


# ---------------------------------------------------------------- multipv
def multipv_not_contiguous(indices):
    return indices != list(range(1, len(indices) + 1))


# ---------------------------------------------------------------- time
def time_exceeds_wall(rec, tolerance_ms=150):
    return rec["time_ms"] > rec["budget_ms"] + tolerance_ms


def rec(**kw):
    base = {"depth": 10, "seldepth": 20, "nodes": 1000, "time": 2, "nps": 500000,
            "hashfull": 10, "stm": "white", "white_is_up": True, "score_cp": 50,
            "time_ms": 900, "budget_ms": 1000}
    base.update(kw)
    return base


def main():
    print("--- depth vs seldepth")
    check("seldepth >= depth", depth_le_seldepth, rec(seldepth=20), rec(seldepth=5))

    print("--- nps arithmetic")
    check("nps == nodes*1000/time", nps_not_nodes_over_time,
          rec(nodes=1000, time=2, nps=500000),
          rec(nodes=1000, time=2, nps=499999))

    print("--- hashfull bounds")
    check("0 <= hashfull <= 1000", hashfull_out_of_range,
          rec(hashfull=10), rec(hashfull=1001))

    print("--- score sign")
    check("White-up score is positive", score_sign_wrong,
          rec(score_cp=50), rec(score_cp=-50))

    print("--- nodes monotonicity")
    check("nodes non-decreasing", nodes_decreases,
          [10, 20, 30], [10, 30, 20])

    print("--- multipv contiguity")
    check("multipv 1..n", multipv_not_contiguous, [1, 2, 3], [1, 3])

    print("--- time vs budget")
    check("time <= budget", time_exceeds_wall,
          rec(time_ms=900, budget_ms=1000), rec(time_ms=3000, budget_ms=1000))

    print()
    if FAILURES:
        print("BROKEN CHECKERS:", FAILURES)
        return 1
    print("all checkers fired on their planted fault and passed the clean control")
    return 0


if __name__ == "__main__":
    sys.exit(main())
