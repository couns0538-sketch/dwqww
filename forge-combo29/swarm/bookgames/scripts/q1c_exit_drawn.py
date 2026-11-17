"""Does a book exit ever leave the engine in a DRAWN-ROOT state on the next move?

This is the game-level form of trap 19a. The trap is that the book decision runs
BEFORE the drawn-root bail, so a drawn root that the book covers ships a book move
with none of the warnings a caller uses to detect a drawn root. The question here
is narrower and is the one a game can answer:

  at the position the engine is handed immediately after the book stops playing,
  is that position already a drawn root by the engine's own three tests --
  repetition, halfmove >= 100, insufficient material?

Each test is checked separately and reported separately, because they fail for
different reasons and a combined "not drawn" would hide which one was close:

  * REPETITION needs move history. Measured with `position startpos moves ...` so
    the engine has a key history to count, NOT from a FEN -- a FEN carries no
    history and would make this test unable to fire at all. This is the mistake
    that made an earlier version of this audit's repetition checks vacuous.
  * HALFMOVE is read from the actual position at exit.
  * INSUFFICIENT MATERIAL is read from the actual position at exit.

A control is included: a hand-built 50-move root and a hand-built threefold are
run through the same detector, so a run of zeros below cannot be the detector
silently failing to fire.
"""

from __future__ import annotations

import argparse
import json
import sys

import chess

from forge_uci import Engine

BLOCK = 60


def drawn_state(board: chess.Board) -> dict:
    """The engine's own three drawn-root tests, evaluated on this board."""
    return {
        "repetition": board.is_repetition(2),        # needs history on the board
        "fifty_move": board.halfmove_clock >= 100,
        "insufficient": board.is_insufficient_material(),
        "halfmove_clock": board.halfmove_clock,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    games = json.load(open(args.games))
    exits: dict[str, dict] = {}
    for g in games:
        n = g["book_plies"]
        if n == 0:
            continue
        key = " ".join(g["moves"][:n])
        exits.setdefault(key, {"moves": g["moves"][:n], "games": 0})
        exits[key]["games"] += 1

    print(f"{len(exits)} distinct book-exit positions from {len(games)} games")

    # --- control: the detector must fire on a 50-move root and on a threefold
    control = {}

    b50 = chess.Board("8/8/4k3/8/8/4K3/8/8 w - - 100 80")
    control["fifty_move_root"] = drawn_state(b50)

    b_rep = chess.Board()
    for m in ("g1f3", "g8f6", "f3g1", "f6g8") * 2:
        b_rep.push_uci(m)
    control["threefold_root"] = drawn_state(b_rep)

    b_ins = chess.Board("8/8/4k3/8/8/4K3/8/5B2 w - - 0 80")
    control["insufficient_root"] = drawn_state(b_ins)

    control_ok = (control["fifty_move_root"]["fifty_move"]
                  and control["threefold_root"]["repetition"]
                  and control["insufficient_root"]["insufficient"])
    if not control_ok:
        out = {"control": control, "control_passed": False,
               "verdict": "VOID: the drawn-root detector cannot fire, so a zero "
                          "below would mean nothing"}
        json.dump(out, open(args.out, "w"), indent=1)
        print("VOID: control failed")
        print(json.dumps(control, indent=1))
        return 1

    eng = Engine(args.engine)
    rows = []
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        for key, info in exits.items():
            board = chess.Board()
            for mv in info["moves"]:
                board.push_uci(mv)
            local = drawn_state(board)
            # the engine's view at the same position, WITH history attached
            eng.position_checked("startpos moves " + " ".join(info["moves"]))
            reply = eng.go("wtime 60000 btime 60000", 20.0)
            rows.append({
                "line_prefix": key.split()[0],
                "moves": " ".join(info["moves"]),
                "games_reaching_it": info["games"],
                "exit_fen": board.fen(),
                **local,
                "engine_booked_at_exit": reply.book_move() is not None,
                "engine_depth_lines": len(reply.depth_lines()),
            })
    finally:
        eng.quit()

    any_drawn = [r for r in rows if r["repetition"] or r["fifty_move"] or r["insufficient"]]
    worst_halfmove = max((r["halfmove_clock"] for r in rows), default=None)
    booked_at_exit = [r for r in rows if r["engine_booked_at_exit"]]

    report = {
        "engine": args.engine,
        "distinct_exit_positions": len(rows),
        "control": control,
        "control_passed": control_ok,
        "exit_positions_that_are_drawn_roots": len(any_drawn),
        "drawn_detail": any_drawn,
        "worst_halfmove_clock_at_exit": worst_halfmove,
        "exit_positions_where_the_book_still_fired": len(booked_at_exit),
        "rows": rows,
    }
    report["verdict"] = (
        f"NO book exit leaves a drawn root: 0 of {len(rows)} distinct exit positions "
        f"is a repetition, a 50-move root or insufficient material, and the worst "
        f"halfmove clock at exit is {worst_halfmove}. The detector is shown to fire "
        "on all three kinds of drawn root by the controls."
        if not any_drawn else
        f"{len(any_drawn)} exit position(s) ARE drawn roots -- trap 19a is reachable"
    )
    json.dump(report, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
