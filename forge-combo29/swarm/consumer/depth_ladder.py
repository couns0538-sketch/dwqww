"""Sec 1b's precise claim: the info-line count on a bailed root is min(request, 64), not a depth.

The document says: "10 lines at `go depth 10`, but 64 lines under both `go nodes 1000` and
`go nodes 100000`, because the depth field defaults to 64 and the clamp passes it through."

This measures the line count on a drawn root for each budget kind.  A client that reads
"64 info lines" as "searched to depth 64" is the failure this pins down.

Usage: python3 depth_ladder.py ENGINE
"""
from __future__ import annotations

import sys

from engine import Engine, EngineDied, EngineTimeout

BARE = "position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1"
REPEAT = "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"

BUDGETS = [
    "go depth 1", "go depth 5", "go depth 10", "go depth 20", "go depth 64", "go depth 100",
    "go nodes 1000", "go nodes 100000", "go nodes 0", "go nodes 1",
    "go movetime 50", "go wtime 5000 btime 5000",
]


def ask(path: str, pos: str, go: str, deadline: float = 20.0) -> dict:
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
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), deadline)
            timed_out = False
        except (EngineTimeout, EngineDied):
            wires = eng.drain_now()
            timed_out = True
        texts = [w.text for w in wires]
        infos = [t for t in texts if t.startswith("info depth")]
        depths = []
        nodes = set()
        pvs_empty = 0
        for t in infos:
            p = t.split()
            if "depth" in p:
                depths.append(int(p[p.index("depth") + 1]))
            if "nodes" in p:
                nodes.add(int(p[p.index("nodes") + 1]))
            if p and (p[-1] == "pv" or "pv" not in p):
                pvs_empty += 1
        return {
            "go": go,
            "n_info": len(infos),
            "last_depth": depths[-1] if depths else None,
            "nodes_set": sorted(nodes),
            "empty_pv_lines": pvs_empty,
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    for label, pos in (("bare kings", BARE), ("threefold by move list", REPEAT)):
        print(f"=== drawn root: {label}")
        print(f"{'go':28s} {'n_info':>6s} {'last_depth':>10s} {'nodes':>8s} {'empty_pv':>8s}  bestmove")
        for go in BUDGETS:
            r = ask(path, pos, go)
            nset = ",".join(str(x) for x in r["nodes_set"])
            print(f"{go:28s} {r['n_info']:>6d} {str(r['last_depth']):>10s} {nset:>8s} "
                  f"{r['empty_pv_lines']:>8d}  {r['bestmove']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
