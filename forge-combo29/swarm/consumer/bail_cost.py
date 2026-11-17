"""What does a naive client LOSE by playing the bail move?

Two arms, same engine, same openings, same seed, same 50 ms clock:
  strict : refuses to play a 0-node/empty-pv move -> the game ends as a protocol failure
  naive  : plays it -> the game continues

A naive client is the realistic GUI (it just plays `bestmove`).  The question is whether
the bail actually costs chess, or merely annoys a strict client.  For every bail the naive
arm played, this compares the move played against what the engine's own search returns for
the same board -- using the FEN form, which (trap 2d) does NOT bail, so it is a legitimate
view of what the search would have chosen.

Then it reports the naive arm's decisive-game statistics against the strict arm's.

Usage: python3 bail_cost.py ENGINE evidence/games-100-strict.json evidence/games-100-naive.json
"""
from __future__ import annotations

from evio import load_json

import json
import sys

import chess

from engine import Engine, EngineDied, EngineTimeout


def ask_fen(path: str, fen: str, go: str = "go depth 12", deadline: float = 40.0) -> dict:
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
        except (EngineTimeout, EngineDied):
            return {"bestmove": None, "timed_out": True}
        texts = [w.text for w in wires]
        infos = [t for t in texts if t.startswith("info depth")]
        score = None
        if infos:
            p = infos[-1].split()
            if "score" in p:
                i = p.index("score")
                score = f"{p[i + 1]} {p[i + 2]}"
        return {
            "bestmove": next((t for t in texts if t.startswith("bestmove")), "").replace("bestmove ", ""),
            "score": score,
            "timed_out": False,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    strict = load_json(sys.argv[2])
    naive = load_json(sys.argv[3])

    # every BAIL ply the naive arm actually played
    bails = []
    for g in naive["games"]:
        board = chess.Board()
        for mv in g["opening"]:
            board.push_uci(mv)
        for ply in g["plies"]:
            if ply["category"] == "BAIL":
                bails.append({"seed": g["seed"], "ply": ply["n"], "fen": board.fen(),
                              "played": ply["bestmove"]})
            if ply["bestmove"] and ply["bestmove"] != "0000":
                board.push_uci(ply["bestmove"])

    print(f"{len(bails)} bail moves PLAYED by the naive arm\n")
    agree = 0
    sample = []
    for b in bails[:40]:
        r = ask_fen(path, b["fen"])
        same = r["bestmove"] == b["played"]
        agree += same
        sample.append({**b, "searched": r["bestmove"], "searched_score": r["score"], "same": same})
    n = min(40, len(bails))
    print(f"move agreement on {n} sampled bail positions: {agree}/{n} "
          f"({100.0 * agree / n:.0f}%)\n")
    for s in sample:
        print(f"  seed {s['seed']:5d} ply {s['ply']:3d} played {s['played']:6s} "
              f"searched {str(s['searched']):6s} score {str(s['searched_score']):8s} "
              f"{'SAME' if s['same'] else 'DIFFERENT'}")

    print("\n=== match outcomes ===")
    for label, d in (("strict", strict), ("naive", naive)):
        s = d["summary"]
        games = d["games"]
        decided = [g for g in games if not g["unfinished"]]
        mate = sum(1 for g in games if g["result"] == "checkmate")
        print(f"  {label:7s} games={s['games']} plies={s['total_plies']} "
              f"protocol_failures={s['protocol_failures']} unfinished={s['unfinished']} "
              f"checkmates={mate} decided={len(decided)}")

    with open("evidence/bail-cost.json", "w") as f:
        json.dump({"n": n, "agree": agree, "sample": sample}, f, indent=1)
    print("\nwrote evidence/bail-cost.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
