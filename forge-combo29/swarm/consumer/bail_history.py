"""Audit the drawn-root BAILs WITH the move history that produced them.

`bail_audit.py` re-sent each BAIL position as a FEN, which per trap 2d *destroys the
repetition history*: a FEN cannot carry it.  That is precisely the defect that decides
whether a BAIL is correct, so a FEN replay can neither confirm nor refute a
repetition-triggered bail.

This script rebuilds the exact pre-move position from the recorded game and asks
python-chess, on the full history, whether the root really was a draw claim.  Then it
re-asks the engine on the same history via `position startpos moves ...`, the only form
that can carry a repetition, so the comparison is against the state the engine saw.

The failing ply's own move was never played (the client refused to play it), so the
history stops one ply short of the recorded list.

Usage: python3 bail_history.py ENGINE evidence/games.json
"""
from __future__ import annotations

from evio import load_json

import json
import sys

import chess

from engine import Engine, EngineDied, EngineTimeout


def played_moves(game: dict) -> list[str]:
    """Moves the client actually pushed, i.e. every ply before the failing one."""
    out = list(game["opening"])
    plies = game["plies"]
    if game.get("protocol_failure") and plies:
        plies = plies[:-1]  # the last recorded ply is the refused one
    for ply in plies:
        bm = ply.get("bestmove")
        if bm and bm != "0000":
            out.append(bm)
    return out


def position_line(moves: list[str]) -> str:
    return "position startpos moves " + " ".join(moves) if moves else "position startpos"


def ask(path: str, pos_line: str, go: str, deadline: float = 40.0) -> dict:
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
        eng.send(pos_line)
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
        nodes, pv, score = None, "", None
        if last:
            p = last.split()
            if "nodes" in p:
                nodes = int(p[p.index("nodes") + 1])
            if "pv" in p:
                pv = " ".join(p[p.index("pv") + 1:])
            if "score" in p:
                i = p.index("score")
                score = (p[i + 1], int(p[i + 2]))
        return {
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "nodes": nodes,
            "pv": pv,
            "score": score,
            "n_info": len(infos),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path, games_file = sys.argv[1], sys.argv[2]
    data = load_json(games_file)

    cases = [g for g in data["games"] if g.get("protocol_failure") == "bail"]
    print(f"{len(cases)} BAIL games; auditing with full move history\n")
    rows = []
    for g in cases:
        moves = played_moves(g)
        b = chess.Board()
        for mv in moves:
            b.push_uci(mv)
        status = {
            "halfmove_clock": b.halfmove_clock,
            "insufficient_material": b.is_insufficient_material(),
            "fifty_moves_claimable": b.is_fifty_moves(),
            "repetition_2fold": b.is_repetition(2),
            "repetition_3fold": b.is_repetition(3),
            "stalemate": b.is_stalemate(),
            "checkmate": b.is_checkmate(),
            "legal_moves": len(list(b.legal_moves)),
            "fen_matches_record": b.fen() == g["failure_fen"],
        }
        pos = position_line(moves)
        rep = ask(path, pos, "go movetime 100")
        rep_d = ask(path, pos, "go depth 12")
        print(f"seed {g['seed']}  ply {g['plies'][-1]['n']}  {b.fen()}")
        print(f"   history status: {status}")
        print(f"   movetime 100 on true history -> {rep['bestmove']} nodes={rep['nodes']} "
              f"score={rep['score']} pv={rep['pv'][:30]!r}")
        print(f"   depth 12     on true history -> {rep_d['bestmove']} nodes={rep_d['nodes']} "
              f"score={rep_d['score']} pv={rep_d['pv'][:30]!r}")
        print()
        rows.append({"seed": g["seed"], "ply": g["plies"][-1]["n"], "fen": b.fen(),
                     "status": status, "movetime": rep, "depth12": rep_d,
                     "n_moves": len(moves)})

    with open("evidence/bail-history.json", "w") as f:
        json.dump(rows, f, indent=1)
    print("wrote evidence/bail-history.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
