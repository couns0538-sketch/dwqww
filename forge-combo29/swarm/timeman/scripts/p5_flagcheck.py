#!/usr/bin/env python3
"""P5: is a flagged move a real overshoot, or harness wall-clock overhead?

The engine reports `time <elapsed>` on every info line, measured from its own
search start (src/search.cpp:2245). This harness measures wall time from just
before writing `go`. Those two differ by pipe write, scheduling, and the
bestmove print. When wall says "flagged" and the engine's own time says
otherwise, the forfeit is a measurement artefact and must be withdrawn.

Replays each move of a recorded game with exactly the clock the game gave the
engine, and reports for every move:
    wall_ms        harness round trip
    engine_ms      the `time` field of the LAST info line
    tail_ms        wall_ms - engine_ms   (the harness's own overhead)
    plan_soft/hard for that input
"""
from __future__ import annotations

import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

OVH = 10


def last_time_field(info_lines):
    for line in reversed(info_lines):
        parts = line.split()
        for i, tok in enumerate(parts):
            if tok == "time" and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    continue
    return None


def main():
    exe, game_json, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.load(open(game_json))
    game = data["games"][0]

    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", str(data.get("threads", 1)))

    board = chess.Board()
    for mv in game["opening"]:
        board.push(chess.Move.from_uci(mv))

    rows = []
    for m in game["moves"]:
        my = m["clock_before"]
        inc = m["inc"]
        opp = my  # opponent clock value does not enter the planner for the mover
        fen = board.fen()
        spec = f"wtime {int(my)} btime {int(opp)} winc {inc} binc {inc}"
        if m["side"] == "black":
            spec = f"wtime {int(opp)} btime {int(my)} winc {inc} binc {inc}"
        e.send(f"position fen {fen}")
        r = e.go(spec, timeout=max(10.0, my / 1000.0 + 20.0))
        eng = last_time_field(r.info_lines)
        soft, hard, _ = plan_clock(int(my), inc, 0, OVH)
        rows.append({
            "ply": m["ply"],
            "side": m["side"],
            "clock_before": int(my),
            "inc": inc,
            "wall_ms": round(r.wall_ms, 3),
            "engine_ms": eng,
            "tail_ms": None if eng is None else round(r.wall_ms - eng, 3),
            "plan_soft": soft,
            "plan_hard": hard,
            "depth": r.depth_reached,
            "recorded_wall": m["wall_ms"],
            "reproduced_move": r.bestmove,
            "recorded_move": m["bestmove"],
            "match": r.bestmove == m["bestmove"],
        })
        if board.is_game_over(claim_draw=False):
            break
        board.push(chess.Move.from_uci(m["bestmove"]))
    e.close()

    with open(outpath, "w") as f:
        json.dump({"exe": exe, "game": game_json, "rows": rows}, f, indent=2)

    print(f"{'ply':>4} {'side':<5} {'clock':>7} {'wall':>9} {'engine':>7} {'tail':>7} "
          f"{'plan':>10} {'depth':>5} match")
    for r in rows:
        print(f"{r['ply']:>4} {r['side']:<5} {r['clock_before']:>7} {r['wall_ms']:>9.2f} "
              f"{str(r['engine_ms']):>7} {str(r['tail_ms']):>7} "
              f"{r['plan_soft']}/{r['plan_hard']:<6} {r['depth']:>5} {r['match']}")
    print("wrote", outpath)


if __name__ == "__main__":
    main()
