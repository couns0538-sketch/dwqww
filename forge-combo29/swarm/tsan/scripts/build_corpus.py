#!/usr/bin/env python3
"""Build the 40-position corpus for the TSan run and validate every FEN.

Validation is two-sided per brief rule 4: python-chess must accept the FEN AND
the engine must not refuse it.  A refused FEN silently searches nothing.
"""
import json
import subprocess
import sys

import chess

CORPUS_SRC = "/home/ubuntu/work/forge/forge-combo29/soak_all/search_corpus.txt"  # or argv[2]
OUT = None  # set from argv


def pick(seed_positions, n=40):
    """Deterministic spread across the corpus, preferring distinct material
    profiles so the run is not 40 copies of the same middlegame."""
    seen = {}
    chosen = []
    step = max(1, len(seed_positions) // (n * 4))
    for i in range(0, len(seed_positions), step):
        fen = seed_positions[i].strip()
        if not fen or fen.startswith("#"):
            continue
        try:
            b = chess.Board(fen)
        except ValueError:
            continue
        if not b.is_valid():
            continue
        sig = (len(b.piece_map()), b.turn)
        if seen.get(sig, 0) >= 3:
            continue
        seen[sig] = seen.get(sig, 0) + 1
        # python-chess normalises the ep square away when no ep capture is
        # legal; use the ORIGINAL text so the engine sees what the corpus says.
        chosen.append({"fen": fen, "turn": "w" if b.turn else "b",
                       "pieces": len(b.piece_map())})
        if len(chosen) == n:
            break
    return chosen


def engine_accepts(exe, fen):
    """The engine reports a refused FEN on the `position` command."""
    cmds = "uci\nisready\nposition fen %s\nisready\nquit\n" % fen
    out = subprocess.run([exe], input=cmds, capture_output=True, text=True,
                         timeout=120).stdout
    bad = [l for l in out.splitlines()
           if "invalid" in l.lower() or "illegal position" in l.lower()]
    return (not bad), bad


def main():
    global OUT, CORPUS_SRC
    exe = sys.argv[1]
    if len(sys.argv) > 2:
        OUT = sys.argv[2]
    if len(sys.argv) > 3:
        CORPUS_SRC = sys.argv[3]
    src = [l for l in open(CORPUS_SRC)]
    chosen = pick(src, 40)
    assert len(chosen) == 40, "only got %d" % len(chosen)
    kept, refused = [], []
    for c in chosen:
        ok, bad = engine_accepts(exe, c["fen"])
        if ok:
            kept.append(c)
        else:
            refused.append({"fen": c["fen"], "why": bad})
    print("accepted %d / refused %d" % (len(kept), len(refused)))
    print("wrote", OUT)
    if refused:
        for r in refused:
            print("  REFUSED:", r["fen"], r["why"])
    json.dump({"corpus": kept, "refused": refused, "source": CORPUS_SRC},
              open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
