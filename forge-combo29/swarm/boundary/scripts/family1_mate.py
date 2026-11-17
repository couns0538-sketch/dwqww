"""Family 1: one ply from checkmate.

Two halves, 50 positions each, constructed not found:

  A. SIDE TO MOVE HAS A MATE IN 1.  The engine must play it. Every legal
     mating move is accepted; any non-mating move is a MISS.

  B. THE OPPONENT HAS A MATE IN 1 NEXT MOVE.  The engine must play a move that
     denies it, when such a move exists. Playing into the mate is an ERROR.
     Positions with no escaping move are counted separately and excluded from
     the denominator, because there the correct answer is "mate against".

Search: `go depth 10` (the family is one ply from terminal; a deeper search
only makes a miss less excusable) plus a `go nodes 20000` cross-check so a
result is not an artefact of one budget.
"""
import json
import sys
import chess

from forge_drv import Forge, RefusedFen
import stalemate as S

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family1_mate.json"

GO_DEPTH = "go depth 10"
GO_NODES = "go nodes 20000"


def gen_mate_in_one(count=50):
    """Construct 50 distinct positions where the side to move mates in 1.

    Deterministic: sweeps queen/rook placements against a corner king in a
    fixed order, so the same 50 come back on every run.
    """
    out = []
    seen = set()
    corners = [chess.A8, chess.H8, chess.A1, chess.H1,
               chess.A7, chess.H7, chess.A2, chess.H2]
    for pt in (chess.QUEEN, chess.ROOK):
        for corner in corners:
            for wk in range(64):
                if chess.square_distance(wk, corner) <= 1 or wk == corner:
                    continue
                for wp in range(64):
                    if wp in (corner, wk):
                        continue
                    b = chess.Board(None)
                    b.set_piece_at(corner, chess.Piece(chess.KING, chess.BLACK))
                    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(wp, chess.Piece(pt, chess.WHITE))
                    b.turn = chess.WHITE
                    b.castling_rights = 0
                    b.ep_square = None
                    b.halfmove_clock = 0
                    b.fullmove_number = 40
                    if not b.is_valid():
                        continue
                    if b.is_checkmate() or b.is_stalemate():
                        continue
                    mates = S.mates_in_one(b)
                    if not mates:
                        continue
                    fen = b.fen()
                    if fen in seen:
                        continue
                    seen.add(fen)
                    out.append({"fen": fen, "mates": mates,
                                "material": "K" + chess.piece_symbol(pt).upper() + "vK",
                                "legal": b.legal_moves.count()})
                    if len(out) >= count:
                        return out
    return out


def gen_opponent_mate_threat(count=50):
    """Construct 50 positions where the side to move faces a mate in 1.

    Requires at least one move that denies the mate, so the family is about
    AVOIDANCE. Enumerated over a boxed king with an enemy queen/rook, keeping
    only positions where the threat is real and escapable.
    """
    out = []
    seen = set()
    # Mover's king is boxed by an enemy queen, with a defender piece able to
    # block or capture. Enumeration, not sampling.
    for ok in (chess.A8, chess.H8, chess.A1, chess.H1,
               chess.A7, chess.H7, chess.A2, chess.H2):
        for mk in range(64):
            if mk == ok or chess.square_distance(mk, ok) <= 1:
                continue
            for eq in range(64):
                if eq in (mk, ok):
                    continue
                for dp in range(64):
                    if dp in (mk, ok, eq):
                        continue
                    for dpt in (chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.QUEEN):
                        b = chess.Board(None)
                        b.set_piece_at(ok, chess.Piece(chess.KING, chess.BLACK))
                        b.set_piece_at(mk, chess.Piece(chess.KING, chess.WHITE))
                        b.set_piece_at(eq, chess.Piece(chess.QUEEN, chess.BLACK))
                        b.set_piece_at(dp, chess.Piece(dpt, chess.WHITE))
                        b.turn = chess.WHITE
                        b.castling_rights = 0
                        b.ep_square = None
                        b.halfmove_clock = 0
                        b.fullmove_number = 40
                        if not b.is_valid():
                            continue
                        # mover must not already be in check from a mate-in-1
                        # threat that is really a checkmate already
                        if b.is_checkmate() or b.is_stalemate():
                            continue
                        avoiding, losing = [], []
                        for mv in b.legal_moves:
                            b.push(mv)
                            if b.is_checkmate():
                                b.pop()
                                continue
                            if b.is_stalemate():
                                b.pop()
                                continue
                            if S.mates_in_one(b):
                                losing.append(mv.uci())
                            else:
                                avoiding.append(mv.uci())
                            b.pop()
                        if not avoiding or not losing:
                            continue
                        fen = b.fen()
                        if fen in seen:
                            continue
                        seen.add(fen)
                        out.append({"fen": fen, "avoid": avoiding,
                                    "lose": losing,
                                    "n_legal": b.legal_moves.count()})
                        if len(out) >= count:
                            return out
    return out


def run(fixtures, eng, go, judge, kind):
    rows = []
    for i, fx in enumerate(fixtures):
        fen = fx["fen"]
        pc = chess.Board(fen)
        row = {"i": i, "fen": fen, "go": go, "kind": kind}
        try:
            rec = eng.search(fen, go)
        except RefusedFen as e:
            row.update(refused=True, error=str(e))
            rows.append(row)
            continue
        row.update(bestmove=rec.bestmove, score=rec.score(), nodes=rec.nodes(),
                   depth=rec.depth(), pv=rec.pv(),
                   info_strings=rec.info_strings(),
                   n_infos=len(rec.infos))
        verdict, note = judge(fx, rec, pc)
        row["verdict"] = verdict
        row["note"] = note
        rows.append(row)
    return rows


def main():
    mate1 = gen_mate_in_one(50)
    threat = gen_opponent_mate_threat(50)
    print(f"constructed: mate_in_one={len(mate1)}, opp_threat={len(threat)}")

    result = {"mate_in_one": {}, "opponent_threat": {}}

    with Forge(EXE) as eng:
        for go, tag in ((GO_DEPTH, "depth10"), (GO_NODES, "nodes20000")):
            rows = run(mate1, eng, go, judge_mate1, "mate_in_one")
            result["mate_in_one"][tag] = rows
            hits = sum(1 for r in rows if r.get("verdict") == "PASS")
            print(f"  mate_in_one {tag}: {hits}/{len(rows)} played a mate")

            rows = run(threat, eng, go, judge_threat, "opponent_threat")
            result["opponent_threat"][tag] = rows
            ok = sum(1 for r in rows if r.get("verdict") == "PASS")
            print(f"  opp_threat  {tag}: {ok}/{len(rows)} avoided the mate")

    with open(OUT, "w") as f:
        json.dump({"fixtures": {"mate_in_one": mate1, "opponent_threat": threat},
                   "results": result}, f, indent=2)
    print(f"wrote {OUT}")


def judge_mate1(fx, rec, board):
    """PASS if the engine played a mating move, or reported mate 0/1."""
    if rec.bestmove is None or rec.bestmove == "0000":
        return "FAIL", f"bestmove {rec.bestmove}"
    if rec.bestmove in fx["mates"]:
        return "PASS", "played a mating move"
    # playing a non-mating move is a miss regardless of the score
    return "MISS", f"played {rec.bestmove}, mates were {fx['mates']}"


def judge_threat(fx, rec, board):
    """PASS if the engine played a move that denies the opponent's mate in 1."""
    if rec.bestmove is None or rec.bestmove == "0000":
        return "FAIL", f"bestmove {rec.bestmove}"
    if rec.bestmove in fx["avoid"]:
        return "PASS", "avoided the mate"
    if rec.bestmove in fx["lose"]:
        return "ERROR", f"played {rec.bestmove} into the mate"
    return "ILLEGAL", f"played {rec.bestmove} which is not a legal move"


if __name__ == "__main__":
    main()
