"""Family 4: the fifty-move band, `missed iff H > 100 - p`.

§2 of forge-findings.md records a measured band: a mate delivered at ply `p`
against the root side is MISSED at halfmove clock `H` when `H > 100 - p`, and
found at `H <= 100 - p`. The boundary cells are the claim: at p=2, H=98 is
FOUND and H=99 is MISSED.

DIRECTION MATTERS, and getting it wrong is what this file exists to prevent.
In the §2 fixture the side to move is the side being MATED, so the correct
score is a NEGATIVE mate (`mate -1`), not a positive one. A first version of
this script counted "mate > 0" as found and therefore labelled H = 96/97/98 as
MISSED when the engine had answered correctly; that near-miss is recorded in
FINDINGS.md rather than quietly fixed.

Correct-answer rule used here, stated before the run:

    H <= 100 - p   ->  score must be `mate -k` (mate against the root side)
    H  > 100 - p   ->  the leaf draw rule fires: the miss, `cp 0`
    H >= 100       ->  the ROOT guard legitimately returns `cp 0`, 0 nodes,
                       because the side to move can claim the draw itself.
                       This is NOT the defect and is judged separately.

Both p = 2 and p = 4 are swept, so the band's dependence on the mate length
is exercised rather than assumed.
"""
import json
import sys
import chess

from forge_drv import Forge

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family4_fifty.json"

# §2's named fixture, p = 2: Black (the mated side) to move; both legal moves
# allow Ra8#, which is mate on the ply-2 half-move.
P2 = "6k1/8/5PPP/8/8/8/8/R6K b - - {hm} 40"
# §2's control: Black has pawn moves that reset the clock, so the draw is real.
P2_CTRL = "6k1/5ppp/8/8/8/8/8/R5NK b - - {hm} 40"

# p = 4 fixture: Black to move and NOT in check, so White's mate lands on ply 4
# (Black 1, White 2, Black 3, White mates 4). Verified with the independent
# oracle `force_mate_plies` == 4 below; every other ply count in the K+QvK set
# I tested gave 2 or 3, so this one is chosen rather than assumed.
P4 = "7k/8/5K2/8/8/8/8/Q7 b - - {hm} 40"


def force_mate_plies(board, limit=11):
    """Plies in which the side to move can FORCE mate, or None.
    Independent minimax -- no engine involvement, no pruning."""
    side = board.turn

    def force(b, plies):
        if b.is_checkmate():
            return b.turn != side
        if plies == 0:
            return False
        moves = list(b.legal_moves)
        if not moves:
            return False
        if b.turn == side:
            for m in moves:
                b.push(m)
                r = force(b, plies - 1)
                b.pop()
                if r:
                    return True
            return False
        for m in moves:
            b.push(m)
            r = force(b, plies - 1)
            b.pop()
            if not r:
                return False
        return True

    for n in range(1, limit + 1):
        if force(board, n):
            return n
    return None


def judge(p, hm, score, nodes):
    """Return (verdict, correct?). Pre-registered, direction-aware."""
    if hm >= 100:
        # Root guard: the side to move claims the draw. cp 0 / 0 nodes is right.
        ok = (score == ("cp", 0))
        return ("ROOT_GUARD_DRAW" if ok else f"UNEXPECTED {score}"), ok
    if score is not None and score[0] == "mate" and score[1] < 0:
        # found the mate against the root side
        missed_expected = hm > 100 - p
        if missed_expected:
            return "FOUND_DESPITE_BAND", False
        return "FOUND", True
    if score == ("cp", 0):
        missed_expected = hm > 100 - p
        if missed_expected:
            return "MISSED_AS_PREDICTED", True   # the reproduced defect
        return "MISSED_OUTSIDE_BAND", False
    return f"OTHER {score}", False


def main():
    cells = []
    with Forge(EXE) as eng:
        for hm in (95, 96, 97, 98, 99, 100, 101):
            fen = P2.format(hm=hm)
            b = chess.Board(fen)
            assert b.is_valid(), fen
            rec = eng.search(fen, "go depth 12")
            v, ok = judge(2, hm, rec.score(), rec.nodes())
            cells.append({"family": "p2_mate_in_1", "p": 2, "hm": hm, "fen": fen,
                          "legal": b.legal_moves.count(),
                          "bestmove": rec.bestmove, "score": rec.score(),
                          "nodes": rec.nodes(), "depth": rec.depth(),
                          "pv": rec.pv(), "verdict": v, "ok": ok})

        for hm in (95, 96, 97, 98, 99):
            fen = P4.format(hm=hm)
            b = chess.Board(fen)
            assert b.is_valid(), fen
            plies = force_mate_plies(b, 8)
            rec = eng.search(fen, "go depth 14")
            v, ok = judge(4, hm, rec.score(), rec.nodes())
            cells.append({"family": "p4_mate_in_2", "p": 4, "hm": hm, "fen": fen,
                          "legal": b.legal_moves.count(),
                          "oracle_mate_plies": plies,
                          "bestmove": rec.bestmove, "score": rec.score(),
                          "nodes": rec.nodes(), "depth": rec.depth(),
                          "pv": rec.pv(), "verdict": v, "ok": ok})

        for hm in (96, 97, 98, 99):
            fen = P2_CTRL.format(hm=hm)
            b = chess.Board(fen)
            assert b.is_valid(), fen
            rec = eng.search(fen, "go depth 12")
            # The draw is real here: every score is defensible as 0.00.
            v = "DRAW_REAL" if rec.score() == ("cp", 0) else f"SCORED {rec.score()}"
            cells.append({"family": "p2_control_clockreset", "p": 2, "hm": hm,
                          "fen": fen, "legal": b.legal_moves.count(),
                          "bestmove": rec.bestmove, "score": rec.score(),
                          "nodes": rec.nodes(), "depth": rec.depth(),
                          "pv": rec.pv(), "verdict": v,
                          "ok": rec.score() == ("cp", 0)})

    with open(OUT, "w") as f:
        json.dump(cells, f, indent=2)

    print(f"{'family':22} {'p':>2} {'hm':>4} {'verdict':24} {'ok':>5} "
          f"{'score':14} {'nodes':>6}")
    for c in cells:
        print(f"{c['family']:22} {c['p']:>2} {c['hm']:>4} {c['verdict']:24} "
              f"{str(c['ok']):>5} {str(c['score']):14} {str(c['nodes']):>6}")
    ok = sum(1 for c in cells if c["ok"])
    print(f"\n{ok}/{len(cells)} cells as predicted")
    print(f"wrote {OUT}")

    # ---- the band, stated as a reproduction -----------------------------
    for p in (2, 4):
        band = [c for c in cells if c.get("p") == p
                and c["family"].startswith(f"p{p}_mate")]
        if not band:
            continue
        found_at = [c["hm"] for c in band if c["verdict"] == "FOUND"]
        missed_at = [c["hm"] for c in band if c["verdict"] == "MISSED_AS_PREDICTED"]
        print(f"p={p} band: FOUND at H={found_at}, MISSED at H={missed_at}, "
              f"predicted boundary H>100-{p}={100-p}")


if __name__ == "__main__":
    main()
