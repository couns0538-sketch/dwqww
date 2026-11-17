"""Job 3d: the ROOT CAUSE of the whole problem, measured.

Claim: the number a move gets when pinned alone is not the number that move got
inside the unrestricted search.  That is why a pinned comparison can disagree
with the engine even when both candidates are pinned.

Test.  Take the engine's top 5 moves from an unrestricted MultiPV 5.  For each,
record:
  * the unrestricted MultiPV score (all 5 searched together, in-tree)
  * the pinned-alone score at the same depth

If pinned-alone were an identity, the two columns would match.  They do not, and
the size of the mismatch bounds how much any pinned corpus can be trusted.

Run: python3 job1/pinned_vs_intree.py
Writes job1/pinned_vs_intree.txt, job1/pinned_vs_intree.csv
"""
import csv
import os
import statistics
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "job3"))
import engine  # noqa: E402
from rank_final import multipv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12


def main():
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]

    rows, out = [], []
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            continue
        cmdpos = f"position fen {fen}"
        plain = engine.run_session(cmdpos, f"go depth {DEPTH}")
        order, intree, mr = multipv(fen, DEPTH, 5)
        if len(order) < 5 or mr.fatal or plain.fatal:
            continue
        if not (order[0] == plain.bestmove and intree[order[0]] == plain.signed_score):
            continue
        for mv in order:
            r = engine.run_session(cmdpos, f"go depth {DEPTH} searchmoves {mv}")
            if r.fatal or r.signed_score is None:
                break
            rows.append(dict(idx=idx, fen=fen, move=mv, intree=intree[mv],
                             pinned=r.signed_score, delta=r.signed_score - intree[mv],
                             is_top=int(mv == order[0])))
        else:
            continue

    with open(os.path.join(HERE, "pinned_vs_intree.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    d = [r["delta"] for r in rows]
    n = len(rows)
    out += [f"engine {engine.ENGINE}", f"depth {DEPTH}",
            f"(move, position) pairs measured: {n}",
            "intree = the score that move got inside one unrestricted MultiPV 5 search",
            "pinned = the score it gets when searched alone with searchmoves",
            "",
            f"identical                                  : {sum(1 for x in d if x == 0)}/{n}",
            f"|delta| >= 10 cp                           : {sum(1 for x in d if abs(x) >= 10)}/{n}",
            f"|delta| >= 50 cp                           : {sum(1 for x in d if abs(x) >= 50)}/{n}",
            f"mean delta {statistics.mean(d):+.1f}   median {statistics.median(d):+.1f}   "
            f"min {min(d)}   max {max(d)}",
            f"sd {statistics.pstdev(d):.1f}"]
    top = [r["delta"] for r in rows if r["is_top"]]
    if top:
        out += ["", f"TOP move only: n {len(top)}, identical "
                    f"{sum(1 for x in top if x == 0)}/{len(top)}, "
                    f"|delta|>=10 {sum(1 for x in top if abs(x) >= 10)}/{len(top)}, "
                    f"mean {statistics.mean(top):+.1f}"]
    text = "\n".join(out)
    with open(os.path.join(HERE, "pinned_vs_intree.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
