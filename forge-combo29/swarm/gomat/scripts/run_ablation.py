#!/usr/bin/env python3
"""Measurement 3: which disabled heuristics actually change the mate ANSWER.

For each ablation arm (one gate, or two gates at a time) this runs the same
corpus under `go mate N` and asks a behavioural question, not a node question:

  * does the arm change the MATE ANSWER (score kind/value) at any N?
  * does it change the MOVE at any N?
  * does it change the node count, and by how much?

A gate whose arm changes nothing is not evidence the gate is irrelevant — it is
evidence that on THIS corpus the gate is not load-bearing. The corpus is
endgame-heavy on purpose, which is where a mate search lives, and that scope
limit is printed with the result rather than left for the reader.

Each arm is verified distinct by sha256 against the control before its numbers
are accepted (the build step already refuses duplicate binaries; this is the
second, independent check at measurement time).

Usage: run_ablation.py --dir /tmp/ab --corpus corpus.json --out ablation.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402

MAX_N = 4


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_arm(exe: str, fens: list[tuple[str, str]], timeout: float) -> dict:
    out: dict[str, dict] = {}
    with Engine(exe, {"OwnBook": "false"}) as eng:
        for rid, fen in fens:
            eng.newgame()
            eng.setpos(fen)
            for n in range(1, MAX_N + 1):
                res = eng.go(f"go mate {n}", timeout=timeout)
                out[f"{rid}|mate{n}"] = {
                    "score": res.last_score,
                    "bestmove": res.bestmove,
                    "depth": res.last_depth,
                    "nodes": res.last_nodes,
                    "timed_out": res.timed_out,
                }
    return out


def classify(base: dict, arm: dict) -> dict:
    """Compare one arm with the control request by request."""
    answer_changes = []
    move_changes = []
    node_ratios = []
    timeouts = 0
    for key, b in base.items():
        a = arm.get(key)
        if a is None:
            continue
        if a["timed_out"]:
            timeouts += 1
        if a["score"] != b["score"]:
            answer_changes.append({"key": key, "base": b, "arm": a})
        elif a["bestmove"] != b["bestmove"]:
            move_changes.append({"key": key, "base": b, "arm": a})
        if b["nodes"] and a["nodes"]:
            node_ratios.append(a["nodes"] / b["nodes"])
    return {
        "answer_changes": len(answer_changes),
        "move_changes_same_score": len(move_changes),
        "examples": answer_changes[:6],
        "move_examples": move_changes[:4],
        "node_ratio_max": round(max(node_ratios), 4) if node_ratios else None,
        "node_ratio_min": round(min(node_ratios), 4) if node_ratios else None,
        "timeouts": timeouts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp/ab")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus))
    fens = [(r["id"], r["fen"]) for bucket in corpus["mate"].values() for r in bucket]
    fens += [(r["id"], r["fen"]) for r in corpus["nomate"]]

    builds = []
    with open(os.path.join(args.dir, "BUILDS.txt")) as fh:
        next(fh)
        for line in fh:
            name, gates, digest = line.rstrip("\n").split("\t")
            builds.append((name, gates, digest))

    control = next(b for b in builds if b[0] == "control")
    control_hash = sha256(os.path.join(args.dir, "control", "build", "forge"))
    assert control_hash == control[2], "control binary changed since BUILDS.txt"

    print(f"corpus: {len(fens)} positions x {MAX_N} mate depths = {len(fens) * MAX_N} requests per arm")
    print(f"control sha256 {control_hash[:16]}")
    base = run_arm(os.path.join(args.dir, "control", "build", "forge"), fens, args.timeout)
    print(f"control run done ({len(base)} requests)\n", flush=True)

    only = {o for o in args.only.split(",") if o}
    results = []
    header = f"{'arm':28s} {'gates':34s} {'answers':>7s} {'moves':>6s} {'nodemin':>8s} {'nodemax':>8s}"
    print(header)
    print("-" * len(header))
    for name, gates, digest in builds:
        if name == "control" or (only and name not in only):
            continue
        exe = os.path.join(args.dir, name, "build", "forge")
        live_hash = sha256(exe)
        if live_hash != digest:
            raise SystemExit(f"{name}: binary hash does not match BUILDS.txt")
        if live_hash == control_hash:
            raise SystemExit(f"{name}: binary IS the control; not an ablation arm")
        arm = run_arm(exe, fens, args.timeout)
        cmp = classify(base, arm)
        results.append({"arm": name, "gates": gates, "sha256": digest, **cmp})
        print(f"{name:28s} {gates:34s} {cmp['answer_changes']:7d} "
              f"{cmp['move_changes_same_score']:6d} "
              f"{str(cmp['node_ratio_min']):>8s} {str(cmp['node_ratio_max']):>8s}", flush=True)

    json.dump({"control_sha256": control_hash, "positions": len(fens),
               "max_n": MAX_N, "arms": results}, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
