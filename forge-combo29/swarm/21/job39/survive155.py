#!/usr/bin/env python3
"""survive155.py EXE OUTDIR

Position 155's TRUE result, decided by the fifty-move counter, not by mate distance.

`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`: White has a bare king; Black has R+B+N. A bare king
against R+B+N is normally lost, BUT the halfmove counter is 18, so only 82 half-moves remain before
the fifty-move draw. So:
  - a line that reaches halfmove 100 alive is a DRAW for White;
  - a line mated before that is a LOSS for White.

The question is whether ANY White move survives 82 half-moves against Black's best play. This
script answers it directly: for each White root move, play Black with the engine and White with the
engine, and record the halfmove counter at the end; if it reaches 100 with no mate, that move DRAWS.

It also runs the same test with BOTH sides at a high node budget, and reports the counter reached
for each root move, so the answer does not depend on one play-out.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
POS155 = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    return e


def play(exe, outdir, tag, start_fen, first_move, go, max_plies=400):
    """Play out from after `first_move`, engine on both sides, and report how it ended."""
    e = eng(exe, os.path.join(outdir, tag + "_raw.txt"))
    b = chess.Board(start_fen)
    b.push_uci(first_move)
    plies = 1
    while plies < max_plies:
        if b.is_checkmate():
            e.close()
            return dict(end="checkmate", plies=plies, counter=b.halfmove_clock,
                        side_to_move=str(b.turn), loser=str(b.turn))
        if b.is_stalemate():
            e.close()
            return dict(end="stalemate", plies=plies, counter=b.halfmove_clock)
        if b.can_claim_fifty_moves() or b.halfmove_clock >= 100:
            e.close()
            return dict(end="fifty_move_draw", plies=plies, counter=b.halfmove_clock)
        if b.can_claim_threefold_repetition():
            e.close()
            return dict(end="threefold_draw", plies=plies, counter=b.halfmove_clock)
        if b.is_insufficient_material():
            e.close()
            return dict(end="insufficient", plies=plies, counter=b.halfmove_clock)
        e.position("position fen " + b.fen())
        try:
            lines = e.go(go, timeout=180)
        except Exception:
            e.close()
            return dict(end="ENGINE_ERROR", plies=plies, counter=b.halfmove_clock)
        bm = bestmove_of(lines)
        if not bm or bm == "0000":
            e.close()
            return dict(end="no_move", plies=plies, counter=b.halfmove_clock)
        try:
            b.push_uci(bm)
        except Exception:
            e.close()
            return dict(end="illegal_from_engine", plies=plies, counter=b.halfmove_clock,
                        move=bm)
        plies += 1
    e.close()
    return dict(end="CAPPED", plies=plies, counter=b.halfmove_clock)


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    b = chess.Board(POS155)
    # ASSERT the premise: White is the bare king at this root (this is what makes "survive" the draw)
    white_men = sum(len(b.pieces(t, chess.WHITE)) for t in
                    (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN))
    assert white_men == 0 and b.turn == chess.WHITE, "155's premise is wrong: white_men=%d turn=%s" % (white_men, b.turn)
    rows = ["| white move | go | ending | plies | halfmove counter at end | result for White |",
            "|---|---|---|---|---|---|"]
    R = {}
    for mv in [m.uci() for m in b.legal_moves]:
        for go in ("go nodes 20000", "go depth 16"):
            tag = "155_%s_%s" % (mv, go.replace(" ", "_"))
            r = play(exe, outdir, tag, POS155, mv, go)
            # White is the side to move at the root; White LOSES if mated, DRAWS if the counter ran out
            if r["end"] == "checkmate":
                # White is the side to move at the root and the BARE KING. Whose king is mated?
                # play() records b.turn AFTER the mating move, which is the LOSER's side.
                res = "LOSS" if r.get("loser") == "w" else "WIN"
                r["mated_side"] = r.get("loser")
            elif r["end"] in ("fifty_move_draw", "threefold_draw", "stalemate", "insufficient"):
                res = "DRAW"
            else:
                res = r["end"]
            R["%s|%s" % (mv, go)] = dict(r, result=res)
            rows.append("| %s | `%s` | %s | %d | %d | **%s** |" % (
                mv, go, r["end"], r["plies"], r["counter"], res))
    text = "\n".join(rows)
    text += ("\n\nThe board has halfmove counter 18 at the root, so a continuation must reach "
             "counter 100 to be a draw for the bare king. The engine's own play decides it here.\n")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()