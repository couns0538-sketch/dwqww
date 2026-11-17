"""Q1b: does any game leave the book into a LOST-ON-THE-SPOT position?

"Lost on the spot" is given a definition here rather than left as a word, because
the phrase could otherwise be tuned to the answer:

  * the position just after book exit is searched at depth 18 with `OwnBook`
    off, and the score is read FROM THE SIDE TO MOVE;
  * the game is counted as leaving into a lost position if that score is worse
    than -200 cp (two pawns) OR is a mate score against the side to move.

Two pawns is a deliberately generous threshold: the question is whether the book
dumps a game into a position that is already decided, not whether the exit score
is perfectly equal. The worst observed exit is reported either way, so a reader can
disagree with the threshold and still read the number.

The move right after book exit is also recorded, to show it came from a real
search (a book move there would mean the book had not actually ended).
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import chess

from forge_uci import Engine

LOST_CP = -200


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args()

    games = json.load(open(args.games))
    # one record per distinct book line: the exit position depends only on the line
    lines: dict[str, dict] = {}
    for g in games:
        n = g["book_plies"]
        if n == 0:
            continue
        key = " ".join(g["moves"][:n])
        lines.setdefault(key, {"moves": g["moves"][:n], "games": 0,
                               "next_flags": set()})
        lines[key]["games"] += 1
        if len(g["moves"]) > n:
            # was the move right after the book a book move? (it must not be)
            lines[key]["next_flags"].add(g["book_flags"][n])

    print(f"{len(lines)} distinct book lines across {len(games)} games")

    eng = Engine(args.engine)
    rows = []
    started = time.monotonic()
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "false")
        for key, info in lines.items():
            board = chess.Board()
            for mv in info["moves"]:
                board.push_uci(mv)
            eng.position_checked(f"fen {board.fen()}")
            reply = eng.go(f"depth {args.depth}", args.timeout)
            score = reply.last_score_cp()
            rows.append({
                "line": key,
                "games_reaching_it": info["games"],
                "exit_fen": board.fen(),
                "side_to_move": "white" if board.turn else "black",
                "exit_score_cp_for_mover": score,
                "engine_choice_after_exit": reply.bestmove(),
                "next_move_was_book": sorted(info["next_flags"]),
                "lost_on_the_spot": (score is not None and
                                     (score <= LOST_CP or abs(score) >= 90_000)),
            })
            print(f"  {info['games']:4d} games  {key.split()[0]:6s} score {score}")
    finally:
        eng.quit()

    scored = [r for r in rows if r["exit_score_cp_for_mover"] is not None]
    lost = [r for r in scored if r["lost_on_the_spot"]]
    worst = min(scored, key=lambda r: r["exit_score_cp_for_mover"]) if scored else None
    any_book_after = any(1 in r["next_move_was_book"] for r in rows)

    report = {
        "engine": args.engine,
        "depth": args.depth,
        "threshold_cp": LOST_CP,
        "definition": "lost on the spot = exit score <= -200 cp for the side to "
                      "move, or a mate score against it, at depth 18 with OwnBook off",
        "distinct_book_lines": len(rows),
        "lines_scored": len(scored),
        "lines_leaving_into_a_lost_position": len(lost),
        "lost_detail": lost,
        "worst_exit": worst,
        "exit_scores_cp": sorted(r["exit_score_cp_for_mover"] for r in scored),
        "any_game_had_a_book_move_after_exit": any_book_after,
        "elapsed_s": round(time.monotonic() - started, 1),
    }
    report["verdict"] = (
        f"NO game leaves the book into a lost position: 0 of {len(scored)} distinct "
        f"book lines exit at or below {LOST_CP} cp. The worst exit is "
        f"{worst['exit_score_cp_for_mover']} cp for the side to move."
        if not lost and not any_book_after else
        f"{len(lost)} line(s) leave into a lost position"
        + ("; and a game had a book move AFTER its exit, which contradicts the "
           "exit definition" if any_book_after else "")
    )
    json.dump(report, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "lost_detail"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
