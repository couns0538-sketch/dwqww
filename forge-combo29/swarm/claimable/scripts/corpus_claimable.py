#!/usr/bin/env python3
"""corpus_claimable.py — differential over roots that ARE claimable, built deliberately.

The self-play sweeps never reached a claimable root (a game ends before the counter fills),
so they establish only that the fix is inert on ordinary boards. This sweep takes real
endgame positions and sets the fifty-move counter to 100 in the FEN, which is exactly the
condition the rule keys on. It is a legitimate construction: the counter is a FEN field, and
100 is the claimable value the fixtures also use.

For every root, python-chess classifies it, and the classification decides whether a
difference is EXPLAINED:
     claimable and >=1 clock-resetting move and no mate  -> the rule may fire
     otherwise                                            -> an unexpected difference

Usage: corpus_claimable.py A_EXE B_EXE
"""
import io
import json
import sys

import chess
import chess.pgn

sys.path.insert(0, "/home/ubuntu/work")
from corpus_diff import Engine  # noqa: E402

# positions from both sweeps' seeds plus tactical middlegame/endgame material, hand-checked
# valid by python-chess below (the assert fails the run if one is not).
SEEDS = [
    "4k3/8/8/8/8/8/8/Q3K2r w - - 0 1",
    "4k3/8/8/8/8/8/8/R3K2r w - - 0 1",
    "4k3/8/8/8/8/8/8/Q3K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/R3K3 w - - 0 1",
    "4k3/pp6/8/8/8/8/8/Q3K3 w - - 0 1",
    "4k3/p7/8/8/8/8/8/R3K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/BN2K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/Q2nK3 w - - 0 1",
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 w - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "8/8/8/4k3/8/8/4P3/4K2R w - - 0 1",
    "8/8/8/3k4/8/8/3P4/3K3R w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
    "1r4k1/pp6/8/8/8/8/P7/3Q2K1 b - - 0 1",
    "8/8/4k3/8/8/8/4P3/4K2Q w - - 0 1",
]


def classify(b):
    resets = []
    for m in b.legal_moves:
        piece = b.piece_at(m.from_square)
        if (piece and piece.piece_type == chess.PAWN) or b.is_capture(m):
            resets.append(m.uci())
    mates = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            mates.append(m.uci())
    return {"halfmove": b.halfmove_clock, "claimable": True, "resets": len(resets),
            "mates": mates, "insufficient": b.is_insufficient_material()}


def explain_arm(info, differs):
    """Which arm of the repair can account for a difference at this root, if any.

    The composed build has TWO arms and they fire on different roots, so a single
    "claimable and no mate" predicate mislabels the mate-bearing roots as anomalies:
      mate_first   a mate exists -> the mate-first scan cancels the adjudication
      clock_reset  no mate, but >=1 legal move is a pawn move or a capture
      claim_stands otherwise: no reset available, so the claim is unavoidable
    """
    if not differs:
        return None
    if info["halfmove"] < 100:
        return "UNEXPECTED (not claimable at all)"
    if info["mates"]:
        return "mate_first"
    if info["resets"] > 0:
        return "clock_reset"
    return "UNEXPECTED (claim unavoidable yet the answer moved)"


def main():
    a, b_eng = Engine(sys.argv[1]), Engine(sys.argv[2])
    rows = []
    try:
        for seed in SEEDS:
            base = chess.Board(seed)
            assert base.is_valid(), f"bad seed {seed}"
            for hm in (99, 100):
                b = base.copy()
                b.halfmove_clock = hm
                fen = b.fen()
                pos = f"position fen {fen}"
                ra = a.search(pos, 10)
                rb = b_eng.search(pos, 10)
                info = classify(b)
                info["claimable"] = hm >= 100
                differs = (ra["bestmove"] != rb["bestmove"] or ra["score"] != rb["score"]
                           or ra["nodes"] != rb["nodes"])
                arm = explain_arm(info, differs)
                rows.append({"seed": seed, "fen": fen, "halfmove": hm, **info,
                             "a": ra, "b": rb, "differs": differs, "arm": arm,
                             "explained": arm in ("mate_first", "clock_reset")})
    finally:
        a.quit()
        b_eng.quit()

    diff = [r for r in rows if r["differs"]]
    unexplained = [r for r in diff if not r["explained"]]
    # The two arms must BOTH be observed, or the sweep cannot tell "arm inert" from
    # "arm never reached" — the shape §7 calls a check that declines to evaluate.
    arms = {}
    for r in diff:
        arms[r["arm"]] = arms.get(r["arm"], 0) + 1
    s = {
        "roots": len(rows),
        "hm99_roots": len([r for r in rows if r["halfmove"] == 99]),
        "hm100_roots": len([r for r in rows if r["halfmove"] == 100]),
        "hm100_with_reset": len([r for r in rows if r["halfmove"] == 100 and r["resets"] > 0]),
        "hm100_no_reset": len([r for r in rows if r["halfmove"] == 100 and r["resets"] == 0]),
        "hm100_with_mate": len([r for r in rows if r["halfmove"] == 100 and r["mates"]]),
        "differing": len(diff),
        "hm99_differing": len([r for r in diff if r["halfmove"] == 99]),
        "differences_by_arm": arms,
        "UNEXPLAINED_DIFF": len(unexplained),
        "unexplained": unexplained[:5],
    }
    json.dump({"summary": s, "rows": rows},
              open("/home/ubuntu/work/ev/corpus_claimable.json", "w"), indent=2)
    print(json.dumps(s, indent=2))

    # machine gates: no difference below the clock-100 boundary, both arms observed, and
    # no difference on a root where the claim genuinely cannot be avoided
    ok = (not unexplained and s["hm99_differing"] == 0
          and arms.get("mate_first", 0) > 0 and arms.get("clock_reset", 0) > 0)
    print("\nGATES:",
          "hm99 clean:", s["hm99_differing"] == 0,
          "| both arms observed:", arms.get("mate_first", 0) > 0 and arms.get("clock_reset", 0) > 0,
          "| no unexplained:", not unexplained)
    print("VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
