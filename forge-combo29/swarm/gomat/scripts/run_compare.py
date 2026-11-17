#!/usr/bin/env python3
"""Measurement 5: the comparability table, `go mate N` vs `go depth 2N-1`.

Two corpora, because the corpus is part of the claim:

  * REAL — 200 real game positions (O) and 353 from games (G). This is where the
    owner's question lives: does a mate label on a real board mean what a depth
    label means?
  * MATE — the proven-DTM endgames, where `go mate N` is at its best.

For every cell it records both searches' bestmove, score, reported depth, node
count and wall time, plus the node ratio and whether the answers agree.

The 163x cell of findings §3a is reproduced as ONE ROW INSIDE A DISTRIBUTION,
which is the whole point of the exercise: an outlier claim is not usable unless
a reader can see its neighbours. The ratio distribution is reported by
quantiles, and the top rows are printed with the full context.

A note on what a ratio means here. `go depth 2N-1` and `go mate N` both label
themselves `depth 2N-1`, so the ratio is the price of the mate-mode search at a
comparable-looking label — not of extra depth.

Usage: run_compare.py --exe build/forge --out compare.json [--limit 200]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import pv_replays_to_mate  # noqa: E402


def load_fens(path: str, limit: int | None) -> list[tuple[str, str]]:
    out = []
    with open(path) as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fen = " ".join(line.split()[:6]) if ";" in line or len(line.split()) > 6 else line
            try:
                board = chess.Board(fen)
            except ValueError:
                continue
            if board.status() != chess.STATUS_VALID:
                continue
            out.append((f"{os.path.basename(path)}:{i + 1}", fen))
            if limit and len(out) >= limit:
                break
    return out


def search(eng: Engine, fen: str, cmd: str, timeout: float) -> dict:
    eng.newgame()
    eng.setpos(fen)
    res = eng.go(cmd, timeout=timeout)
    return {
        "bestmove": res.bestmove,
        "score_kind": (res.last_score or (None, None))[0],
        "score_value": (res.last_score or (None, None))[1],
        "depth": res.last_depth,
        "nodes": res.last_nodes,
        "wall_s": round(res.wall_s, 5),
        "pv": res.last_pv,
        "info_lines": len(res.info_depths),
        "timed_out": res.timed_out,
    }


def run(exe: str, corpus: list[tuple[str, str]], label: str, out_path: str,
        timeout: float, max_n: int) -> list[dict]:
    rows = []
    print(f"\n=== {label}: {len(corpus)} positions x {max_n} N x 2 modes")
    with Engine(exe, {"OwnBook": "false"}) as eng:
        for i, (rid, fen) in enumerate(corpus):
            board = chess.Board(fen)
            legal = board.legal_moves.count()
            eng.newgame()
            eng.setpos(fen)
            eng.send("go perft 1")
            gate = None
            for ln in eng.expect("nodes", timeout=60):
                if ln.startswith("nodes "):
                    gate = int(ln.split()[1])
            if gate != legal:
                print(f"  {rid}: BOARD GATE FAILED ({gate} vs {legal}) -- skipped")
                continue
            for n in range(1, max_n + 1):
                m = search(eng, fen, f"go mate {n}", timeout)
                d = search(eng, fen, f"go depth {2 * n - 1}", timeout)
                # Verify any positive mate claim the engine made, in python-chess.
                if m["score_kind"] == "mate" and (m["score_value"] or 0) > 0:
                    ok, detail = pv_replays_to_mate(board, m["pv"])
                    want = 2 * m["score_value"] - 1
                    m["claim_verified"] = ok and len(m["pv"]) == want
                    m["claim_detail"] = f"{detail}; plies={len(m['pv'])} want={want}"
                else:
                    m["claim_verified"] = None
                if d["score_kind"] == "mate" and (d["score_value"] or 0) > 0:
                    ok, detail = pv_replays_to_mate(board, d["pv"])
                    want = 2 * d["score_value"] - 1
                    d["claim_verified"] = ok and len(d["pv"]) == want
                    d["claim_detail"] = f"{detail}; plies={len(d['pv'])} want={want}"
                else:
                    d["claim_verified"] = None
                ratio = (m["nodes"] / d["nodes"]) if (m["nodes"] and d["nodes"]) else None
                same_answer = (m["bestmove"] == d["bestmove"]
                               and m["score_kind"] == d["score_kind"]
                               and m["score_value"] == d["score_value"])
                rows.append({
                    "id": rid, "fen": fen, "N": n, "label_depth": 2 * n - 1,
                    "mate": m, "depth": d, "node_ratio": round(ratio, 4) if ratio else None,
                    "same_answer": same_answer,
                    "same_move": m["bestmove"] == d["bestmove"],
                })
            if (i + 1) % 25 == 0:
                print(f"  ... {i + 1}/{len(corpus)}", flush=True)
    json.dump(rows, open(out_path, "w"), indent=1)
    print(f"  wrote {out_path} ({len(rows)} cells)")
    return rows


def summarise(rows: list[dict], label: str) -> str:
    lines = [f"\n--- {label}: {len(rows)} cells"]
    if not rows:
        return "\n".join(lines)
    ratios = sorted(r["node_ratio"] for r in rows if r["node_ratio"])
    def q(p):
        return ratios[min(len(ratios) - 1, int(p * (len(ratios) - 1)))]
    lines.append(f"node ratio mate/depth  min {ratios[0]:.3f}  q25 {q(.25):.3f}  "
                 f"median {q(.5):.3f}  q75 {q(.75):.3f}  q95 {q(.95):.3f}  max {ratios[-1]:.3f}")
    diff = [r for r in rows if not r["same_answer"]]
    diffmove = [r for r in rows if not r["same_move"]]
    lines.append(f"differing answers {len(diff)}/{len(rows)}  differing moves {len(diffmove)}/{len(rows)}")
    for n in sorted({r["N"] for r in rows}):
        sub = [r for r in rows if r["N"] == n]
        dd = [r for r in sub if not r["same_answer"]]
        rs = sorted(r["node_ratio"] for r in sub if r["node_ratio"])
        lines.append(f"  N={n} (label depth {2*n-1}): differ {len(dd)}/{len(sub)}, "
                     f"median ratio {rs[len(rs)//2]:.3f}, max {rs[-1]:.3f}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--o", default="/tmp/first200.fens")
    ap.add_argument("--g", default="/tmp/set_G.epd")
    ap.add_argument("--mate-corpus")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--max-n", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    all_summ = []
    real = []
    if os.path.exists(args.o):
        real += load_fens(args.o, args.limit)
    if os.path.exists(args.g):
        real += load_fens(args.g, args.limit)
    if real:
        rows = run(args.exe, real, "REAL (O+G)", os.path.join(args.outdir, "compare_real.json"),
                   args.timeout, args.max_n)
        all_summ.append(summarise(rows, "REAL (O+G)"))

    if args.mate_corpus:
        corpus = json.load(open(args.mate_corpus))
        mates = [(r["id"], r["fen"]) for bucket in corpus["mate"].values() for r in bucket]
        rows = run(args.exe, mates, "PROVEN-DTM ENDGAMES",
                   os.path.join(args.outdir, "compare_mate.json"), args.timeout, args.max_n)
        all_summ.append(summarise(rows, "PROVEN-DTM ENDGAMES"))

    print("\n".join(all_summ))
    with open(os.path.join(args.outdir, "compare_summary.txt"), "w") as fh:
        fh.write("\n".join(all_summ) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
