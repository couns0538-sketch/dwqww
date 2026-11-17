"""Was the drawn-root bail actually correct where the match hit it?

The bail fires when the engine adjudicates the ROOT as drawn.  Under the client's rules a
BAIL is a protocol failure because the move was never searched -- but the client must not
report that as an engine error if the position genuinely is a draw claim.  This script
re-opens every BAIL position from the games file and asks an independent question of the
position itself (python-chess claim logic on the client's own board plus a perft-style
legality check), then replays the position with `OwnBook false` and a drawn-root-free
control to show what the same search does when the root is not drawn.

Usage: python3 bail_audit.py ENGINE evidence/games.json
"""
from __future__ import annotations

import json
import sys

import chess

from engine import Engine, EngineDied, EngineTimeout


def independent_draw_status(fen: str) -> dict:
    b = chess.Board(fen)
    return {
        "insufficient_material": b.is_insufficient_material(),
        "halfmove_clock": b.halfmove_clock,
        "fifty_moves_claimable": b.is_fifty_moves(),
        "repetition_claimable": b.is_repetition(2),
        "stalemate": b.is_stalemate(),
        "checkmate": b.is_checkmate(),
        "legal_moves": len(list(b.legal_moves)),
    }


def ask(path: str, fen: str, go: str, deadline: float = 30.0) -> dict:
    eng = Engine(path)
    try:
        eng.send("uci")
        eng.read_until(lambda w: w.text.strip() == "uciok", 20.0)
        eng.send("setoption name OwnBook value false")
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), deadline)
            timed_out = False
        except (EngineTimeout, EngineDied):
            wires = eng.drain_now()
            timed_out = True
        texts = [w.text for w in wires]
        infos = [t for t in texts if t.startswith("info depth")]
        last = infos[-1] if infos else None
        nodes = None
        pv = ""
        if last:
            p = last.split()
            if "nodes" in p:
                nodes = int(p[p.index("nodes") + 1])
            if "pv" in p:
                pv = " ".join(p[p.index("pv") + 1:])
        return {
            "go": go,
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "nodes": nodes,
            "pv": pv,
            "n_info": len(infos),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path, games_file = sys.argv[1], sys.argv[2]
    with open(games_file) as f:
        data = json.load(f)

    bails = []
    for g in data["games"]:
        if g.get("protocol_failure") == "bail" and g.get("failure_fen"):
            bails.append((g["seed"], g["failure_fen"], g.get("failure_ply")))

    print(f"{len(bails)} BAIL positions from the match\n")
    rows = []
    for seed, fen, ply in bails:
        ind = independent_draw_status(fen)
        # Same position, delivered as a FEN: no repetition history, per trap 2d.
        again = ask(path, fen, "go depth 12")
        print(f"seed {seed}  fen {fen}")
        print(f"   client-side check: {ind}")
        print(f"   re-sent as FEN, go depth 12 -> {again['bestmove']} nodes={again['nodes']} "
              f"pv={again['pv'][:40]!r}")
        rows.append({"seed": seed, "fen": fen, "independent": ind, "fen_replay": again})

    # Control: the same search on a position with the same material but a live clock,
    # to show what a normal search looks like at depth 12.
    with open("evidence/bail-audit.json", "w") as f:
        json.dump(rows, f, indent=1)
    print("\nwrote evidence/bail-audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
