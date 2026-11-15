#!/usr/bin/env python3
"""Job 1, sharper test of the same question ("a repetition two or more plies
below the node whose stored score is used").

Why this test exists
  In the B tests the node C is always a ROOT search.  Read search.cpp: the TT
  cutoff at a node needs !pv_node (line 1637) and the root is a PV node, so a
  root search never takes a stored score in place of searching.  B1-B3
  therefore test the root path only.  This test puts C at ply 1 under a
  restricted root, where it IS a non-PV node, and poisons the table first.

Construction, per case (S0, list a k a' k' a k a' from gen_cases.py)
  step 1  `position fen S0 moves a k a'` + `go depth 16`
          Here C has only ONE prior occurrence, so black has no third
          repetition and C is genuinely "black lost".  The table now holds a
          deep "black lost" score at C.  This is the poisoning, and it is a
          score the engine itself computes.
  step 2  `position fen S0 moves a k a' k' a k` + `go depth 12 searchmoves <a'>`
          The root is now one ply before C, restricted to a'.  Its only line is
          a' -> C, and at C black's k' is the third repetition.  So the true
          value of this restricted root is a DRAW.
          C sits at ply 1, a non-PV node, with the poisoned entry in place.

  fresh process, step 2 only  = the control: no poisoned entry, the search
                                must report a draw.
  warm  process, step 1 then 2 = the test.  A win score here means the stored
                                score hid the draw.
"""

import json
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
CASES = sys.argv[2]
OUT = sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 100


def score_of(info):
    if not info:
        return None
    t = info.split()
    if "score" not in t:
        return None
    i = t.index("score")
    return t[i + 1] + " " + t[i + 2]


def ask(eng, pos, limit, extra=""):
    eng.send(pos)
    eng.send(("go " + limit + (" " + extra if extra else "")).strip())
    lines = eng.until("bestmove", timeout=300)
    info = None
    best = None
    for ln in lines:
        if ln.startswith("info") and " score " in ln:
            info = ln
        if ln.startswith("bestmove"):
            best = ln.split()[1]
    return best, info, lines


def main():
    cases = json.load(open(CASES))["cases"][:N]
    rows = []
    for i, c in enumerate(cases):
        s0, mv = c["s0"], c["moves"]
        a2 = mv[2]                       # a' : the white return move
        pos_poison = "position fen " + s0 + " moves " + " ".join(mv[:3])
        pos_root = "position fen " + s0 + " moves " + " ".join(mv[:6])

        # control: fresh process, step 2 only
        e1 = Engine()
        e1.send("setoption name Threads value 1")
        e1.send("setoption name Hash value 16")
        e1.send("isready")
        e1.until("readyok")
        c_best, c_info, _ = ask(e1, pos_root, "depth 12", "searchmoves " + a2)
        c_poison = None
        e1.quit()

        # test: poison C, then the same root
        e2 = Engine()
        e2.send("setoption name Threads value 1")
        e2.send("setoption name Hash value 16")
        e2.send("isready")
        e2.until("readyok")
        p_best, p_info, _ = ask(e2, pos_poison, "depth 16")
        w_best, w_info, _ = ask(e2, pos_root, "depth 12", "searchmoves " + a2)
        e2.quit()

        rec = {
            "i": i, "s0": s0, "moves": mv, "root_move": a2,
            "poison_search": {"best": p_best, "score": score_of(p_info), "info": p_info},
            "fresh_root": {"best": c_best, "score": score_of(c_info), "info": c_info},
            "warm_root": {"best": w_best, "score": score_of(w_info), "info": w_info},
        }
        rows.append(rec)
        if (i + 1) % 25 == 0:
            print(f"{i+1}/{len(cases)}", flush=True)

    def bucket(s):
        if s is None:
            return "missing"
        if s == "cp 0":
            return "draw"
        if s.startswith("mate "):
            return "mate+" if int(s.split()[1]) > 0 else "mate-"
        return "cp+" if int(s.split()[1]) > 0 else "cp-"

    summary = {}
    for key in ("poison_search", "fresh_root", "warm_root"):
        b = {}
        for r in rows:
            k = bucket(r[key]["score"])
            b[k] = b.get(k, 0) + 1
        summary[key] = b
    diffs = [r for r in rows
             if bucket(r["fresh_root"]["score"]) != bucket(r["warm_root"]["score"])]
    json.dump({"summary": summary, "differing": len(diffs), "rows": rows},
              open(OUT, "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("differing cases:", len(diffs))
    for r in diffs[:5]:
        print(" ", r["s0"], r["moves"], "fresh", r["fresh_root"]["score"],
              "warm", r["warm_root"]["score"])


if __name__ == "__main__":
    main()
