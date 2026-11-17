"""Exact node counts for malformed `go` values, with a reference row beside each.

Trap 3aa says seven malformed requests all land on one identical search: depth 5,
1001 nodes.  This measures each request's node count against `go depth 1` and
`go depth 5` controls, because a claim about "one identical search" is a claim
about node counts, not about the number of info lines.

Usage: python3 go_values.py ENGINE OUT.json
"""
from __future__ import annotations

import json
import sys

from engine import Engine, EngineDied, EngineTimeout

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"

CASES = [
    # references
    ("ref_depth1", "go depth 1"),
    ("ref_depth2", "go depth 2"),
    ("ref_depth5", "go depth 5"),
    ("ref_movetime1", "go movetime 1"),
    ("ref_movetime10", "go movetime 10"),
    ("ref_wtime_btime", "go wtime 10000 btime 10000"),
    # malformed depth
    ("bad_depth_abc", "go depth abc"),
    ("bad_depth_noval", "go depth"),
    ("bad_depth_negative", "go depth -3"),
    ("bad_depth_empty", "go depth 0"),
    # malformed nodes
    ("bad_nodes_abc", "go nodes abc"),
    ("bad_nodes_noval", "go nodes"),
    # malformed movetime
    ("bad_movetime_abc", "go movetime abc"),
    ("bad_movetime_noval", "go movetime"),
    ("bad_movetime_0", "go movetime 0"),
    # malformed clock
    ("bad_wtime_abc", "go wtime abc"),
    ("bad_wtime_noval", "go wtime"),
    ("bad_wtime_0", "go wtime 0"),
    # unknown tokens
    ("unknown_token", "go depth 5 frobnicate 3"),
    ("unknown_only", "go frobnicate"),
    ("bare_go", "go"),
]


def parse_last_info(text: str | None) -> dict:
    if not text:
        return {}
    p = text.split()
    out = {}
    for key in ("depth", "seldepth", "nodes", "nps", "time", "hashfull", "multipv"):
        if key in p:
            try:
                out[key] = int(p[p.index(key) + 1])
            except (ValueError, IndexError):
                pass
    if "score" in p:
        i = p.index("score")
        out["score_kind"] = p[i + 1] if i + 1 < len(p) else None
        try:
            out["score"] = int(p[i + 2])
        except (ValueError, IndexError):
            pass
    if "pv" in p:
        out["pv"] = " ".join(p[p.index("pv") + 1:])
    return out


def run(path: str, go: str, deadline: float = 20.0) -> dict:
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
        eng.send(go)
        timed_out = False
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), deadline)
        except (EngineTimeout, EngineDied):
            wires = eng.drain_now()
            timed_out = True
        texts = [w.text for w in wires]
        infos = [t for t in texts if t.startswith("info depth")]
        bm = next((t for t in texts if t.startswith("bestmove")), None)
        return {
            "go": go,
            "bestmove": bm,
            "n_info": len(infos),
            "last_info": infos[-1] if infos else None,
            "last": parse_last_info(infos[-1] if infos else None),
            "all_nodes": [parse_last_info(t).get("nodes") for t in infos],
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path, out = sys.argv[1], sys.argv[2]
    results = []
    print(f"{'case':24s} {'go':28s} {'bm':13s} {'d':>3s} {'nodes':>9s} {'sd':>4s}  first-line")
    for name, go in CASES:
        r = run(path, go)
        r["case"] = name
        results.append(r)
        last = r["last"]
        first_nodes = r["all_nodes"][0] if r["all_nodes"] else None
        print(
            f"{name:24s} {go:28s} {str(r['bestmove']).replace('bestmove ',''):13s} "
            f"{str(last.get('depth')):>3s} {str(last.get('nodes')):>9s} {str(last.get('seldepth')):>4s}  "
            f"first_nodes={first_nodes} n_info={r['n_info']}{' TIMEOUT' if r['timed_out'] else ''}"
        )
    with open(out, "w") as f:
        json.dump({"engine": path, "results": results}, f, indent=1)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
