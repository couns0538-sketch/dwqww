"""Is trap 3aa's 'depth 5 / 1001 nodes' reachable by any malformed `go` on this build?

1001 nodes is what `go depth 5` costs on STARTPOS on this binary, so if the doc's
figure is a startpos figure it should appear here.  Every malformed form in the
doc's list is run on startpos with a cold reset, beside the `go depth 5` control.

Usage: python3 trap3aa_startpos.py ENGINE
"""
from __future__ import annotations

import sys

from engine import Engine, EngineDied, EngineTimeout
from go_values import parse_last_info

MALFORMED = [
    "go depth abc",
    "go depth",
    "go nodes abc",
    "go nodes",
    "go movetime abc",
    "go movetime 0",
    "go wtime abc",
]
CONTROLS = ["go depth 5", "go depth 1", "go movetime 1"]


def run(path: str, go: str, deadline: float = 12.0) -> dict:
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
        eng.send("position startpos")
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
        last = parse_last_info(infos[-1] if infos else None)
        return {
            "go": go,
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "depth": last.get("depth"),
            "nodes": last.get("nodes"),
            "pv": last.get("pv"),
            "n_info": len(infos),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    print(f"{'go':22s} {'bestmove':14s} {'depth':>5s} {'nodes':>9s} {'n_info':>6s}  pv")
    for go in CONTROLS + MALFORMED:
        r = run(path, go)
        tag = " (control)" if go in CONTROLS else ""
        print(
            f"{go:22s} {str(r['bestmove']):14s} {str(r['depth']):>5s} {str(r['nodes']):>9s} "
            f"{r['n_info']:>6d}  {str(r['pv'])[:26]}{' TIMEOUT' if r['timed_out'] else ''}{tag}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
