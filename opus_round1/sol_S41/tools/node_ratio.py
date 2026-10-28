#!/usr/bin/env python3
"""Tree-size check for an option: fixed-depth searches on many positions, OFF then ON, in one engine process.

Each search starts from a cleared state (ucinewgame + the option's own hash clear), so every search is independent
and deterministic. Prints per-position nodes and the summary: total ON/OFF node ratio, median and quartiles of the
per-position ratios, and the share of positions whose tree changes by more than 20%. Idle priority on Windows.

  node_ratio.py <exe> --fens positions.txt --first 300 --count 100 --depth 12 --on NetScale=99 [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys

import subprocess

IDLE_PRIORITY_CLASS = 0x00000040


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--fens", required=True)
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--on", action="append", required=True, help="NAME=VALUE (repeat)")
    ap.add_argument("--off", action="append", default=[], help="NAME=VALUE restoring OFF (default: none)")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    lines = open(a.fens, encoding="utf-8").read().splitlines()[a.first:a.first + a.count]
    fens = [l.split("|")[0].strip() for l in lines]
    flags = IDLE_PRIORITY_CLASS if os.name == "nt" else 0
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, creationflags=flags)

    def send(s: str) -> None:
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat: str) -> tuple[re.Match, list[str]]:
        rx = re.compile(pat)
        seen = []
        for line in p.stdout:
            seen.append(line)
            m = rx.search(line)
            if m:
                return m, seen
        raise SystemExit("engine exited before " + pat)

    send("uci")
    wait(r"^uciok")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + o)

    def run_all() -> list[int]:
        out = []
        for fen in fens:
            send("ucinewgame")
            send("position fen " + fen)
            send(f"go depth {a.depth}")
            _, seen = wait(r"^bestmove")
            nodes = [int(m.group(1)) for l in seen for m in [re.search(r"\bnodes (\d+)", l)] if m]
            out.append(nodes[-1] if nodes else 0)
        return out

    for o in a.off:
        n, v = o.split("=", 1)
        send(f"setoption name {n} value {v}")
    send("isready")
    wait(r"^readyok")
    off = run_all()
    for o in a.on:
        n, v = o.split("=", 1)
        send(f"setoption name {n} value {v}")
    send("isready")
    wait(r"^readyok")
    on = run_all()
    send("quit")
    p.wait(timeout=60)
    ratios = [b / a_ for a_, b in zip(off, on) if a_ > 0]
    q = statistics.quantiles(ratios, n=4) if len(ratios) >= 4 else [float("nan")] * 3
    res = {"exe": a.exe, "depth": a.depth, "positions": len(fens), "first": a.first, "on": a.on,
           "total_off": sum(off), "total_on": sum(on), "total_ratio": sum(on) / sum(off),
           "median_ratio": statistics.median(ratios), "q1": q[0], "q3": q[2],
           "share_abs_change_gt_20pct": sum(1 for r in ratios if abs(r - 1) > 0.20) / len(ratios),
           "identical": sum(1 for x, y in zip(off, on) if x == y), "nodes_off": off, "nodes_on": on}
    print(f"{os.path.basename(a.exe)} depth {a.depth} positions {len(fens)} ON {' '.join(a.on)}: total ON/OFF "
          f"{res['total_ratio']:.4f} (OFF {res['total_off']} ON {res['total_on']}), per-position median "
          f"{res['median_ratio']:.4f} IQR {res['q1']:.4f}-{res['q3']:.4f}, |change|>20%: "
          f"{100 * res['share_abs_change_gt_20pct']:.0f}%, identical trees {res['identical']}")
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=2)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
