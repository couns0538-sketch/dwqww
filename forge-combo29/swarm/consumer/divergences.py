"""Resolve two divergences from the findings document.

A. Trap 3aa says every malformed `go` value lands on one identical search: depth 5,
   1001 nodes.  On this build malformed depth lands on depth 1 / 41 nodes, and
   1001 nodes is not a number `go depth 5` produces on the midgame FEN.  Test the
   same requests on STARTPOS, where depth 5 is a different node count, to see
   whether 1001 is a startpos figure.

B. `go nodes abc`, `go nodes`, `go frobnicate` and bare `go` produced no bestmove
   inside 20 s.  Measure where they get to and whether `stop` recovers them.

Usage: python3 divergences.py ENGINE
"""
from __future__ import annotations

import sys
import time

from engine import Engine, EngineDied, EngineTimeout

POSITIONS = {
    "midgame": "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "startpos": "position startpos",
}

REQUESTS = ["go depth 1", "go depth 5", "go depth abc", "go depth"]


def fresh(path: str) -> Engine:
    eng = Engine(path)
    eng.send("uci")
    eng.read_until(lambda w: w.text.strip() == "uciok", 20.0)
    eng.send("setoption name OwnBook value false")
    for _ in range(2):
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
    return eng


def last_info(texts):
    infos = [t for t in texts if t.startswith("info depth")]
    if not infos:
        return None
    p = infos[-1].split()
    d = {"depth": int(p[p.index("depth") + 1])}
    if "nodes" in p:
        d["nodes"] = int(p[p.index("nodes") + 1])
    if "pv" in p:
        d["pv"] = " ".join(p[p.index("pv") + 1:])
    return d


def ask(path: str, pos: str, go: str, deadline: float = 15.0) -> dict:
    eng = fresh(path)
    try:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send(POSITIONS[pos])
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        t = time.monotonic()
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), deadline)
            timed_out = False
        except (EngineTimeout, EngineDied):
            wires = eng.drain_now()
            timed_out = True
        texts = [w.text for w in wires]
        return {
            "pos": pos,
            "go": go,
            "bestmove": next((x for x in texts if x.startswith("bestmove")), None),
            "last": last_info(texts),
            "n_info": len([x for x in texts if x.startswith("info depth")]),
            "elapsed": round(time.monotonic() - t, 3),
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def hang_probe(path: str, go: str, window: float = 8.0) -> dict:
    """Send `go`, wait `window`, then send `stop` and see whether it recovers."""
    eng = fresh(path)
    try:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        eng.send(POSITIONS["midgame"])
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        t = time.monotonic()
        eng.send(go)
        seen = eng.drain_idle(quiet_for=window, cap=window)
        texts = [w.text for w in seen]
        progressed = last_info(texts)
        eng.send("stop")
        recovered = None
        try:
            w2 = eng.read_until(lambda w: w.text.startswith("bestmove"), 10.0)
            recovered = next((w.text for w in w2 if w.text.startswith("bestmove")), None)
        except (EngineTimeout, EngineDied):
            recovered = None
        return {
            "go": go,
            "progress_after_8s": progressed,
            "n_info": len([x for x in texts if x.startswith("info depth")]),
            "stop_bestmove": recovered,
            "stop_latency": round(time.monotonic() - t - window, 3),
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    print("== A. malformed depth, both positions ==")
    for pos in POSITIONS:
        for go in REQUESTS:
            r = ask(path, pos, go)
            last = r["last"] or {}
            print(
                f"  {pos:9s} {go:16s} -> {str(r['bestmove']):14s} depth={last.get('depth')} "
                f"nodes={last.get('nodes')} pv={str(last.get('pv'))[:22]!r} n_info={r['n_info']}"
            )
    print()
    print("== B. unbounded `go` forms: progress at 8 s, then `stop` ==")
    for go in ["go nodes abc", "go nodes", "go frobnicate", "go", "go movestogo 20", "go ponder"]:
        r = hang_probe(path, go)
        pr = r["progress_after_8s"] or {}
        print(
            f"  {go:18s} depth={pr.get('depth')} nodes={pr.get('nodes')} n_info={r['n_info']} "
            f"stop->{r['stop_bestmove']} stop_latency={r['stop_latency']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
