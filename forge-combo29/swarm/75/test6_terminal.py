"""Test 6: terminal scores.

Three distinct terminal conditions must be distinguishable, because collapsing
any two of them is a real defect class (the 5.30.0 release notes record exactly
that bug: a restricted root falsely printing `score mate 0`).

  checkmate      side to move is in check with no legal move -> a mate score
  stalemate      no legal move, NOT in check                 -> 0
  no-legal-move  same as stalemate here, asserted separately because the brief
                 asks for it explicitly and because the engine once conflated
                 them with a "restricted root" state

A mate score must be typed `mate`, not folded into centipawns: `mate 0` and
`cp 0` are completely different claims and must never be conflated.

Also covers the eval command's `incheck` flag, which is the second proof that
the engine holds the position the fixture intended.
"""

from __future__ import annotations

import json
import sys

import chess

from harness import Forge, parse_fen

# Fool's mate: White is checkmated, White to move.
CHECKMATE_WHITE = parse_fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
# The mirror: Black is checkmated, Black to move.
CHECKMATE_BLACK = parse_fen("rnbqkbnr/ppppp2p/5p2/6pQ/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 3")
# Classic stalemate: Black to move, not in check, no legal move.
STALEMATE = parse_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
# A second stalemate in the corner, to be sure it is not one lucky board.
STALEMATE_2 = parse_fen("k7/8/1Q6/8/8/8/8/6K1 b - - 0 1")
# A live position with many legal moves, as the control that the "no legal
# move" detection is not simply always-on.
LIVE = parse_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


def describe(res: dict) -> str:
    return f"{res['score']['type']} {res['score']['value']}"


def main() -> int:
    rows: list[dict] = []
    errors: list[dict] = []

    with Forge() as f:
        cases = [
            ("checkmated White to move", CHECKMATE_WHITE, "checkmate", "white_mated"),
            ("checkmated Black to move", CHECKMATE_BLACK, "checkmate", "black_mated"),
            ("stalemate Black to move", STALEMATE, "stalemate", "draw"),
            ("stalemate corner Black", STALEMATE_2, "stalemate", "draw"),
            ("live position", LIVE, "live", None),
        ]
        for name, board, kind, _ in cases:
            assert board.is_valid(), f"invalid fixture {name}: {board.fen()}"
            ev = f.evaluate(board)
            res = f.search(board, depth=6)

            # Ground truth from python-chess, computed independently.
            py_checkmate = board.is_checkmate()
            py_stalemate = board.is_stalemate()
            py_legal = board.legal_moves.count()

            # The engine's own terminal claim: no bestmove at all.
            no_bestmove = res["bestmove"] in (None, "0000", "(none)")

            row = {
                "case": name, "fen": board.fen(), "kind": kind,
                "python_checkmate": py_checkmate, "python_stalemate": py_stalemate,
                "python_legal_moves": py_legal,
                "eval_incheck": ev["incheck"], "eval_total": ev["total"],
                "eval_hce": ev["hce"], "eval_nnue": ev["nnue"],
                "search_score": res["score"], "engine_no_bestmove": no_bestmove,
                "bestmove": res["bestmove"],
            }
            rows.append(row)

            print(f"  {name:28s} {describe(res):18s} "
                  f"eval={ev['total']:6d} incheck={ev['incheck']} "
                  f"bestmove={res['bestmove']} legal={py_legal}")

            # --- assertions ------------------------------------------------
            if kind == "checkmate":
                # A checkmate must be a mate score, never 0 and never a
                # centipawn number.
                if res["score"]["type"] != "mate":
                    errors.append({**row, "why": "checkmate not reported as a mate score"})
                elif not no_bestmove:
                    errors.append({**row, "why": "checkmate still returned a bestmove"})
                if not ev["incheck"]:
                    errors.append({**row, "why": "mated side not flagged in check"})
            elif kind == "stalemate":
                if res["score"]["type"] != "cp" or res["score"]["value"] != 0:
                    errors.append({**row, "why": f"stalemate scored {describe(res)}, expected cp 0"})
                if ev["incheck"]:
                    errors.append({**row, "why": "stalemated side wrongly flagged in check"})
                if py_checkmate:
                    errors.append({**row, "why": "fixture is actually checkmate, not stalemate"})
            elif kind == "live":
                if no_bestmove:
                    errors.append({**row, "why": "live position returned no bestmove"})
                if res["score"]["type"] == "mate":
                    errors.append({**row, "why": "live position reported as mate"})
                if py_legal == 0:
                    errors.append({**row, "why": "control fixture has no legal moves"})

        # The distinguishing test the brief asks for: checkmate and stalemate
        # are BOTH "no legal move", and the engine must not confuse them.
        mate_row = next(r for r in rows if r["kind"] == "checkmate")
        stale_row = next(r for r in rows if r["kind"] == "stalemate")
        distinct = (mate_row["search_score"]["type"] != stale_row["search_score"]["type"]
                    or mate_row["search_score"]["value"] != stale_row["search_score"]["value"])
        print()
        print(f"checkmate vs stalemate distinguishable: {distinct}")
        if not distinct:
            errors.append({"why": "checkmate and stalemate scored identically",
                           "checkmate": mate_row["search_score"],
                           "stalemate": stale_row["search_score"]})

    with open("out_terminal.json", "w") as fh:
        json.dump({"cases": rows, "errors": errors}, fh, indent=2)

    print(f"cases={len(rows)} errors={len(errors)}")
    for err in errors:
        print(f"  ERROR {err.get('case', '?')}: {err['why']}")
        print(f"        fen {err.get('fen', '?')}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
