"""Close the open thread from FINDINGS F1.

F1 showed that restoring the root TT store (scratch patch A) makes
`searchmoves <all legal>` reproduce the unrestricted answer exactly, 60/60 moves
and 60/60 scores.  That makes the all-legal CONTROL valid.  It does NOT follow
that a single-move root -- what a verifier actually does -- returns the score that
move had inside the full search.  A one-move root is still a different search.

This script answers that directly.  For each position and each of the engine's
own top 5 moves, four numbers:

  intree_base   score inside one unrestricted MultiPV 5 search, BASE build
  pinned_base   score when searched alone with searchmoves, BASE build
  intree_pA     same, PATCH A build (root TT store restored)
  pinned_pA     same, PATCH A build

Reported:
  (1) pinned_base == intree_base          -- the original 10/265 result, as control
  (2) pinned_pA   == intree_pA            -- does the fix restore a PINNED score
  (3) pinned_pA   == intree_base          -- does it land on the engine's real value

(3) is the number a harness author cares about, because intree_base is the number
the engine actually believes.

Power: the original measurement was 10/265.  If the fix were irrelevant, (2) and
(3) would land near 10/265 again; the 95% interval on 10/265 is 0.021-0.068, so an
observed rate above ~0.10 is outside it and the fix would be doing something.

Run: python3 job1/fix_vs_pinned_score.py [--limit N]
Writes job1/fix_vs_pinned_score.txt, job1/fix_vs_pinned_score.csv
"""
import csv
import os
import statistics
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "job3"))
import engine  # noqa: E402
from rank_final import multipv  # noqa: E402

DEPTH = 12
BASE = "/tmp/build-rel/forge"
PATCH_A = "/tmp/build-pA/forge"


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    rows, out = [], []
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen, engine=BASE)
        if got != len(legal):
            out.append(f"SKIP {fen}: perft1 {got} != {len(legal)}")
            continue
        cmdpos = f"position fen {fen}"

        order_b, intree_b, mr_b = multipv(fen, DEPTH, 5)
        if len(order_b) < 5 or mr_b.fatal:
            continue
        plain_b = engine.run_session(cmdpos, f"go depth {DEPTH}", engine=BASE)
        if plain_b.fatal:
            continue
        # only keep positions where the BASE reference is trustworthy
        if not (order_b[0] == plain_b.bestmove and intree_b[order_b[0]] == plain_b.signed_score):
            continue

        order_a, intree_a, mr_a = multipv(fen, DEPTH, 5)
        if len(order_a) < 5 or mr_a.fatal:
            continue

        ok = True
        for mv in order_b:
            pb = engine.run_session(cmdpos, f"go depth {DEPTH} searchmoves {mv}", engine=BASE)
            pa = engine.run_session(cmdpos, f"go depth {DEPTH} searchmoves {mv}", engine=PATCH_A)
            if pb.fatal or pa.fatal or pb.signed_score is None or pa.signed_score is None:
                out.append(f"SKIP {idx}/{mv}: {pb.fatal}/{pa.fatal}")
                ok = False
                break
            rows.append(dict(
                idx=idx, fen=fen, move=mv,
                intree_base=intree_b[mv], pinned_base=pb.signed_score,
                intree_pA=intree_a.get(mv), pinned_pA=pa.signed_score,
                is_top=int(mv == order_b[0]),
            ))
        if not ok:
            continue

    with open(os.path.join(HERE, "fix_vs_pinned_score.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def tally(pred, label, filt=None):
        sub = [r for r in rows if (filt is None or filt(r))]
        vals = [pred(r) for r in sub]
        n = len(vals)
        eq = sum(1 for v in vals if v == 0)
        ge10 = sum(1 for v in vals if abs(v) >= 10)
        ge50 = sum(1 for v in vals if abs(v) >= 50)
        out.append(f"{label:52s} n {n:3d}  identical {eq:3d}/{n}  "
                   f"|d|>=10 {ge10:3d}/{n}  |d|>=50 {ge50:3d}/{n}  "
                   f"mean {statistics.mean(vals):+7.1f}  sd {statistics.pstdev(vals):6.1f}")

    out.insert(0, f"engine base {BASE}")
    out.insert(1, f"engine pA   {PATCH_A}   (scratch build, root TT store restored)")
    out.insert(2, f"depth {DEPTH}")
    out.insert(3, "")
    n_pos = len({r["idx"] for r in rows})
    out.append(f"positions {n_pos}, (move, position) pairs {len(rows)}")
    out.append("")
    out.append("== CONTROL: the original measurement, reproduced ==")
    tally(lambda r: r["pinned_base"] - r["intree_base"], "pinned_base  - intree_base   (BASE build)")
    tally(lambda r: r["pinned_base"] - r["intree_base"], "  ...top move only",
          filt=lambda r: r["is_top"])
    out.append("")
    out.append("== THE QUESTION: does the fix restore a PINNED score? ==")
    tally(lambda r: r["pinned_pA"] - r["intree_pA"], "pinned_pA    - intree_pA     (PATCH A build)")
    tally(lambda r: r["pinned_pA"] - r["intree_pA"], "  ...top move only",
          filt=lambda r: r["is_top"])
    out.append("")
    out.append("== THE NUMBER A HARNESS AUTHOR NEEDS ==")
    tally(lambda r: r["pinned_pA"] - r["intree_base"], "pinned_pA    - intree_base   (fix vs the engine's real value)")
    tally(lambda r: r["pinned_base"] - r["intree_base"], "pinned_base  - intree_base   (same comparison, no fix)",
          filt=lambda r: r["is_top"])

    text = "\n".join(out)
    with open(os.path.join(HERE, "fix_vs_pinned_score.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
