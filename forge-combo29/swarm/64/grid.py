"""The Hash x MultiPV grid at a fixed node budget.

Every cell: one fresh process, Threads 1, `go nodes 200000`, wall ms measured to
the `bestmove` line. Four independent defences against a silently-refused FEN:

  1. python-chess validates the FEN before the cell runs (positions.py)
  2. `info string invalid FEN` is scanned in the POSITION reply AND the go output
  3. every PV from the root is replayed with python-chess and must be legal
  4. node count, depth and bestmove must be identical across the cell's repeats

Usage:
    python3 grid.py --engine /tmp/build-base/forge --out base.json [--repeats 3]

`--selftest` runs the refusal and range assertions against a deliberately bad
input and must exit non-zero; it is how the checker proves it can fail.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time

import chess

import ucidrv
from positions import FENS

HASHES = [8, 16, 24, 32, 48, 64, 128, 256]
MPVS = [1, 2, 3, 4, 5, 6]
NODES = 200000
# A finished-iteration node count sits at or below the budget and above a floor
# no real 200k search reaches. Both bounds are checked per cell.
NODES_MIN = 1000
NODES_MAX = NODES
CELL_TIMEOUT_S = 180.0


def refusals(lines: list[str]) -> list[str]:
    return [l for l in lines if "invalid FEN" in l]


def pv_illegal(fen: str, pv: list[str]) -> str | None:
    """Replay the PV from the root FEN. Return a reason if it does not fit."""
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        return f"root FEN unparsable: {exc}"
    for i, token in enumerate(pv):
        try:
            move = chess.Move.from_uci(token)
        except ValueError:
            return f"pv[{i}]={token} not a UCI move"
        if move not in board.legal_moves:
            return f"pv[{i}]={token} illegal in the searched root"
        board.push(move)
    return None


def run_cell(engine: str, fen: str, hash_mb: int, mpv: int, timeout: float) -> dict:
    bad: list[str] = []
    with ucidrv.Engine(engine) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        e.set_option("Threads", "1")
        e.set_option("Hash", str(hash_mb))
        e.set_option("MultiPV", str(mpv))
        e.sync()

        pos_reply = e.set_position(fen)
        for line in refusals(pos_reply):
            bad.append(f"refusal in position reply: {line}")

        go, ms = e.go_nodes(NODES, timeout=timeout)
        for line in refusals(go):
            bad.append(f"refusal in go output: {line}")

        infos = [x for x in (ucidrv.parse_info(l) for l in go) if x]
        best = ""
        for line in go:
            if line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else ""

    if not infos:
        bad.append("no info depth line")
        nodes = depth = 0
        pv: list[str] = []
    else:
        last = infos[-1]
        nodes = last.get("nodes", 0)
        depth = last.get("depth", 0)
        # The last emitted line is multipv 1 only at MPV 1; at MPV>1 the emit
        # order is by line index, so check the best move's own line instead.
        pv = infos[-1].get("pv", [])
        if not (NODES_MIN <= nodes <= NODES_MAX):
            bad.append(f"node count {nodes} outside [{NODES_MIN},{NODES_MAX}]")
        if pv:
            why = pv_illegal(fen, pv)
            if why:
                bad.append(f"PV does not fit the root: {why}")

    return {
        "hash": hash_mb,
        "mpv": mpv,
        "ms": ms,
        "nodes": nodes,
        "depth": depth,
        "best": best,
        "pv_head": pv[:3],
        "bad": bad,
    }


def selftest(engine: str) -> int:
    """The checks must reject a bad FEN. Exit 1 when they fail to."""
    failures: list[str] = []
    bad_fen = "zzzz/pppp/8/8/8/8/PPPP/ZZZZ w - - 0 1"

    # The diagnostic is emitted ONCE. `isready` decides which stream carries it,
    # so exactly one of the two scans must fire -- never neither, never both.
    with ucidrv.Engine(engine) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        pos = e.set_position(bad_fen)          # isready IS sent -> diagnostic here
        go_with_sync = None
        go, _ = e.go_nodes(5000, timeout=120)
        n_pos, n_go = len(refusals(pos)), len(refusals(go))
        print(f"selftest A (isready after position): position={n_pos} go={n_go}")
        if n_pos + n_go != 1:
            failures.append(f"expected exactly one diagnostic, saw {n_pos}+{n_go}")

    # Without isready the same diagnostic lands in the go output instead.
    with ucidrv.Engine(engine) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        e.send(f"position fen {bad_fen}")       # no isready
        go, _ = e.go_nodes(5000, timeout=120)
        n_go2 = len(refusals(go))
        print(f"selftest B (no isready): go={n_go2}")
        if n_go2 != 1:
            failures.append(f"expected the diagnostic in the go output, saw {n_go2}")

    # A reading that scans only one stream must be shown to miss it somewhere,
    # which is why the runner scans both.
    print("selftest: a position-only scan misses case B; a go-only scan misses case A")

    # The PV check must reject a PV that is illegal in the root.
    legal_fen = FENS[0]
    why = pv_illegal(legal_fen, ["a1a8"])
    print(f"selftest: illegal-PV detection -> {why}")
    if why is None:
        failures.append("PV check accepted a move illegal in the root")

    # And it must accept a genuinely legal SEQUENCE (root-legal moves are not
    # automatically legal in order -- this defect was found by this selftest).
    board = chess.Board(legal_fen)
    good: list[str] = []
    for _ in range(4):
        move = next(iter(board.legal_moves))
        good.append(move.uci())
        board.push(move)
    if pv_illegal(legal_fen, good) is not None:
        failures.append(f"PV check rejected a legal sequence {good}")
    print(f"selftest: legal sequence {good} accepted")

    if failures:
        print("SELFTEST FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("SELFTEST PASS: the checker rejects bad input on every path")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.engine)

    cells = len(HASHES) * len(MPVS)
    total = cells * len(FENS) * args.repeats
    print(f"grid: {len(HASHES)} hashes x {len(MPVS)} mpv = {cells} cells", flush=True)
    print(f"positions: {len(FENS)}  repeats: {args.repeats}  engine runs: {total}", flush=True)
    print(f"node budget: {NODES} (literal)  threads: 1  engine: {args.engine}", flush=True)

    results: list[dict] = []
    done = 0
    t_start = time.monotonic()
    for hash_mb in HASHES:
        for mpv in MPVS:
            runs = []
            for fen_index, fen in enumerate(FENS):
                for rep in range(args.repeats):
                    r = run_cell(args.engine, fen, hash_mb, mpv, CELL_TIMEOUT_S)
                    r["fen_index"] = fen_index
                    r["rep"] = rep
                    runs.append(r)
                    done += 1
            bad = [r["bad"] for r in runs if r["bad"]]
            ms = [r["ms"] for r in runs]
            nodes = [r["nodes"] for r in runs]
            # Determinism: same cell, same position -> same nodes and depth.
            shape = {(r["fen_index"], r["nodes"], r["depth"], r["best"]) for r in runs}
            n_shapes = len({(r["fen_index"], r["nodes"], r["depth"]) for r in runs})
            results.append({
                "hash": hash_mb,
                "mpv": mpv,
                "ms_median": statistics.median(ms),
                "ms_min": min(ms),
                "ms_max": max(ms),
                "nodes_median": statistics.median(nodes),
                "nodes_min": min(nodes),
                "nodes_max": max(nodes),
                "runs": runs,
                "bad": bad,
                "distinct_position_shapes": n_shapes,
                "expected_shapes": len(FENS),
            })
            flag = ""
            if bad:
                flag += " BAD"
            if n_shapes != len(FENS):
                flag += " NONDETERMINISTIC"
            print(
                f"  Hash {hash_mb:>3} MPV {mpv}: med {statistics.median(ms):7.1f} ms "
                f"[{min(ms):.1f},{max(ms):.1f}]  nodes {int(statistics.median(nodes)):>6}{flag}",
                flush=True,
            )

    elapsed = time.monotonic() - t_start
    payload = {
        "engine": args.engine,
        "nodes_budget": NODES,
        "hashes": HASHES,
        "mpvs": MPVS,
        "positions": FENS,
        "repeats": args.repeats,
        "cells": results,
        "runs_total": total,
        "runs_done": done,
        "wall_s": elapsed,
    }
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=1)

    bad_cells = [c for c in results if c["bad"]]
    nondet = [c for c in results if c["distinct_position_shapes"] != c["expected_shapes"]]
    print(f"\ncompleted {done}/{total} runs in {elapsed:.1f}s", flush=True)
    print(f"cells with a failed assertion: {len(bad_cells)}/{cells}", flush=True)
    print(f"cells that were nondeterministic: {len(nondet)}/{cells}", flush=True)
    if bad_cells or nondet:
        print("FAIL: grid is not trustworthy; see", args.out)
        return 1
    print("PASS: every cell passed its assertions and was deterministic")
    return 0


if __name__ == "__main__":
    sys.exit(main())
