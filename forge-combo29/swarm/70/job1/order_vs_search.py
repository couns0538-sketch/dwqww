"""Job 1 contrast on ORDINARY positions: when `searchmoves <all legal>` changes the
bestmove, does the score change too?

Two competing accounts of the 6/25 and 5/15 changes:
  (H-order)  the restriction reorders EQUAL-SCORING moves; the same score, a
             different move.  The engine's answer did not change, only its tie-break.
  (H-search) the restriction changes the search itself (fewer nodes available to
             the root, IIR reduction, no root TT store), so a DIFFERENT score is
             reached and the move that score picks is different.

Discriminator: among positions where the bestmove changed, the fraction with an
UNCHANGED reported score.  Under H-order that fraction is 1; under H-search it is low.
Power: see POWER below -- stated before the run.

Run: python3 job1/order_vs_search.py [--limit N]
Writes job1/order_vs_search.csv, job1/order_vs_search.txt
"""
import csv
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTHS = (10, 12)


def load(name):
    with open(os.path.join(HERE, f"{name}.epd")) as fh:
        return [l.strip() for l in fh if l.strip()]


def last_nodes(raw):
    best = 0
    for line in raw.split("\n"):
        if " nodes " in line:
            try:
                best = int(line.split(" nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
    return best


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    fens = load("pinpool")
    if limit:
        fens = fens[:limit]

    rows, lines = [], []
    for idx, fen in enumerate(fens):
        board = chess.Board(fen)
        legal = [m.uci() for m in board.legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            lines.append(f"SKIP {fen}: perft1 {got} != {len(legal)} err={err}")
            continue
        for depth in DEPTHS:
            base = engine.run_session(f"position fen {fen}", f"go depth {depth}")
            allm = engine.run_session(f"position fen {fen}",
                                      f"go depth {depth} searchmoves {' '.join(legal)}")
            if base.fatal or allm.fatal:
                lines.append(f"FATAL base={base.fatal} all={allm.fatal} {fen} d{depth}")
                continue
            rows.append(dict(
                idx=idx, fen=fen, depth=depth, legal=len(legal),
                base_move=base.bestmove, base_score=base.score, base_kind=base.score_kind,
                all_move=allm.bestmove, all_score=allm.score, all_kind=allm.score_kind,
                moved=int(base.bestmove != allm.bestmove),
                score_delta=(base.signed_score - allm.signed_score),
                nodes_base=last_nodes(base.raw_go), nodes_all=last_nodes(allm.raw_go),
            ))
            r = rows[-1]
            lines.append(
                f"pinpool[{idx}] d{depth} legal {len(legal):2d} "
                f"base {r['base_move']} {r['base_kind']}{r['base_score']} n{r['nodes_base']} | "
                f"all {r['all_move']} {r['all_kind']}{r['all_score']} n{r['nodes_all']} | "
                f"{'MOVED' if r['moved'] else 'same '} delta {r['score_delta']}")

    with open(os.path.join(HERE, "order_vs_search.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    moved = [r for r in rows if r["moved"]]
    n = len(rows)
    lines += ["", "== DISCRIMINATOR =="]
    lines.append(f"searches: {n}")
    lines.append(f"bestmove changed: {len(moved)}/{n}")
    if moved:
        same_score = sum(1 for r in moved if r["score_delta"] == 0)
        lines.append(f"of the {len(moved)} changes, score UNCHANGED: {same_score}/{len(moved)}")
        ge10 = sum(1 for r in moved if abs(r["score_delta"]) >= 10)
        lines.append(f"of the {len(moved)} changes, |delta| >= 10 cp: {ge10}/{len(moved)}")
        lines.append("per-change deltas: " + " ".join(str(r["score_delta"]) for r in moved))
    unchanged_score_all = sum(1 for r in rows if r["score_delta"] == 0)
    lines.append(f"all searches with score unchanged: {unchanged_score_all}/{n}")

    text = "\n".join(lines)
    with open(os.path.join(HERE, "order_vs_search.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
