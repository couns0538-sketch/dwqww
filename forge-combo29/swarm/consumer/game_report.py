"""Summarise a games file: results, protocol failures, bail structure.

Separates three things a reader will otherwise merge:
  * games that ended because CHESS ended them (mate, stalemate, insufficient material...)
  * games that ended because the PROTOCOL ended them (a bail the client refused, a hang,
    a null token on a live board)
  * games that never finished inside the ply cap

Usage: python3 game_report.py evidence/games-100-strict.json [more.json ...]
"""
from __future__ import annotations

from evio import load_json

import json
import sys

PROTOCOL_WHY = {"bail", "hang", "null-token-on-live-board", "illegal", "unparsed",
                "client could not push the verified move"}


def report(path: str) -> dict:
    data = load_json(path)
    s = data["summary"]
    games = data["games"]

    chess_end = []
    proto_end = []
    unfinished = []
    for g in games:
        if g["protocol_failure"] in PROTOCOL_WHY or (g["protocol_failure"] and g["result"] == "protocol-failure"):
            proto_end.append(g)
        elif g["unfinished"]:
            unfinished.append(g)
        else:
            chess_end.append(g)

    bail_games = [g for g in games if g["category_counts"].get("BAIL")]
    total_bails = sum(g["category_counts"].get("BAIL", 0) for g in games)
    book_plies = sum(g["category_counts"].get("BOOK", 0) for g in games)
    unsearched = sum(g["category_counts"].get("UNSEARCHED", 0) for g in games)

    print(f"=== {path}")
    print(f"  games            : {s['games']}")
    print(f"  movetime         : {s['movetime_ms']} ms/move, allow_bail_play={s['allow_bail_play']}")
    print(f"  total plies      : {s['total_plies']}")
    print(f"  wall             : {s['wall_seconds']} s")
    print(f"  ended by chess   : {len(chess_end)}  {s['results']}")
    print(f"  ended by protocol: {len(proto_end)}  "
          f"{ {w: sum(1 for g in proto_end if g['protocol_failure'] == w) for w in PROTOCOL_WHY if any(g['protocol_failure'] == w for g in proto_end)} }")
    print(f"  unfinished       : {len(unfinished)} (ply cap {200})")
    print(f"  category totals  : {s['categories']}")
    print(f"  games w/ a BAIL  : {len(bail_games)}   BAIL plies: {total_bails}")
    print(f"  BOOK plies       : {book_plies}   UNSEARCHED plies: {unsearched}")

    # per-game bail multiplicity: a bail can repeat inside one game
    if bail_games:
        multi = {g["seed"]: g["category_counts"]["BAIL"] for g in bail_games
                 if g["category_counts"]["BAIL"] > 1}
        if multi:
            print(f"  games with >1 bail: {multi}")

    # every protocol failure, with its position
    for g in proto_end:
        fp = g.get("failure_ply") or {}
        print(f"    seed {g['seed']:5d} why={g['protocol_failure']:24s} ply={fp.get('n')} "
              f"move={fp.get('bestmove')} depth={fp.get('depth')} nodes={fp.get('nodes')} "
              f"pv_len={fp.get('pv_len')}")
    return {"path": path, "summary": s, "chess_end": len(chess_end),
            "proto_end": len(proto_end), "unfinished": len(unfinished),
            "bail_games": len(bail_games), "bail_plies": total_bails}


def main() -> int:
    for p in sys.argv[1:]:
        report(p)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
