#!/usr/bin/env python3
"""Repro of O1 bug 1 (stale helper node counters) over UCI.
After a deep multi-thread search the helpers' published node counts stay at their final values.
At the next `go nodes N`, the main thread checks the node budget at every node and sums those
stale counts before the helpers have reset them, so the search stops before depth 1 completes and
the engine plays the first legal move unsearched (no info line). Works on the AL1 s198 lock exe;
on the O1 build compare SmpExactNodes=false/true.
usage: repro_stale_nodes.py <engine> [--threads 3] [--rounds 10] [--option Name=Value ...]"""
import argparse
import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucilib import Engine  # noqa: E402

KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--nodes", type=int, default=20000)
    ap.add_argument("--option", action="append", default=[])
    a = ap.parse_args()
    eng = Engine(a.engine)
    eng.handshake([("Hash", 16), ("OwnBook", "false"), ("Threads", a.threads)] +
                  [tuple(o.split("=", 1)) for o in a.option])
    unsearched = 0
    for r in range(a.rounds):
        eng.send(f"position fen {KIWI}")
        eng.send("go depth 13")
        eng.expect(lambda l: l.startswith("bestmove"), 600, "bestmove of the deep search")
        eng.send(f"go nodes {a.nodes}")
        line, seen = eng.expect(lambda l: l.startswith("bestmove"), 600, "bestmove of the node search")
        infos = [l for l in seen if l.startswith("info depth ")]
        depth = int(re.search(r"^info depth (\d+)", infos[-1]).group(1)) if infos else 0
        nodes = re.search(r" nodes (\d+)", infos[-1]).group(1) if infos else "-"
        unsearched += depth == 0
        print(f"round {r}: go nodes {a.nodes} -> {line}  (completed depth {depth}, last info nodes {nodes})")
    eng.quit()
    print(f"{unsearched}/{a.rounds} node-limited searches returned before completing depth 1")


if __name__ == "__main__":
    main()
