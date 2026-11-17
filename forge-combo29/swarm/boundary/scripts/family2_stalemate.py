"""Family 2: one ply from stalemate.

The brief's question is a SCORE question, so the score is what is judged.

  A. LOSING SIDE whose only legal moves all lead to stalemate (`next_stale`):
     the true value is 0.00 and the engine should say so. This is the
     "prefer stalemate when losing" half.

  B. WINNING SIDE that has both a mating move and a stalemating move
     (`stale_available`): the true value is a MATE and the engine must not
     answer 0.00, and must not play the stalemating move.

  C. LOSING SIDE that can choose between stalemate and a loss-with-material
     (`stale_optional`): score should be 0.00 when the stalemate is taken.
"""
import json
import sys
import chess

from forge_drv import Forge, RefusedFen
import stalemate as S
import construct as C

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family2_stalemate.json"

GO = "go depth 10"


def gen_stale_available(count=50):
    """Winning side: a mating move AND a stalemating move both exist."""
    return C.enum_stalemate_available(limit=count)


def gen_next_stale(count=50):
    """Every legal move stalemates: true value 0.00."""
    return S.enum_every_move_stalemates(limit=count)


def gen_stale_optional(count=50):
    """Losing side: one move stalemates the opponent (draw), others lose slowly."""
    out = []
    seen = set()
    # mover has a lone king; opponent has a piece; mover can step to a square
    # where the opponent's every move stalemates it. Built by enumeration over
    # the final stalemate square.
    for ok in range(64):
        for opp_pt in (chess.QUEEN, chess.ROOK):
            for opp_sq in range(64):
                if opp_sq == ok:
                    continue
                for mk in range(64):
                    if mk == ok or chess.square_distance(mk, ok) <= 1:
                        continue
                    b = chess.Board(None)
                    b.set_piece_at(ok, chess.Piece(chess.KING, chess.BLACK))
                    b.set_piece_at(opp_sq, chess.Piece(opp_pt, chess.BLACK))
                    b.set_piece_at(mk, chess.Piece(chess.KING, chess.WHITE))
                    b.turn = chess.WHITE
                    b.castling_rights = 0
                    b.ep_square = None
                    b.halfmove_clock = 0
                    b.fullmove_number = 40
                    if not b.is_valid():
                        continue
                    if b.is_checkmate() or b.is_stalemate():
                        continue
                    stale_moves = []
                    for mv in b.legal_moves:
                        b.push(mv)
                        if b.is_stalemate():
                            stale_moves.append(mv.uci())
                        b.pop()
                    if not stale_moves:
                        continue
                    n_legal = b.legal_moves.count()
                    if len(stale_moves) == n_legal:
                        continue  # that is family A
                    fen = b.fen()
                    if fen in seen:
                        continue
                    seen.add(fen)
                    out.append({"fen": fen, "stale_moves": stale_moves,
                                "n_legal": n_legal})
                    if len(out) >= count:
                        return out
    return out


def main():
    fam_a = gen_next_stale(50)
    fam_b = gen_stale_available(50)
    fam_c = gen_stale_optional(50)
    print(f"constructed: next_stale={len(fam_a)} stale_available={len(fam_b)} "
          f"stale_optional={len(fam_c)}")

    out = {}
    with Forge(EXE) as eng:
        for name, fixtures, judge in (
            ("next_stale", fam_a, judge_next_stale),
            ("stale_available", fam_b, judge_available),
            ("stale_optional", fam_c, judge_optional),
        ):
            rows = []
            for i, fx in enumerate(fixtures):
                pc = chess.Board(fx["fen"])
                assert pc.is_valid(), fx["fen"]
                try:
                    rec = eng.search(fx["fen"], GO)
                except RefusedFen as e:
                    rows.append({"i": i, "fen": fx["fen"], "refused": True,
                                 "error": str(e)})
                    continue
                verdict, note = judge(fx, rec, pc)
                rows.append({"i": i, "fen": fx["fen"], "go": GO,
                             "bestmove": rec.bestmove, "score": rec.score(),
                             "nodes": rec.nodes(), "depth": rec.depth(),
                             "pv": rec.pv(), "info_strings": rec.info_strings(),
                             "n_infos": len(rec.infos),
                             "verdict": verdict, "note": note, **{
                                 k: v for k, v in fx.items() if k != "fen"}})
            out[name] = rows
            import collections
            c = collections.Counter(r.get("verdict") for r in rows)
            print(f"  {name}: {dict(c)}  (denominator {len(rows)})")

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}")


def judge_next_stale(fx, rec, board):
    """True value is 0.00: every move draws by stalemate."""
    sc = rec.score()
    if sc is None:
        return "NO_SCORE", "no score on the wire"
    if sc == ("cp", 0):
        return "PASS", "score 0.00, correct"
    if sc[0] == "mate" and sc[1] == 0:
        return "PASS", "mate 0 (terminal path), equivalent"
    return "WRONG_SCORE", f"score {sc}, position is a dead stalemate draw"


def judge_available(fx, rec, board):
    """A win exists: score must be a positive mate and the move must mate."""
    sc = rec.score()
    if sc is None:
        return "NO_SCORE", "no score"
    if rec.bestmove in fx["mates"]:
        if sc[0] == "mate" and sc[1] > 0:
            return "PASS", "played the mate and scored it"
        return "SCORE_WRONG", f"played the mate but scored {sc}"
    if rec.bestmove in [m for m in fx["stale"]]:
        return "TOOK_STALEMATE", f"played the stalemating move {rec.bestmove}"
    return "MISSED_MATE", f"played {rec.bestmove}, mate was {fx['mates']}, score {sc}"


def judge_optional(fx, rec, board):
    """Losing side can stalemate. 0.00 is the best available score."""
    sc = rec.score()
    if sc is None:
        return "NO_SCORE", "no score"
    took = rec.bestmove in fx["stale_moves"]
    if took and sc == ("cp", 0):
        return "PASS", "took the stalemate and scored 0.00"
    if took and sc != ("cp", 0):
        return "SCORE_WRONG", f"took the stalemate but scored {sc}"
    if not took and sc == ("cp", 0):
        return "SCORE_ONLY", "score 0.00 without taking the stalemate"
    return "DECLINED", f"played {rec.bestmove}, score {sc}"


if __name__ == "__main__":
    main()
