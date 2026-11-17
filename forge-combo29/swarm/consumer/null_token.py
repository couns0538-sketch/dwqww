"""The `0000` question: when is the null token correct, and what does the score say?

Sec 1b gives the discriminator: `mate 0` means checkmate, `cp 0` means stalemate or an
empty restriction.  Trap 3ac0 adds the harder case: **`0000` can be CORRECT on a root
that is already won.**  A client that treats `0000` as an error would throw away a
correct answer; a client that treats it as a move would play nothing and forfeit.

This enumerates the cases a client can actually meet and records what the wire says,
including the score that has to decide it.

Usage: python3 null_token.py ENGINE
"""
from __future__ import annotations

import sys

import chess

from engine import Engine, EngineDied, EngineTimeout

CASES = [
    ("checkmate", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", "go depth 10"),
    ("stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go depth 10"),
    ("mate_in_1_for_mover", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "go depth 10"),
    ("bare_kings", "8/8/8/4k3/8/8/8/4K3 w - - 0 1", "go depth 10"),
    ("kvk_insufficient", "8/8/8/4k3/8/8/8/4K2R w - - 0 1", "go depth 10"),
    ("empty_searchmoves", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
     "go depth 10 searchmoves"),
    ("legal_searchmoves_one", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
     "go depth 10 searchmoves b1c3"),
]


def ask(path: str, fen: str, go: str, deadline: float = 20.0) -> dict:
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
        eng.send(f"position fen {fen}")
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
        last = infos[-1] if infos else None
        score, nodes, pv_tok = None, None, None
        if last:
            p = last.split()
            if "score" in p:
                i = p.index("score")
                score = f"{p[i + 1]} {p[i + 2]}"
            if "nodes" in p:
                nodes = int(p[p.index("nodes") + 1])
            pv_tok = "pv" in p
        return {
            "bestmove": next((t for t in texts if t.startswith("bestmove")), None),
            "score": score,
            "nodes": nodes,
            "has_pv_token": pv_tok,
            "n_info": len(infos),
            "strings": [t for t in texts if "info string" in t],
            "timed_out": timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    print(f"{'case':24s} {'bestmove':14s} {'score':9s} {'nodes':>8s} {'legal':>5s}  client reading")
    for name, fen, go in CASES:
        r = ask(path, fen, go)
        b = chess.Board(fen)
        legal = len(list(b.legal_moves))
        bm = (r["bestmove"] or "").replace("bestmove ", "")
        if bm == "0000":
            if r["score"] == "mate 0" and legal == 0:
                reading = "CORRECT no-move (checkmate)"
            elif legal == 0:
                reading = "CORRECT no-move (stalemate)"
            elif r["strings"]:
                reading = "no-move with a diagnostic (restriction)"
            else:
                reading = "!! no move on a LIVE board, no diagnostic"
        else:
            reading = "real move"
        print(f"{name:24s} {bm:14s} {str(r['score']):9s} {str(r['nodes']):>8s} {legal:>5d}  {reading}")
        if r["strings"]:
            print(f"    strings: {r['strings']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
