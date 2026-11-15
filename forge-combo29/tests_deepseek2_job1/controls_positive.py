#!/usr/bin/env python3
"""Job 1 positive controls for the measuring apparatus itself.

Control 1 (harness): feed the B1 runner a case file whose "rep_move" is
deliberately WRONG.  The runner must then count them as "did not play k'".
If it still reports 500/500 the counting is broken and every "all good"
number in the report is worthless.

Control 2 (engine): at the C node the draw is on offer; five plies earlier the
SAME position (call it C') has occurred twice but k' would be only the second
occurrence, so it is not a draw.  The engine must NOT report a draw score at C'.
If it did, the cp 0 at C would prove nothing about repetition handling.
"""

import json
import subprocess
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
CASES = sys.argv[2]
OUTDIR = sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 100


def main():
    data = json.load(open(CASES))
    cases = data["cases"][:N]

    # ---- control 1: wrong expectation must be counted as a failure
    bad = {"cases": []}
    for c in cases:
        c2 = dict(c)
        legal = None
        import chess
        b = chess.Board(c["s0"])
        for u in c["moves"]:
            b.push_uci(u)
        moves = [m.uci() for m in b.legal_moves if m.uci() != c["rep_move"]]
        c2["rep_move"] = moves[0]
        bad["cases"].append(c2)
    badfile = OUTDIR + "/control1_cases_wrong_expectation.json"
    json.dump(bad, open(badfile, "w"), indent=1)
    out1 = OUTDIR + "/control1_wrong_expectation.json"
    r = subprocess.run([sys.executable,
                        "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1/run_engine.py",
                        ENGINE, badfile, "fresh", out1, "depth 12", "16"],
                       capture_output=True, text=True)
    with open(OUTDIR + "/control1_harness.txt", "w") as f:
        f.write("Control 1: 100 cases with a deliberately wrong expected move.\n")
        f.write("The runner must count these as NOT played (played_k low), and\n")
        f.write("the engine's actual bestmoves must still be the true k'.\n\n")
        f.write(r.stdout)
        f.write("\nstderr:\n" + r.stderr)
    d1 = json.load(open(out1))
    played = sum(1 for x in d1["records"] if x.get("played_k"))
    truth = sum(1 for x in d1["records"] if x.get("final") == data["cases"][x["i"]]["rep_move"])
    with open(OUTDIR + "/control1_harness.txt", "a") as f:
        f.write(f"\nplayed the (wrong) expected move: {played}/{len(d1['records'])}\n")
        f.write(f"engine actually played the TRUE k': {truth}/{len(d1['records'])}\n")

    # ---- control 2: score at C' (5 plies, no draw on offer)
    import chess
    rows = []
    for c in cases:
        eng = Engine()
        eng.send("setoption name Threads value 1")
        eng.send("setoption name Hash value 16")
        eng.send("isready")
        eng.until("readyok")
        rec = {"s0": c["s0"], "rep_move": c["rep_move"]}
        for label, k in (("Cprime_5plies", 5), ("C_7plies", 7)):
            prefix = "position fen " + c["s0"] + " moves " + " ".join(c["moves"][:k])
            eng.send(prefix)
            eng.send("go depth 12")
            lines = eng.until("bestmove", timeout=120)
            info = None
            best = None
            for ln in lines:
                if ln.startswith("info") and " score " in ln:
                    info = ln
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            sc = None
            if info:
                t = info.split()
                i = t.index("score")
                sc = t[i + 1] + " " + t[i + 2]
            rec[label] = {"best": best, "score": sc, "info": info}
        eng.quit()
        rows.append(rec)
        if len(rows) % 25 == 0:
            print(f"control2 {len(rows)}/{len(cases)}", flush=True)

    def tally(key):
        out = {"draw": 0, "mate_neg": 0, "cp_neg_big": 0, "other": 0}
        for r in rows:
            s = r[key]["score"]
            if s == "cp 0":
                out["draw"] += 1
            elif s and s.startswith("mate -"):
                out["mate_neg"] += 1
            elif s and s.startswith("cp ") and int(s.split()[1]) <= -300:
                out["cp_neg_big"] += 1
            else:
                out["other"] += 1
        return out

    summary = {"Cprime_5plies": tally("Cprime_5plies"), "C_7plies": tally("C_7plies")}
    json.dump({"rows": rows, "summary": summary},
              open(OUTDIR + "/control2_engine.json", "w"), indent=1)
    with open(OUTDIR + "/control2_engine.txt", "w") as f:
        f.write("Control 2: same positions, five plies earlier (C', no repetition on offer)\n")
        f.write("and at C (third repetition on offer).\n")
        f.write(json.dumps(summary, indent=1) + "\n\nfirst 10 rows:\n")
        for r in rows[:10]:
            f.write(f"  {r['s0']} rep={r['rep_move']}\n")
            f.write(f"    C'  best {r['Cprime_5plies']['best']} score {r['Cprime_5plies']['score']}\n")
            f.write(f"    C   best {r['C_7plies']['best']} score {r['C_7plies']['score']}\n")
    print("control2 summary", json.dumps(summary))


if __name__ == "__main__":
    main()
