#!/usr/bin/env python3
"""patch_narrow.py BASE PATCHED OUT.tsv — is the patch narrow?

The claim in S-F17 is that the patch only changes behaviour on drawn/adjudicated roots. If that is true,
then on every position where the base engine actually SEARCHES, the patched engine must return the same
bestmove, the same node count and the same score. Any difference there would mean the patch changed the
search itself, not just the shortcut, and S-F17's "narrow" claim would be false.

Method: 120 positions (O and G), `go depth 10`, both binaries, fresh process per position per binary.
Classifies each position by whether the base engine reported 0 nodes (shortcut fired) or searched.

Usage: patch_narrow.py BASE PATCHED OUT.tsv
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

DEPTH = 10
N = 120


def probe(exe, fen):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"go depth {DEPTH}")
    out, ok = eng.read_until("bestmove", 120)
    eng.close()
    best, nodes, score = "", 0, ""
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
            if "score" in f:
                score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
    return {"best": best, "nodes": nodes, "score": score, "ok": ok}


def main() -> int:
    base, patched, out = sys.argv[1], sys.argv[2], sys.argv[3]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], N)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    rows = []
    searched = 0
    differ = 0
    shortcut = 0
    for fen in fens:
        b = probe(base, fen)
        p = probe(patched, fen)
        same = (b["best"] == p["best"] and b["nodes"] == p["nodes"] and b["score"] == p["score"])
        if b["nodes"] == 0:
            shortcut += 1
            kind = "shortcut (base 0 nodes)"
        else:
            searched += 1
            kind = "searched"
            if not same:
                differ += 1
        rows.append((fen, kind, b["best"], b["nodes"], b["score"], p["best"], p["nodes"], p["score"],
                     same))
    print("| fen | base class | base bestmove | base nodes | base score | patched bestmove | "
          "patched nodes | patched score | identical |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        if r[1] == "shortcut (base 0 nodes)" or not r[8]:
            print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | {r[8]} |")
    print()
    print(f"positions {len(rows)}: base searched {searched}, base used the shortcut {shortcut}")
    print(f"searched positions where the patched engine DIFFERS: {differ} "
          f"({'NARROW — patch only affects shortcut roots' if differ == 0 else 'NOT NARROW — patch changed the search'})")
    with open(out, "w") as fh:
        fh.write("fen\tclass\tbase_best\tbase_nodes\tbase_score\tpatched_best\tpatched_nodes\t"
                 "patched_score\tidentical\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    return 1 if differ else 0


if __name__ == "__main__":
    raise SystemExit(main())
