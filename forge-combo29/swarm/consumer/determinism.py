"""Determinism check: same cold process, same commands, `go movetime 0`.

Two of this seat's own harnesses disagreed about `go movetime abc` on one FEN
(one saw `depth 5 / 896 nodes`, the other `a2a3` with zero info lines).  A client
cannot be written against a reply that is not reproducible, so measure the rate
before believing either reading.

Usage: python3 determinism.py ENGINE N
"""
from __future__ import annotations

import sys

from engine import Engine, EngineDied, EngineTimeout

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"


def once(path: str, go: str, pos: str) -> dict:
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
        eng.send(pos)
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), 15.0)
            timed_out = False
        except (EngineTimeout, EngineDied):
            wires = eng.drain_now()
            timed_out = True
        texts = [w.text for w in wires]
        infos = [t for t in texts if t.startswith("info depth")]
        return {
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "n_info": len(infos),
            "last_info": infos[-1] if infos else None,
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for go in ["go movetime 0", "go movetime abc"]:
        shapes = {}
        for _ in range(n):
            r = once(path, go, MIDGAME)
            key = (r["bestmove"], r["n_info"])
            shapes[key] = shapes.get(key, 0) + 1
        print(f"{go}: {n} cold runs")
        for (bm, ni), count in sorted(shapes.items(), key=lambda kv: -kv[1]):
            print(f"   {count:3d}/{n}  bestmove={bm}  n_info={ni}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
