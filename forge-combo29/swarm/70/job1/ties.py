"""Job 1: when the answer changes under `searchmoves <all legal>`, is it the
EQUAL-SCORING ties that flip?

Instrument.  ties2/ties3/ties5 are positions where exactly 2/3/5 legal moves are
PROVEN mate in 1 by python-chess.  Every one of those moves scores the same at the
root -- mate -- so no evaluation term can separate them and no depth can.  If
"naming all legal moves reorders equal-scoring moves", these are the positions in
which it must show: the winner among the tie set is decided by move order alone.

Also measured on the same positions:
  * pin the single best move   -> move must be preserved (VACUOUS check)
  * pin each tie move alone    -> rank/score comparison
  * pin the whole legal list   -> the treatment

Run: python3 job1/ties.py
Writes job1/ties.csv, job1/ties.txt
"""
import csv
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTHS = (8, 10, 12)
SETS = ("ties2", "ties3", "ties5")


def load(name):
    path = os.path.join(HERE, f"{name}.epd")
    with open(path) as fh:
        return [l.strip() for l in fh if l.strip()]


def is_mate(r):
    return r is not None and r.score_kind == "mate" and r.score is not None and r.score > 0


def main():
    rows = []
    lines = []
    for setname in SETS:
        fens = load(setname)
        for idx, fen in enumerate(fens):
            board = chess.Board(fen)
            legal = [m.uci() for m in board.legal_moves]
            mates1 = []
            for m in board.legal_moves:
                board.push(m)
                if board.is_checkmate():
                    mates1.append(m.uci())
                board.pop()

            # Independent board-identity check: perft-1 must equal python-chess.
            got, err, _ = engine.perft1(fen)
            if got != len(legal):
                lines.append(f"SKIP {fen}: perft1 {got} != python-chess {len(legal)} err={err}")
                continue

            for depth in DEPTHS:
                base = engine.run_session(f"position fen {fen}", f"go depth {depth}")
                allm = engine.run_session(f"position fen {fen}",
                                          f"go depth {depth} searchmoves {' '.join(legal)}")
                pin = None
                if base.bestmove and base.bestmove != "0000":
                    pin = engine.run_session(f"position fen {fen}",
                                             f"go depth {depth} searchmoves {base.bestmove}")
                for r in (base, allm, pin):
                    if r is not None and r.fatal:
                        lines.append(f"FATAL {r.fatal} on {fen} d{depth}")

                tie_scores = {}
                for tm in mates1:
                    r = engine.run_session(f"position fen {fen}",
                                           f"go depth {depth} searchmoves {tm}")
                    tie_scores[tm] = r.signed_score
                    if r.fatal:
                        lines.append(f"FATAL tie {tm} {r.fatal} {fen} d{depth}")

                row = dict(
                    set=setname, idx=idx, fen=fen, depth=depth, legal=len(legal),
                    n_mates1=len(mates1), mate_moves=" ".join(mates1),
                    base_move=base.bestmove, base_score=base.score,
                    all_move=allm.bestmove, all_score=allm.score,
                    pin_move=pin.bestmove if pin else "",
                    pin_score=pin.score if pin else "",
                    base_is_mate=is_mate(base), all_is_mate=is_mate(allm),
                    tie_scores=json.dumps(tie_scores), tie_picks=" ".join(sorted(tie_scores)),
                )
                rows.append(row)

                chg = "CHANGED" if base.bestmove != allm.bestmove else "same"
                lines.append(
                    f"{setname}[{idx}] d{depth} legal {len(legal):2d} mates1 {len(mates1)} "
                    f"base {base.bestmove} {base.score_kind}{base.score} | "
                    f"all {allm.bestmove} {allm.score_kind}{allm.score} -> {chg} | "
                    f"pin {row['pin_move']} {row['pin_score']}")

    fields = list(rows[0].keys())
    with open(os.path.join(HERE, "ties.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = []
    for setname in SETS:
        for depth in DEPTHS:
            sub = [r for r in rows if r["set"] == setname and r["depth"] == depth]
            n = len(sub)
            changed = sum(1 for r in sub if r["base_move"] != r["all_move"])
            base_mate = sum(1 for r in sub if r["base_is_mate"])
            all_mate = sum(1 for r in sub if r["all_is_mate"])
            score_eq = sum(1 for r in sub if r["base_score"] == r["all_score"])
            summary.append(
                f"{setname:7s} d{depth:2d}: bestmove changed {changed}/{n} | "
                f"base reported mate {base_mate}/{n} | all-legal reported mate {all_mate}/{n} | "
                f"score equal {score_eq}/{n}")

    text = "\n".join(lines + ["", "== SUMMARY =="] + summary)
    with open(os.path.join(HERE, "ties.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
