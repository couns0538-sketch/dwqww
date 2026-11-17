"""Focused test: `go movetime 0` / `go movetime abc` on a midgame FEN.

The sweep showed a 0-node reply (`bestmove a2a3`, no info lines) on the midgame FEN but
`depth 5 / 1001 nodes` on startpos for the same command.  Trap 2d0 warns that a 0-node
`a2a3` row and a piped-abort row look identical, so repeat cold and warm, and check the
TT dependence the doc describes.

Usage: python3 movetime_zero.py ENGINE
"""
from __future__ import annotations

import sys

from engine import Engine, EngineDied, EngineTimeout

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"


def one(path: str, go: str, *, warm: bool, pos: str = MIDGAME) -> dict:
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
        if warm:
            eng.send(pos)
            eng.send("isready")
            eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
            eng.send("go depth 8")
            eng.read_until(lambda w: w.text.startswith("bestmove"), 30.0)
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
            "go": go,
            "warm": warm,
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "n_info": len(infos),
            "last_info": infos[-1] if infos else None,
            "first_info": infos[0] if infos else None,
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    for go in ["go movetime 0", "go movetime abc", "go movetime 1", "go movetime 10"]:
        for warm in (False, True):
            rows = [one(path, go, warm=warm) for _ in range(3)]
            bms = {r["bestmove"] for r in rows}
            ninfos = {r["n_info"] for r in rows}
            print(
                f"{go:18s} warm={str(warm):5s}  bestmove={sorted(bms)}  n_info={sorted(ninfos)}  "
                f"last={rows[0]['last_info']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
