"""searchmoves arity matrix: which token(s) actually reach the root?

Every row uses the same position and `go depth 8`.  If `searchmoves` worked as specified,
a row listing only legal moves must return one of the listed moves.

Usage: python3 sm_matrix.py ENGINE
"""
from __future__ import annotations

import itertools
import sys

from engine import Engine, EngineDied, EngineTimeout

MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"

LEGAL = ["g1f3", "b1c3", "d2d4", "e1g1", "c4b5", "f3g5"]

ROWS = []
for n in (1, 2, 3, 4, 6):
    ROWS.append((f"legal_x{n}", " ".join(LEGAL[:n])))
ROWS += [
    ("legal_single_c3", "b1c3"),
    ("legal_single_d4", "d2d4"),
    ("legal_single_g1f3", "g1f3"),
    ("illegal_then_legal", "z9z9 g1f3"),
    ("legal_c3_then_illegal", "b1c3 z9z9"),
    ("single_illegal", "z9z9"),
    ("empty", ""),
]


def ask(eng: Engine, go: str) -> dict:
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
    eng.send(MIDGAME)
    eng.send("isready")
    eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
    eng.send(go)
    try:
        wires = eng.read_until(lambda w: w.text.startswith("bestmove"), 30.0)
    except (EngineTimeout, EngineDied) as e:
        wires = eng.drain_now()
        return {"bestmove": None, "error": str(e), "nodes": None, "strings": []}
    texts = [w.text for w in wires]
    bm = next((t for t in texts if t.startswith("bestmove")), None)
    infos = [t for t in texts if t.startswith("info depth")]
    nodes = None
    if infos:
        for tok in infos[-1].split():
            if tok.isdigit():
                pass
        parts = infos[-1].split()
        if "nodes" in parts:
            nodes = int(parts[parts.index("nodes") + 1])
    return {
        "bestmove": bm,
        "nodes": nodes,
        "last_info": infos[-1] if infos else None,
        "strings": [t for t in texts if "info string" in t],
        "n_info": len(infos),
    }


def main() -> int:
    path = sys.argv[1]
    eng = Engine(path)
    eng.send("uci")
    eng.read_until(lambda w: w.text.strip() == "uciok", 20.0)
    eng.send("setoption name OwnBook value false")
    print(f"{'row':26s} {'go':38s} {'bestmove':14s} {'nodes':>8s}  strings")
    try:
        for name, moves in ROWS:
            go = ("go depth 8 searchmoves " + moves).strip()
            r = ask(eng, go)
            print(
                f"{name:26s} {go:38s} {str(r['bestmove']):14s} {str(r['nodes']):>8s}  "
                f"{';'.join(r['strings'])[:60]}"
            )
    finally:
        eng.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
