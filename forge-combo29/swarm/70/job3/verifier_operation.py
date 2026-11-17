"""Job 3c: THE VERIFIER'S OPERATION, tested directly.

A verifier does not ask for a full ordering.  It asks: "of these candidates, which
is better?" by pinning each one alone and comparing the pinned numbers.  So the
test is:

  plain `go depth D` says move B with score S.
  pin B alone -> sB.  Pin each other candidate x alone -> sx.
  Is sB >= sx for every x?  If not, the verifier's own procedure contradicts the
  engine's own answer, and its verdict is not the engine's.

This avoids every reference-construction problem of job3 (MultiPV's separate
worker, restricted MultiPV being itself a restriction).  The reference here is the
PLAIN SEARCH, which is the engine's answer by definition and which job3 measured
to be deterministic at 60/60.

Candidates are taken from an unrestricted MultiPV 5 so that they are genuinely
the engine's top five, and B is forced to be the plain bestmove.

Also reported: the pin-arm's own winner (highest pinned score among the
candidates).  If the pin arm's winner is not B, that position's 2-candidate
comparison is WRONG in the strongest sense.

Run: python3 job3/verifier_operation.py [--limit N]
Writes job3/verifier_operation.txt, job3/verifier_operation.csv
"""
import csv
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402
from rank_final import multipv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    rows, out = [], []
    n = 0
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            out.append(f"SKIP {fen}: perft1 {got} != {len(legal)}")
            continue
        cmdpos = f"position fen {fen}"
        plain = engine.run_session(cmdpos, f"go depth {DEPTH}")
        if plain.fatal or not plain.bestmove or plain.bestmove == "0000":
            continue
        order, _, _ = multipv(fen, DEPTH, 5)
        cand = [plain.bestmove] + [m for m in order if m != plain.bestmove]
        cand = cand[:5]
        pinned = {}
        for mv in cand:
            r = engine.run_session(cmdpos, f"go depth {DEPTH} searchmoves {mv}")
            if r.fatal or r.signed_score is None:
                pinned = {}
                break
            pinned[mv] = r.signed_score
        if len(pinned) < len(cand):
            continue
        n += 1
        B = plain.bestmove
        sB = pinned[B]
        others = [m for m in cand if m != B]
        beaten_by = [m for m in others if pinned[m] > sB]
        tied_by = [m for m in others if pinned[m] == sB]
        pin_winner = max(cand, key=lambda m: (pinned[m], -cand.index(m)))
        rows.append(dict(idx=idx, fen=fen, plain_move=B, plain_score=plain.signed_score,
                         pinB=sB, pin_winner=pin_winner,
                         n_cand=len(cand), n_beaten=len(beaten_by),
                         beaten=" ".join(beaten_by), tied=" ".join(tied_by),
                         winner_ok=int(pin_winner == B),
                         all_others_below=int(not beaten_by and not tied_by),
                         pin_spread=max(pinned.values()) - min(pinned.values())))
        out.append(f"[{idx:2d}] plain {B} {plain.signed_score} pinB {sB} "
                   f"winner {pin_winner} {'OK' if pin_winner == B else 'WRONG'} "
                   f"beaten {beaten_by} tied {tied_by} | pins {pinned}")

    with open(os.path.join(HERE, "verifier_operation.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    out += ["", "== THE VERIFIER'S OPERATION (pin each candidate alone) ==",
            f"positions: {n}",
            f"pin arm's winner == plain bestmove                    : "
            f"{sum(r['winner_ok'] for r in rows)}/{n}",
            f"pinned bestmove strictly above ALL other candidates    : "
            f"{sum(r['all_others_below'] for r in rows)}/{n}",
            f"positions where some other candidate beat the best move: "
            f"{sum(1 for r in rows if r['n_beaten']) }/{n}"]
    for k in (1, 2, 3, 4):
        sub = [r for r in rows if r["n_beaten"] == k]
        if sub:
            out.append(f"  exactly {k} candidate(s) beat it: {len(sub)}/{n} "
                       f"(idx {[r['idx'] for r in sub]})")
    text = "\n".join(out)
    with open(os.path.join(HERE, "verifier_operation.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
