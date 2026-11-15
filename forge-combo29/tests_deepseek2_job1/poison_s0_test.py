#!/usr/bin/env python3
"""Job 1, the sharpest direct test of scenario 1.

In every case the drawing move k' at C leads to S0 for the THIRD time.  So the
node that must return "draw" is S0 itself, one ply below C.  Here the table is
poisoned at S0 with the engine's OWN score from a deep search of S0, where S0
is not yet a repetition and white is winning:

  step 1  `position fen <S0>` + `go depth 18`   (S0 evaluated as a white win)
  step 2  `position fen S0 moves <a k a' k' a k a'>` + `go depth 12`
          (root C, black to move; k' reaches S0 for the third time)

If the stored win at S0 can hide the draw, the engine will not play k' here.
Control: the same step 2 in a FRESH process, with no poisoning.

A third arm re-searches S0 after the draw is established, to show the stored
score is replaced rather than kept: `position fen <S0>` again in the same
process.
"""

import json
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
CASES = sys.argv[2]
OUT = sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 500
POISON_DEPTH = sys.argv[5] if len(sys.argv) > 5 else "18"


def score_of(info):
    if not info:
        return None
    t = info.split()
    if "score" not in t:
        return None
    i = t.index("score")
    return t[i + 1] + " " + t[i + 2]


def ask(eng, pos, limit):
    eng.send(pos)
    eng.send("go " + limit)
    lines = eng.until("bestmove", timeout=300)
    info = best = None
    for ln in lines:
        if ln.startswith("info") and " score " in ln:
            info = ln
        if ln.startswith("bestmove"):
            best = ln.split()[1]
    return best, info


def fresh():
    e = Engine()
    e.send("setoption name Threads value 1")
    e.send("setoption name Hash value 16")
    e.send("isready")
    e.until("readyok")
    return e


def main():
    cases = json.load(open(CASES))["cases"][:N]
    rows = []
    for i, c in enumerate(cases):
        s0, mv = c["s0"], c["moves"]
        pos_c = "position fen " + s0 + " moves " + " ".join(mv)
        pos_s0 = "position fen " + s0

        # control arm: fresh process, search only at C
        e1 = fresh()
        c_best, c_info = ask(e1, pos_c, "depth 12")
        e1.quit()

        # test arm: poison S0, then search at C
        e2 = fresh()
        p_best, p_info = ask(e2, pos_s0, "depth " + POISON_DEPTH)
        w_best, w_info = ask(e2, pos_c, "depth 12")
        # after the game line, what does the engine now think of S0?
        r_best, r_info = ask(e2, pos_s0, "depth 12")
        e2.quit()

        rows.append({
            "i": i, "s0": s0, "moves": mv, "want": c["rep_move"],
            "poison_s0": {"best": p_best, "score": score_of(p_info), "info": p_info},
            "fresh_c": {"best": c_best, "score": score_of(c_info), "info": c_info},
            "warm_c": {"best": w_best, "score": score_of(w_info), "info": w_info},
            "rescore_s0": {"best": r_best, "score": score_of(r_info), "info": r_info},
        })
        if (i + 1) % 50 == 0:
            ok = sum(1 for r in rows if r["warm_c"]["best"] == r["want"])
            print(f"{i+1}/{len(cases)} warm_played_k={ok}", flush=True)

    def tally(key, field="best"):
        d = {}
        for r in rows:
            v = r[key][field] if field != "score" else r[key]["score"]
            d[v] = d.get(v, 0) + 1
        return dict(sorted(d.items(), key=lambda kv: -kv[1])[:6])

    summary = {
        "cases": len(rows),
        "fresh_played_k": sum(1 for r in rows if r["fresh_c"]["best"] == r["want"]),
        "warm_played_k": sum(1 for r in rows if r["warm_c"]["best"] == r["want"]),
        "fresh_scores": tally("fresh_c", "score"),
        "warm_scores": tally("warm_c", "score"),
        "poison_scores": tally("poison_s0", "score"),
        "rescore_s0_scores": tally("rescore_s0", "score"),
    }
    json.dump({"poison_depth": POISON_DEPTH, "summary": summary, "rows": rows},
              open(OUT, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
