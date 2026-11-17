"""What a client does WRONG if it plays the drawn-root bail move.

Trap 2d gives the instrument: a FEN cannot carry repetition history, so
`position fen <board>` on a threefold root does NOT bail, while
`position startpos moves ...` DOES.  The two forms therefore show, from the client's
side, what the same position is worth when the engine actually searches it, next to
what the bail hands back without searching.

For each bail position from a match this prints:
  * the bail's reply (move list form): move, nodes, score, pv
  * the same board searched as a FEN:  move, score, nodes, pv
  * whether the two moves agree

Agreement is the control: if both forms gave the same move, the bail move would be
harmless and this script would say so.

Usage: python3 bail_harm.py ENGINE evidence/games.json
"""
from __future__ import annotations

import json
import sys

import chess

from engine import Engine, EngineDied, EngineTimeout


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


def ask(path: str, pos_line: str, go: str, deadline: float = 60.0) -> dict:
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
        nodes, pv, score, depth = None, "", None, None
        if last:
            p = last.split()
            if "nodes" in p:
                nodes = int(p[p.index("nodes") + 1])
            if "depth" in p:
                depth = int(p[p.index("depth") + 1])
            if "pv" in p:
                pv = " ".join(p[p.index("pv") + 1:])
            if "score" in p:
                i = p.index("score")
                score = f"{p[i + 1]} {p[i + 2]}"
        return {
            "bestmove": (next((t for t in texts if t.startswith("bestmove")), "") or "").replace("bestmove ", ""),
            "nodes": nodes,
            "depth": depth,
            "pv": pv,
            "score": score,
            "n_info": len(infos),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path, games_file = sys.argv[1], sys.argv[2]
    with open(games_file) as f:
        data = json.load(f)

    cases = [g for g in data["games"] if g.get("protocol_failure") == "bail"]
    rows = []
    print(f"{len(cases)} bail positions; move-list form vs FEN form of the SAME board\n")
    agree = 0
    for g in cases:
        moves = played_moves(g)
        b = chess.Board()
        for mv in moves:
            b.push_uci(mv)
        fen = b.fen()
        if not moves:
            continue
        ml = ask(path, "position startpos moves " + " ".join(moves), "go depth 12")
        fx = ask(path, f"position fen {fen}", "go depth 12")
        same = ml["bestmove"] == fx["bestmove"]
        agree += same
        legal = [m.uci() for m in b.legal_moves]
        rows.append({
            "seed": g["seed"], "fen": fen, "legal_moves": len(legal),
            "move_list_form": ml, "fen_form": fx, "moves_agree": same,
            "bail_move_legal": ml["bestmove"] in legal,
        })
        print(f"seed {g['seed']}  {fen}")
        print(f"   move-list (bails): {ml['bestmove']:6s} depth={ml['depth']} "
              f"nodes={ml['nodes']} score={ml['score']:8s} pv={ml['pv'][:26]!r}")
        print(f"   fen       (search): {fx['bestmove']:6s} depth={fx['depth']} "
              f"nodes={fx['nodes']} score={fx['score']:8s} pv={fx['pv'][:26]!r}")
        print(f"   moves agree: {same}   bail move legal: {ml['bestmove'] in legal}")
        print()

    print(f"AGREEMENT: {agree}/{len(rows)} bail positions returned the move the engine's own")
    print("search returns for the same board.  Disagreement is the bail's cost.")
    with open("evidence/bail-harm.json", "w") as f:
        json.dump({"rows": rows, "agree": agree, "n": len(rows)}, f, indent=1)
    print("wrote evidence/bail-harm.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
