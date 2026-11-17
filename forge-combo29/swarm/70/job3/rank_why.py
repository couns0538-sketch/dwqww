"""Job 3b: WHY does pinning reorder candidates, and is a 2-candidate comparison safe?

Two sub-questions, both mechanical:

(a) COMPRESSION.  The pinned score of every move is measured with the same alpha
    window of a one-move root.  If pinning shrinks the gaps between moves, near
    ties get scrambled while big gaps survive.  Measured as |pinned gap| divided
    by |reference gap| per pair.

(b) DOES PINNING PRESERVE THE WINNER?  A 2-candidate comparison does not need the
    full order, only the winner.  So the useful statistic is: when the reference
    says A > B by at least X cp, does pinning also say A > B?  Swept over X, on
    both references, this gives the operating threshold for a usable comparison.

Control: the same sweep against the UNRESTRICTED bestmove as the reference for the
top pair, which must be 100% by construction and proves the sweep can see its own
trivial case.

Run: python3 job3/rank_why.py
Writes job3/rank_why.txt, job3/rank_why.csv
"""
import csv
import itertools
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402
from rank_final import multipv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12


def main():
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]

    rows, out = [], []
    n = 0
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            continue
        cmdpos = f"position fen {fen}"
        p1 = engine.run_session(cmdpos, f"go depth {DEPTH}")
        if p1.fatal:
            continue
        order1, sc1, mr1 = multipv(fen, DEPTH, 5)
        if len(order1) < 5 or mr1.fatal:
            continue
        if not (order1[0] == p1.bestmove and sc1[order1[0]] == p1.signed_score):
            continue
        cand = order1[:5]
        _, sc3, mr3 = multipv(fen, DEPTH, 5, restricted=cand)
        if len(sc3) < 5 or mr3.fatal:
            continue
        pinned = {}
        for mv in cand:
            r = engine.run_session(cmdpos, f"go depth {DEPTH} searchmoves {mv}")
            if r.fatal or r.signed_score is None:
                break
            pinned[mv] = r.signed_score
        if len(pinned) < 5:
            continue
        n += 1
        for a, b in itertools.combinations(cand, 2):
            ref_gap = sc3[a] - sc3[b]
            pin_gap = pinned[a] - pinned[b]
            rows.append(dict(idx=idx, a=a, b=b, ref_gap=ref_gap, pin_gap=pin_gap,
                             same=int((ref_gap > 0) == (pin_gap > 0)),
                             ref_a=sc3[a], ref_b=sc3[b], pin_a=pinned[a], pin_b=pinned[b],
                             top_pair=int({a, b} == {cand[0], cand[1]})))

    with open(os.path.join(HERE, "rank_why.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    out += [f"positions used {n}, pair comparisons {len(rows)}", "",
            "== COMPRESSION (pinned gap / reference gap) =="]
    ratios = [abs(r["pin_gap"]) / abs(r["ref_gap"]) for r in rows if r["ref_gap"] != 0]
    ratios.sort()
    if ratios:
        m = len(ratios)
        out.append(f"pairs with a nonzero reference gap: {m}")
        out.append(f"median ratio {ratios[m // 2]:.3f}   10th pct {ratios[m // 10]:.3f}   "
                   f"90th pct {ratios[9 * m // 10]:.3f}   max {ratios[-1]:.3f}")

    out += ["", "== OPERATING THRESHOLD: agreement only for pairs the reference separates by >= X ==",
            "X cp | pairs | agree | fraction"]
    for x in (0, 1, 5, 10, 20, 30, 50, 75, 100):
        sub = [r for r in rows if abs(r["ref_gap"]) >= x]
        if sub:
            a = sum(r["same"] for r in sub)
            out.append(f"{x:4d} | {len(sub)} | {a}/{len(sub)} | {a / len(sub):.3f}")

    out += ["", "== CONTROL: top pair only, pinned winner vs reference winner =="]
    top = [r for r in rows if r["top_pair"]]
    out.append(f"top pairs: {sum(r['same'] for r in top)}/{len(top)}")

    text = "\n".join(out)
    with open(os.path.join(HERE, "rank_why.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
