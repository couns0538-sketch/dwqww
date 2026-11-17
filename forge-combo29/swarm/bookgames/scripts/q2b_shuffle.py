"""Can the book fire on an actual DRAWN root in a real game?

THE HARNESS TRAP THIS SCRIPT EXISTS TO AVOID: a `position fen ...` command carries
NO move history. The engine's repetition test walks a key history, so a position
fed as a FEN reports "not a repetition" no matter how many times it occurred in
the game it came from. Every repetition question below is asked with
`position startpos moves ...`. An earlier version fed FENs, so its threefold
control could never have fired and every "not drawn" answer it gave was vacuous.

THE STRUCTURE BEING TESTED (found by reentry_drawn.py, then confirmed by hand):

  ply 15  Black to move, bishop on f8. IN THE BOOK.
  ply 16  the book plays ...f8e7. White to move, bishop on e7. A book LEAF -- the
          book has no entry for any continuation, so play leaves the book here.

  The two positions differ only in where that bishop stands, and White's pieces
  are identical in both. So from the leaf:

      White plays a (any reversible move),
      Black plays ...e7f8 (restoring the bishop),
      White plays a-inverse (restoring White),

  lands exactly on the ply-15 position again -- the same placement, the same side
  to move, the same castling rights. That position IS in the book, so the book
  fires there again, plays ...f8e7, and the cycle can run a third time. The third
  occurrence is a threefold root that the book covers: trap 19a reached in play.

CONTROLS, in order of execution, and the run is VOID if either fails:

  CONTROL 1  an ordinary book position must still book.
  CONTROL 2  a hand-built threefold on startpos (a 4-ply knight shuffle twice)
             must show trap 19a's signature with the book on (a book move and no
             `info depth`) and the drawn-root bail with it off (cp 0, empty pv).
             Without this the harness cannot be shown to detect the defect, so a
             clean result below would mean nothing.
"""

from __future__ import annotations

import json
import sys

import chess
import chess.polyglot

import book_graph as bg
from forge_uci import Engine

LINE16 = ("e2e4 c7c5 c2c3 e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1d3 c5c4 "
          "d3c2 b8c6 e1g1 f8e7").split()

# The book move that takes ply 15 to ply 16, and its inverse.
BOOK_MOVE = "f8e7"
BOOK_UNDO = "e7f8"


def ask(engine: Engine, moves: list[str], timeout: float = 20.0) -> dict:
    body = "startpos moves " + " ".join(moves) if moves else "startpos"
    engine.position_checked(body)
    reply = engine.go("wtime 60000 btime 60000", timeout)
    return {"book": reply.book_move(), "best": reply.bestmove(),
            "depth_lines": len(reply.depth_lines()), "timed_out": reply.timed_out}


def board_after(moves: list[str]) -> chess.Board:
    b = chess.Board()
    for m in moves:
        b.push_uci(m)
    return b


def find_cycle(leaf: chess.Board, target: chess.Board) -> list[str] | None:
    """Three plies from `leaf` that land on `target`: White a, Black undo, White a-inverse."""
    rights = leaf.clean_castling_rights()
    for mv in leaf.legal_moves:
        if leaf.is_capture(mv) or leaf.piece_type_at(mv.from_square) == chess.PAWN:
            continue
        mid = leaf.copy()
        mid.push(mv)
        if mid.clean_castling_rights() != rights or mid.turn != chess.BLACK:
            continue
        if not any(m.uci() == BOOK_UNDO for m in mid.legal_moves):
            continue
        after = mid.copy()
        after.push_uci(BOOK_UNDO)
        for back in after.legal_moves:
            if back.from_square != mv.to_square or back.to_square != mv.from_square:
                continue
            if after.is_capture(back):
                continue
            if after.piece_type_at(back.from_square) != leaf.piece_type_at(mv.from_square):
                continue
            end = after.copy()
            end.push(back)
            if end.clean_castling_rights() != rights:
                continue
            if end._transposition_key() == target._transposition_key():
                return [mv.uci(), BOOK_UNDO, back.uci()]
    return None


def main() -> int:
    engine_path, out_path, book_path = sys.argv[1], sys.argv[2], sys.argv[3]
    entries = bg.load_book(book_path)
    keys = {k for k, _m, _w in entries}

    eng = Engine(engine_path)
    report: dict = {"engine": engine_path,
                    "method": "every repetition question is asked with "
                              "`position startpos moves ...` so the engine has a "
                              "key history to count"}
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")

        # ---------------- CONTROL 1
        c1 = ask(eng, ["e2e4"])
        report["control1_ordinary_book"] = c1
        if c1["book"] is None:
            report["verdict"] = "VOID: control 1 did not book"
            json.dump(report, open(out_path, "w"), indent=1)
            print("VOID: control 1")
            return 1

        # ---------------- CONTROL 2
        rep = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2
        rep_board = board_after(rep)
        c2_on = ask(eng, rep)
        eng.setoption("OwnBook", "false")
        c2_off = ask(eng, rep)
        eng.setoption("OwnBook", "true")
        report["control2_threefold_root"] = {
            "moves": " ".join(rep),
            "python_chess_threefold": rep_board.is_repetition(3),
            "startpos_in_book": chess.polyglot.zobrist_hash(rep_board) in keys,
            "book_on": c2_on, "book_off": c2_off,
            "signature_present": c2_on["book"] is not None and c2_on["depth_lines"] == 0,
            "bail_present_with_book_off": c2_off["book"] is None,
        }
        c2_ok = (c2_on["book"] is not None and c2_on["depth_lines"] == 0
                 and c2_off["book"] is None)
        report["control2_passed"] = c2_ok
        if not c2_ok:
            report["verdict"] = ("VOID: control 2 could not show the trap-19a "
                                 "signature, so the harness cannot detect it")
            json.dump(report, open(out_path, "w"), indent=1)
            print("VOID: control 2")
            return 1

        # ---------------- the finding
        moves = list(LINE16)
        leaf = board_after(moves)
        prev = board_after(moves[:-1])
        report["positions"] = {
            "recurring": {"ply": prev.ply(), "fen": prev.fen(),
                          "in_book": chess.polyglot.zobrist_hash(prev) in keys},
            "leaf": {"ply": leaf.ply(), "fen": leaf.fen(),
                     "in_book": chess.polyglot.zobrist_hash(leaf) in keys},
            "book_move": BOOK_MOVE, "book_undo": BOOK_UNDO,
        }
        cycle = find_cycle(leaf, prev)
        report["cycle"] = cycle
        if cycle is None:
            report["verdict"] = "no 3-ply cycle from this leaf back to ply 15"
            json.dump(report, open(out_path, "w"), indent=1)
            print(report["verdict"])
            return 0

        # run it. Each round is: the 3-ply cycle (which lands on the ply-15
        # position, Black to move), then the BOOK move ...f8e7 back to the leaf.
        # The book move is part of the loop because the cycle returns to `prev`,
        # not to the leaf -- the first version of this driver forgot it and tried
        # to play White's move on Black's turn.
        steps = []
        cur = list(moves)
        for round_index in (1, 2, 3):
            for m in cycle:
                cur.append(m)
            b = board_after(cur)
            entry = {
                "round": round_index,
                "ply": b.ply(),
                "at_ply15_position": b._transposition_key() == prev._transposition_key(),
                "threefold": b.is_repetition(3),
                "in_book": chess.polyglot.zobrist_hash(b) in keys,
            }
            # what does the engine actually do here, with history attached?
            asked = ask(eng, cur)
            entry["engine_book"] = asked["book"]
            entry["engine_best"] = asked["best"]
            entry["engine_depth_lines"] = asked["depth_lines"]
            steps.append(entry)
            if asked["book"] is None:
                steps[-1]["note"] = "book did not fire at this occurrence"
                break
            cur.append(asked["book"])
        report["cycles"] = steps

        final = board_after(cur)
        at_final = ask(eng, cur)
        report["at_final"] = {
            "moves": " ".join(cur), "ply": final.ply(), "fen": final.fen(),
            "threefold": final.is_repetition(3),
            "in_book": chess.polyglot.zobrist_hash(final) in keys,
            "engine": at_final,
        }

        # The detection point is each CYCLE position (the recurring ply-15
        # position), NOT the final position: the last move of a round is the book
        # move back to the leaf, so `final` is the leaf and is not the threefold.
        # The first version tested only `final` and therefore reported
        # trap_19a_reached_in_play = false while `cycles` recorded the threefold
        # with a book move and zero depth lines one loop earlier.
        hit = next((c for c in steps
                    if c.get("threefold") and c.get("in_book")
                    and c.get("engine_book") is not None
                    and c.get("engine_depth_lines") == 0), None)
        report["trap_19a_reached_in_play"] = hit is not None
        report["trap_19a_point"] = hit
        report["trap_19a_note"] = (
            "The recurring position is reached for the THIRD time and the book "
            "plays it anyway, emitting `info string book move` with zero `info "
            "depth` lines -- the trap-19a signature. Reaching it required driving "
            "the shuffle: the opponent must cooperate, so this shows the state is "
            "REACHABLE in play, not that either engine walks into it unaided."
            if hit else
            "no cycle position was simultaneously a threefold and in the book"
        )

        # the same final position with the book OFF, to show the bail it should have had
        eng.setoption("OwnBook", "false")
        report["at_final_book_off"] = ask(eng, cur)
        eng.setoption("OwnBook", "true")

        # does the ENGINE play the cycle on its own, or only if forced?
        # ask at the leaf and at each point with the book on.
        auto = []
        sim = list(moves)
        for _ in range(6):
            r = ask(eng, sim)
            if r["best"] in (None, "0000"):
                break
            auto.append({"ply": board_after(sim).ply(), "book": r["book"], "best": r["best"]})
            sim.append(r["best"])
        report["engine_own_play_from_leaf"] = auto
    finally:
        eng.quit()

    json.dump(report, open(out_path, "w"), indent=1)
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
