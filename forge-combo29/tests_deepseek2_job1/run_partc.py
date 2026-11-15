#!/usr/bin/env python3
"""Job 1 part C: stored mate vs the 50-move clock.

For each of 100 queen-vs-king positions whose shortest mate is exactly 3 moves
(5 plies), in ONE engine process with NO ucinewgame:
  1. `position fen <P with halfmove clock 0>` then `go depth 12`
     -> the table now holds a mate score for P
  2. `position fen <the same P with halfmove clock 97>` then `go depth 12`
With clock 97 only three plies remain (97, 98, 99 then 100 drawn on the next
non-mating move), so a 5-ply mate cannot be completed; the correct answer is a
draw score and no move can be reported as mate in 3.

Control: the same with halfmove clock 90, where the 5-ply mate still fits.
"""

import json
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
OUT = sys.argv[3]
DEPTH = sys.argv[4] if len(sys.argv) > 4 else "12"


def with_clock(fen, clock):
    parts = fen.split()
    parts[4] = str(clock)
    return " ".join(parts)


def parse_score(info):
    if not info:
        return None
    toks = info.split()
    if "score" not in toks:
        return None
    i = toks.index("score")
    return toks[i + 1] + " " + toks[i + 2]


def main():
    positions = json.load(open(POSFILE))["positions"]
    rows = []
    for n, p in enumerate(positions):
        fen0 = with_clock(p["fen"], 0)
        fen97 = with_clock(p["fen"], 97)
        fen90 = with_clock(p["fen"], 90)
        eng = Engine()
        eng.send("setoption name Threads value 1")
        eng.send("setoption name Hash value 16")
        eng.send("isready")
        eng.until("readyok")
        rec = {"i": n, "fen0": fen0}
        for label, fen in (("first0", fen0), ("then97", fen97), ("then90", fen90)):
            eng.send("position fen " + fen)
            eng.send("go depth " + DEPTH)
            lines = eng.until("bestmove", timeout=180)
            info = None
            best = None
            for ln in lines:
                if ln.startswith("info") and " score " in ln:
                    info = ln
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            rec[label] = {"best": best, "info": info, "score": parse_score(info)}
        eng.quit()
        rows.append(rec)
        if (n + 1) % 20 == 0:
            print(f"{n+1}/{len(positions)}", flush=True)

    def tally(key):
        out = {"mate_positive": 0, "mate_negative": 0, "draw": 0, "other": 0, "missing": 0}
        for r in rows:
            s = r[key]["score"]
            if s is None:
                out["missing"] += 1
            elif s.startswith("mate "):
                d = int(s.split()[1])
                if d > 0:
                    out["mate_positive"] += 1
                else:
                    out["mate_negative"] += 1
            elif s == "cp 0":
                out["draw"] += 1
            else:
                out["other"] += 1
        return out

    summary = {k: tally(k) for k in ("first0", "then97", "then90")}
    json.dump({"depth": DEPTH, "rows": rows, "summary": summary}, open(OUT, "w"), indent=1)
    print("summary", json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
