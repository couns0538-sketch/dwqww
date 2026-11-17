"""Job 1 causal test: is the all-legal-bestmove change caused by the restricted
root never storing a TT entry?

Mechanism read off the source (src/search.cpp, base 6b98f217):
  2093  if (excluded.is_none() && !(root_node && root_restricted_)) { store_tt(...); }
  1784  if (... depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;

A restricted root therefore (a) never publishes a root TT move and (b) makes every
root iteration take the IIR depth reduction, because tt_move is always none there.
Both change the search, not merely the order of equal moves.

Three arms on the SAME 60 pinpool positions at depth 12:
  base      unmodified engine, plain `go depth 12`
  base_all  unmodified engine, `go depth 12 searchmoves <all legal>`
  pA_all    SCRATCH PATCH A engine (restricted root DOES store), same searchmoves
Plus two option arms on the UNMODIFIED engine (no rebuild needed):
  iir20_all `setoption IirDepth 20` + searchmoves <all legal>   (kills IIR at d12)

Prediction stated before the run:
  If the root TT store is the mechanism, pA_all must agree with base far more often
  than base_all does, and IirDepth 20 must do the same.  If neither moves the
  agreement, the mechanism is elsewhere and I say so.

Run: python3 job1/causal_tt_iir.py [--limit N]
Writes job1/causal_tt_iir.csv, job1/causal_tt_iir.txt
"""
import csv
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12
PATCH_A = "/tmp/build-pA/forge"


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    iir20 = [(k, v) for k, v in engine.S14 if k != "IirDepth"] + [("IirDepth", "20")]
    rows, lines = [], []
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        pos = f"position fen {fen}"
        sm = f"go depth {DEPTH} searchmoves {' '.join(legal)}"
        base = engine.run_session(pos, f"go depth {DEPTH}")
        b_all = engine.run_session(pos, sm)
        p_all = engine.run_session(pos, sm, engine=PATCH_A)
        i_all = engine.run_session(pos, sm, options=iir20)
        if any(r.fatal for r in (base, b_all, p_all, i_all)):
            lines.append(f"FATAL {fen}: {[r.fatal for r in (base, b_all, p_all, i_all)]}")
            continue
        row = dict(idx=idx, fen=fen, base=base.bestmove, base_score=base.score,
                   base_all=b_all.bestmove, base_all_score=b_all.score,
                   pA_all=p_all.bestmove, pA_all_score=p_all.score,
                   iir20_all=i_all.bestmove, iir20_all_score=i_all.score,
                   moved_base=int(base.bestmove != b_all.bestmove),
                   moved_pA=int(base.bestmove != p_all.bestmove),
                   moved_iir=int(base.bestmove != i_all.bestmove))
        rows.append(row)
        lines.append(
            f"[{idx:2d}] base {row['base']:5s} {row['base_score']:>6} | "
            f"base_all {row['base_all']:5s} {row['base_all_score']:>6} "
            f"{'M' if row['moved_base'] else '.'} | "
            f"pA_all {row['pA_all']:5s} {row['pA_all_score']:>6} "
            f"{'M' if row['moved_pA'] else '.'} | "
            f"iir20 {row['iir20_all']:5s} {row['iir20_all_score']:>6} "
            f"{'M' if row['moved_iir'] else '.'}")

    with open(os.path.join(HERE, "causal_tt_iir.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    mb = sum(r["moved_base"] for r in rows)
    mp = sum(r["moved_pA"] for r in rows)
    mi = sum(r["moved_iir"] for r in rows)
    lines += ["", "== CAUSAL TEST, depth 12, pinpool ==",
              f"positions: {n}",
              f"base vs base_all  : bestmove moved {mb}/{n}",
              f"base vs pA_all    : bestmove moved {mp}/{n}   (patch A: restricted root stores TT)",
              f"base vs iir20_all : bestmove moved {mi}/{n}   (IIR disabled at d12)"]
    text = "\n".join(lines)
    with open(os.path.join(HERE, "causal_tt_iir.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
