"""Targeted controls for two contradictions the sweep turned up.

1. `searchmoves` with ONE legal + ONE illegal token: findings sec 1b / trap 3a00 say the
   illegal token is silently DROPPED and the legal move is searched.  The sweep saw
   "no legal root moves" + 0000.  Controls: legal-only, illegal-only, and the same
   two-token list in both orders.
2. `go depth abc`: trap 3aa says it lands on depth 5 / 1001 nodes.  The sweep saw a
   single depth-1 line.  Controls: `go depth 5`, `go depth 1`, `go depth` (no value).

Usage: python3 controls.py ENGINE OUT.json
"""
from __future__ import annotations

import json
import sys

from engine import Engine, EngineDied, EngineTimeout
from probe import enc

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"

GO_CASES = [
    ("control_depth1", "go depth 1"),
    ("control_depth5", "go depth 5"),
    ("control_depth_noval", "go depth"),
    ("probe_depth_abc", "go depth abc"),
    ("control_nodes0", "go nodes 0"),
    ("control_nodes1", "go nodes 1"),
    ("control_movetime0", "go movetime 0"),
    ("control_movetime_abc", "go movetime abc"),
    ("control_wtime_abc", "go wtime abc"),
    ("sm_legal_only", "go depth 8 searchmoves g1f3"),
    ("sm_legal_illegal", "go depth 8 searchmoves g1f3 z9z9"),
    ("sm_illegal_legal", "go depth 8 searchmoves z9z9 g1f3"),
    ("sm_two_legal_one_illegal", "go depth 8 searchmoves g1f3 b1c3 z9z9"),
    ("sm_illegal_only", "go depth 8 searchmoves z9z9"),
    ("sm_duplicate_legal", "go depth 8 searchmoves g1f3 g1f3"),
    ("sm_enemy_piece_move", "go depth 8 searchmoves g8f6"),
    ("sm_no_such_move_but_legal_shape", "go depth 8 searchmoves a1a8"),
]


def run(path: str, name: str, go: str) -> dict:
    out = {"case": name, "go": go, "lines": [], "sent": [], "events": []}
    eng = Engine(path)
    t0 = None
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
        import time

        t0 = time.monotonic()
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), 40.0)
        except (EngineTimeout, EngineDied) as e:
            wires = eng.drain_now()
            out["events"].append({"what": "bestmove", "ok": False, "error": str(e)})
        for w in wires:
            out["lines"].append(enc(w.text))
        out["elapsed"] = round(time.monotonic() - t0, 4)
    finally:
        eng.quit()
    infos = [l for l in out["lines"] if l.startswith("info depth")]
    out["n_info"] = len(infos)
    out["last_info"] = infos[-1] if infos else None
    out["first_info"] = infos[0] if infos else None
    out["strings"] = [l for l in out["lines"] if "string" in l]
    out["bestmove"] = next((l for l in out["lines"] if l.startswith("bestmove")), None)
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    path, out_path = sys.argv[1], sys.argv[2]
    results = []
    for name, go in GO_CASES:
        r = run(path, name, go)
        results.append(r)
        print(f"{name:32s} {go:45s} -> {r.get('bestmove')}  info={r['n_info']}", flush=True)
    with open(out_path, "w") as f:
        json.dump({"engine": path, "results": results}, f, indent=1)
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
