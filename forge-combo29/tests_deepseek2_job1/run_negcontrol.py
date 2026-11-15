#!/usr/bin/env python3
"""Job 1 control B0(iv): the engine must call these endings LOST when the third
repetition is NOT on offer.

For every case, the position after the first ply (a) has the bare king to move,
the same material as at C, but no repetition anywhere in its history.  If the
engine there reports a draw score too, then a draw score at C proves nothing.
"""

import json
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
CASES = sys.argv[2]
OUT = sys.argv[3]
LIMIT = sys.argv[4] if len(sys.argv) > 4 else "depth 12"


def run(pos_cmd, limit):
    eng = Engine()
    eng.send("setoption name Threads value 1")
    eng.send("setoption name Hash value 16")
    eng.send("isready")
    eng.until("readyok")
    eng.send(pos_cmd)
    eng.send("go " + limit)
    out = eng.until("bestmove", timeout=120)
    eng.quit()
    best, info = None, None
    for ln in out:
        if ln.startswith("info") and " score " in ln:
            info = ln
        if ln.startswith("bestmove"):
            best = ln.split()[1]
    return best, info, out


def main():
    cases = json.load(open(CASES))["cases"]
    rows = []
    for c in cases:
        prefix = "position fen " + c["s0"] + " moves " + c["moves"][0]
        best, info, _ = run(prefix, LIMIT)
        score = None
        if info and " score " in info:
            toks = info.split()
            i = toks.index("score")
            score = toks[i + 1] + " " + toks[i + 2]
        rows.append({"s0": c["s0"], "pos": c["moves"][0], "best": best, "score": score})
    drawish = [r for r in rows if r["score"] in ("cp 0",)]
    mates = [r for r in rows if r["score"] and r["score"].startswith("mate -")]
    big = [r for r in rows if r["score"] and r["score"].startswith("cp ") and int(r["score"].split()[1]) <= -500]
    with open(OUT, "w") as f:
        f.write(f"limit {LIMIT}; position = S0 + first ply a, bare king to move, no repetition in history\n")
        f.write(f"cases {len(rows)}; score cp 0: {len(drawish)}; mate for white: {len(mates)}; "
                f"cp <= -500: {len(big)}\n")
        f.write("first 10 rows:\n")
        for r in rows[:10]:
            f.write(f"  {r['s0']} + {r['pos']} -> best {r['best']} score {r['score']}\n")
    print(f"cp0={len(drawish)} mate_neg={len(mates)} cp<=-500={len(big)} of {len(rows)}")


if __name__ == "__main__":
    main()
