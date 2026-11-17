"""Job 2: is the pinned-score distortion a function of HOW MANY moves are pinned?

Pin count k in {1, 2, 4, 8, all}, on the same 40 pinpool positions at depth 12.
For each k the pinned set is the first k moves in the engine's own UNRESTRICTED
best-first order, which we obtain from MultiPV so that "first k" is the engine's
ranking and not ours.  k = 1 pins the engine's own best move (what a verifier does).

Two measures per k:
  move_preserved : the pinned search still returns the UNRESTRICTED best move
  score_delta    : unrestricted score minus pinned score, signed cp

Prediction stated before the run:
  if the distortion is about WHICH SET of moves the root sees (fewer root moves =
  smaller root effort / different node distribution), |delta| falls as k rises and
  reaches 0 at k = all-but-with-the-TT-bug... no: k = all is the full list, which we
  already know perturbs.  So the shape to look for is a NON-MONOTONE curve: small k
  distorts because the best move's search sees a different alpha history, large k
  distorts because of the root TT/IIR change found in job 1.

Run: python3 job2/pin_count.py [--limit N]
Writes job2/pin_count.csv, job2/pin_count.txt
"""
import csv
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12
KS = (1, 2, 4, 8, "all")


def multipv_order(fen, depth):
    """The engine's own best-first order, from a MultiPV 8 search."""
    opts = list(engine.S14) + [("MultiPV", "8")]
    r = engine.run_session(f"position fen {fen}", f"go depth {depth}", options=opts)
    order = []
    for line in r.raw_go.split("\n"):
        if " multipv " in line and " pv " in line:
            mv = line.split(" pv ")[1].split()[0]
            if mv not in order:
                order.append(mv)
    return order, r


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
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
        base = engine.run_session(f"position fen {fen}", f"go depth {DEPTH}")
        order, _ = multipv_order(fen, DEPTH)
        # k=1 must be EXACTLY what a verifier does: pin the move the unmodified
        # search returned.  MultiPV 8 runs its secondary lines in a separate worker
        # and its first move can differ from the plain search's bestmove, so the
        # plain bestmove is forced to rank 0 here and the MultiPV order fills in
        # the rest of the engine's ranking.
        ranked = [m for m in order if m != base.bestmove]
        if base.bestmove and base.bestmove != "0000":
            ranked = [base.bestmove] + ranked
        multipv_first = order[0] if order else None
        if multipv_first and multipv_first != base.bestmove:
            lines.append(f"[{idx:2d}] NOTE multipv-8 first move {multipv_first} != plain bestmove {base.bestmove}")
        lines.append(f"[{idx:2d}] base {base.bestmove} {base.score}  ranked {ranked[:8]}")

        for k in KS:
            if k == "all":
                pinned = legal
            else:
                pinned = ranked[:min(k, len(ranked))]
            r = engine.run_session(f"position fen {fen}",
                                   f"go depth {DEPTH} searchmoves {' '.join(pinned)}")
            if r.fatal:
                lines.append(f"   k={k}: FATAL {r.fatal}")
                continue
            delta = (base.signed_score - r.signed_score) if (base.score is not None and r.score is not None) else None
            rows.append(dict(idx=idx, fen=fen, k=str(k), n_pinned=len(pinned),
                             base_move=base.bestmove, base_score=base.score,
                             pin_move=r.bestmove, pin_score=r.score, delta=delta,
                             preserved=int(r.bestmove == base.bestmove),
                             contains_best=int(base.bestmove in pinned)))
            lines.append(f"   k={k:>3} pinned {len(pinned):2d} -> {r.bestmove} {r.score} "
                         f"delta {delta} {'preserved' if r.bestmove == base.bestmove else 'CHANGED'}")

    with open(os.path.join(HERE, "pin_count.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    lines += ["", "== PIN-COUNT TABLE (depth 12) ==",
              "k | n | move preserved | score delta = 0 | |delta| >= 10 | median |delta|"]
    for k in KS:
        sub = [r for r in rows if r["k"] == str(k) and r["delta"] is not None]
        n = len(sub)
        if not n:
            continue
        pres = sum(r["preserved"] for r in sub)
        eq = sum(1 for r in sub if r["delta"] == 0)
        big = sum(1 for r in sub if abs(r["delta"]) >= 10)
        deltas = sorted(abs(r["delta"]) for r in sub)
        med = deltas[n // 2]
        lines.append(f"{k:>4} | {n} | {pres}/{n} | {eq}/{n} | {big}/{n} | {med}")
    text = "\n".join(lines)
    with open(os.path.join(HERE, "pin_count.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
