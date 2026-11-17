#!/usr/bin/env python3
"""Determinism of `go depth N` and `go nodes N` at Threads 1/2/4/8.

Method notes that matter for reading the output (see FINDINGS.md):
- Every search is preceded by `ucinewgame` + `position`, so the ONLY state that can
  differ between two repeats is the multithreading. `ucinewgame` is a cold reset on
  this engine (findings §7 trap 3: 0 of 25 differ from a fresh process), so a
  difference left over is not warm-TT drift.
- A "signature" is (nodes, score_kind, score, bestmove). WALL TIME IS NOT PART OF IT.
  An earlier probe of mine counted wall time in the signature and reported Threads 1
  as 2/4 distinct; that was the instrument, not the engine.
- Node counts at Threads > 1 are a SUM over workers (search.cpp:2696-2705) and are
  therefore not comparable to Threads 1. Within one thread count they are compared
  only against each other.

Usage: python3 determinism.py <exe> <fens> <out.jsonl> <repeats> <limit-kind> <limit-args...>
  limit-kind: depth | nodes
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

THREADS = (1, 2, 4, 8)


def signature(info, best):
    d = last_depth_info(info)
    if d is None:
        return {"no_info_depth": True, "bestmove": best.split()[-1] if best else None}
    return {
        "no_info_depth": False,
        "nodes": d["nodes"],
        "depth": d["depth"],
        "score_kind": d.get("score_kind"),
        "score": d.get("score"),
        "bestmove": best.split()[-1] if best else None,
    }


def main():
    exe, fens_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    repeats = int(sys.argv[4])
    limit_kind = sys.argv[5]
    limit_args = sys.argv[6] if len(sys.argv) > 6 else "12"
    go_cmd = f"{limit_kind} {limit_args}"

    with open(fens_path) as fh:
        fens = [line.strip() for line in fh if line.strip()]
    # both inputs are bare six-field FENs (set_G.epd holds FENs with no EPD opcodes)
    for fen in fens:
        if fen.count(" ") != 5:
            raise SystemExit(f"not a six-field FEN: {fen!r}")

    rows = []
    for threads in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": threads}, timeout=300.0)
        # A control that the Threads option actually reached the engine: the reply
        # to `uci` is not a statement about the applied value, so assert behaviour
        # later (see multithread_control.py). Here we only record what we sent.
        for idx, fen in enumerate(fens):
            for rep in range(repeats):
                e.ucinewgame()
                e.position(fen)
                info, best, wall = e.go(go_cmd)
                sig = signature(info, best)
                rows.append({
                    "threads": threads, "idx": idx, "rep": rep, "fen": fen,
                    "limit": go_cmd, "sig": sig, "wall": round(wall, 4),
                    "n_info_depth": len([l for l in info if l.startswith("info depth")]),
                })
        e.close()
        print(f"threads {threads} done", flush=True)

    with open(out_path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {out_path}  ({len(rows)} searches)")


if __name__ == "__main__":
    main()
