"""Job 1 causal test, second half: separate the two code paths.

Two things change at a restricted root in base 6b98f217:
  (i)  no TT store        src/search.cpp:2093  if (excluded.is_none() && !(root_node && root_restricted_))
  (ii) IIR depth reduction src/search.cpp:1784  fires because tt_move is always none there

Arms, all at depth 12 on the same pinpool positions, all with `searchmoves <all legal>`:
  base_all  unmodified
  pA_all    SCRATCH PATCH A: (i) removed, (ii) still fires
  pB_all    SCRATCH PATCH B: (ii) removed for a restricted root, (i) still present
  pAB_all   both removed -- must equal the unrestricted answer exactly if these two
            lines are the WHOLE mechanism

Controls:
  * each patch build must still pass the honesty nodes (bench 13 = 862329 here,
    recorded by the build step; a patch that changed the search in general would
    move it)
  * base plain (no searchmoves) is the reference in every row

Run: python3 job1/causal_split.py
Writes job1/causal_split.txt, job1/causal_split.csv
"""
import csv
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12
BIN = {
    "base": "/tmp/build-rel/forge",
    "pA": "/tmp/build-pA/forge",
    "pB": "/tmp/build-pB/forge",
    "pAB": "/tmp/build-pAB/forge",
}


def main():
    with open(os.path.join(HERE, "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]

    rows, out = [], []
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            out.append(f"SKIP {fen}")
            continue
        pos = f"position fen {fen}"
        plain = engine.run_session(pos, f"go depth {DEPTH}", engine=BIN["base"])
        if plain.fatal:
            continue
        sm = f"go depth {DEPTH} searchmoves {' '.join(legal)}"
        arms = {"base_all": engine.run_session(pos, sm, engine=BIN["base"]),
                "pA_all": engine.run_session(pos, sm, engine=BIN["pA"]),
                "pB_all": engine.run_session(pos, sm, engine=BIN["pB"]),
                "pAB_all": engine.run_session(pos, sm, engine=BIN["pAB"])}
        if any(r.fatal for r in arms.values()):
            out.append(f"SKIP {idx}: {[(k, r.fatal) for k, r in arms.items()]}")
            continue
        row = dict(idx=idx, fen=fen, plain=plain.bestmove, plain_score=plain.score)
        for k, r in arms.items():
            row[k] = r.bestmove
            row[k + "_score"] = r.score
        rows.append(row)
        out.append(f"[{idx:2d}] plain {plain.bestmove} {plain.score:>6} | " + " | ".join(
            f"{k} {r.bestmove} {r.score}" for k, r in arms.items()))

    with open(os.path.join(HERE, "causal_split.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    out += ["", "== SPLIT OF THE TWO CODE PATHS, depth 12, all-legal restriction ==",
            f"positions: {n}",
            "arm | bestmove == plain | score == plain"]
    for k in ("base_all", "pA_all", "pB_all", "pAB_all"):
        mv = sum(1 for r in rows if r[k] == r["plain"])
        sc = sum(1 for r in rows if r[k + "_score"] == r["plain_score"])
        out.append(f"{k:9s} | {mv}/{n} | {sc}/{n}")

    text = "\n".join(out)
    with open(os.path.join(HERE, "causal_split.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
