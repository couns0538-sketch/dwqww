"""Verify ALL protocol-failure positions from a match against an independent referee.

`bail_history.py` did this for 6 positions by hand.  This does it for every failure in a
100-game file.  For each failing position it rebuilds the exact pre-move board from the
recorded moves and asks python-chess three questions, none of which involve the engine:

  1. Is the position a threefold repetition claim on the full history?
  2. Is it a fifty-move claim, insufficient material, stalemate or checkmate?
  3. How many legal moves does it have?

and it reports the engine's reported depth/nodes/pv beside it.  A bail on a position that
is NOT a claim is a different (and worse) finding from a bail on one that is, so the two
must not be merged.

Usage: python3 verify_failures.py evidence/games-100-strict.json
"""
from __future__ import annotations

from evio import load_json

import json
import sys

import chess

CLAIM_KEYS = ("repetition_3fold", "fifty_moves_claimable", "insufficient_material",
              "stalemate", "checkmate")


def played_moves(game: dict) -> list[str]:
    out = list(game["opening"])
    plies = game["plies"]
    if game.get("protocol_failure") and plies:
        plies = plies[:-1]
    for ply in plies:
        bm = ply.get("bestmove")
        if bm and bm != "0000":
            out.append(bm)
    return out


def legal(moves: list[str]) -> chess.Board:
    b = chess.Board()
    for mv in moves:
        b.push_uci(mv)
    return b


def main() -> int:
    path = sys.argv[1]
    data = load_json(path)

    fails = [g for g in data["games"] if g.get("protocol_failure")]
    rows = []
    tally: dict[str, int] = {}
    unexplained = []
    fen_mismatch = []

    for g in fails:
        moves = played_moves(g)
        b = legal(moves)
        status = {
            "repetition_2fold": b.is_repetition(2),
            "repetition_3fold": b.is_repetition(3),
            "fifty_moves_claimable": b.is_fifty_moves(),
            "halfmove_clock": b.halfmove_clock,
            "insufficient_material": b.is_insufficient_material(),
            "stalemate": b.is_stalemate(),
            "checkmate": b.is_checkmate(),
            "legal_moves": len(list(b.legal_moves)),
            "fen_matches_record": b.fen() == g.get("failure_fen"),
        }
        why = g["protocol_failure"]
        causes = [k for k in CLAIM_KEYS if status.get(k)]
        cause = "+".join(causes) if causes else "NONE"
        key = f"{why}:{cause}"
        tally[key] = tally.get(key, 0) + 1
        if not causes:
            unexplained.append(g["seed"])
        if not status["fen_matches_record"]:
            fen_mismatch.append(g["seed"])
        fp = g.get("failure_ply") or {}
        rows.append({"seed": g["seed"], "why": why, "cause": cause, "status": status,
                     "ply": fp.get("n"), "move": fp.get("bestmove"),
                     "depth": fp.get("depth"), "nodes": fp.get("nodes"),
                     "pv_len": fp.get("pv_len")})

    print(f"{len(fails)} protocol failures in {path}")
    print("\nby cause (independent referee, engine not consulted):")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nindependently justified : {len(fails) - len(unexplained)}/{len(fails)}")
    print(f"NOT justified           : {len(unexplained)}"
          + (f"  seeds {unexplained}" if unexplained else ""))
    print(f"FEN mismatch (my rebuild vs the client's record): {len(fen_mismatch)}"
          + (f"  seeds {fen_mismatch}" if fen_mismatch else ""))

    # the engine's own reporting on those same positions
    depths = {r["depth"] for r in rows}
    nodes = {r["nodes"] for r in rows}
    pvs = {r["pv_len"] for r in rows}
    print(f"\nengine reporting on those {len(rows)} positions:")
    print(f"  reported depth values : {sorted(d for d in depths if d is not None)}")
    print(f"  reported node counts  : {sorted(n for n in nodes if n is not None)}")
    print(f"  pv lengths            : {sorted(p for p in pvs if p is not None)}")

    with open("evidence/verify-failures.json", "w") as f:
        json.dump({"tally": tally, "unexplained": unexplained, "rows": rows}, f, indent=1)
    print("\nwrote evidence/verify-failures.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
