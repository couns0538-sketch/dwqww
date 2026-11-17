"""How long is "unbounded"?  Bounded observation of the no-limit `go` forms.

`go nodes abc`, `go nodes`, `go frobnicate` and bare `go` produce no bestmove.  Trap 24
says depth is clamped at 64, so they *should* end eventually.  This records the depth
reached at increasing observation windows and whether `stop` is the only way out, so
"unbounded" is a measured statement with a window attached rather than an impression.

Usage: python3 unbounded.py ENGINE WINDOW_SECONDS
"""
from __future__ import annotations

import sys
import time

from engine import Engine, EngineDied, EngineTimeout

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"


def observe(path: str, go: str, window: float) -> dict:
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
        eng.send(MIDGAME)
        eng.send("isready")
        eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
        t = time.monotonic()
        eng.send(go)
        got = eng.drain_idle(quiet_for=window, cap=window)
        texts = [w.text for w in got]
        bm = next((x for x in texts if x.startswith("bestmove")), None)
        infos = [x for x in texts if x.startswith("info depth")]
        last_depth = last_nodes = None
        if infos:
            p = infos[-1].split()
            if "depth" in p:
                last_depth = int(p[p.index("depth") + 1])
            if "nodes" in p:
                last_nodes = int(p[p.index("nodes") + 1])
        eng.send("stop")
        try:
            w2 = eng.read_until(lambda w: w.text.startswith("bestmove"), 10.0)
            stop_bm = next((w.text for w in w2 if w.text.startswith("bestmove")), None)
        except (EngineTimeout, EngineDied):
            stop_bm = None
        return {
            "go": go,
            "window": window,
            "returned_on_its_own": bm is not None,
            "bestmove": bm,
            "last_depth": last_depth,
            "last_nodes": last_nodes,
            "n_info": len(infos),
            "stop_bestmove": stop_bm,
            "elapsed": round(time.monotonic() - t, 2),
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    for go in ["go", "go nodes abc", "go nodes", "go frobnicate", "go movestogo 20", "go ponder"]:
        r = observe(path, go, window)
        print(f"{go:18s} window={window:5.0f}s returned={r['returned_on_its_own']!s:5s} "
              f"depth={r['last_depth']} nodes={r['last_nodes']} n_info={r['n_info']} "
              f"stop->{r['stop_bestmove']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
