#!/usr/bin/env python3
"""A2: turn the raw microbench log (a2_kbstats_run.py output) into Markdown tables.

usage: a2_kbstats_table.py <kbstats_raw.log>

Every number printed is computed from the raw counter lines of the log (no other input). Definitions:
  updated evals  = evals - evals_valid - scratch_refresh   (evaluations that replayed >= 1 ply)
  inc cols/node  = 2 * replayed_cols / nodes                (weight columns added/subtracted by the
                                                             incremental updates, both perspectives)
  xm             = king moves made by the search whose own key changes (the spec's "king moves that
                   cross buckets"), per node
  xp             = replayed plies whose mover's key changes = perspective refreshes when every ply is
                   replayed (C4's scheme)
  xe             = (updated evaluation, perspective) pairs whose own key differs between the replay
                   source and the evaluated position = perspective refreshes when a refresh jumps
                   straight to the evaluated position
  cache cols     = weight columns those xe refreshes need with a refresh cache (one entry per
                   perspective and key, cold at the start of every bench position)
  scratch cols   = weight columns those xe refreshes need without a cache (= pieces on the board)
"""
import re
import sys
from collections import defaultdict

HEAD = re.compile(r"a2kb (pos (\d+)|total depth (\d+)) nodes (\d+) evals (\d+) evals_valid (\d+) scratch_refresh (\d+) "
                  r"replayed (\d+) replayed_cols (\d+) moves (\d+) null_moves (\d+) king_moves (\d+)")
LAY = re.compile(r"a2kb (pos (\d+)|total depth (\d+)) layout (\S+) keys (\d+) xm (\d+) xp (\d+) xe (\d+) "
                 r"cache_cols (\d+) scratch_cols (\d+)")
BENCH = re.compile(r"^> bench (\d+)")


def parse(path):
    depth = None
    data = defaultdict(lambda: {"head": {}, "lay": {}})   # key (depth, 'total'|pos) -> dict
    order = []
    for line in open(path, encoding="ascii"):
        m = BENCH.search(line)
        if m:
            depth = int(m.group(1))
            continue
        m = HEAD.search(line)
        if m:
            key = (depth, "total") if m.group(3) else (depth, int(m.group(2)))
            if m.group(3):
                assert int(m.group(3)) == depth
            names = ["nodes", "evals", "evals_valid", "scratch", "replayed", "replayed_cols", "moves", "null_moves", "king_moves"]
            data[key]["head"] = dict(zip(names, map(int, m.groups()[3:])))
            continue
        m = LAY.search(line)
        if m:
            key = (depth, "total") if m.group(3) else (depth, int(m.group(2)))
            name = m.group(4)
            vals = list(map(int, m.groups()[4:]))
            data[key]["lay"][name] = dict(zip(["keys", "xm", "xp", "xe", "cache_cols", "scratch_cols"], vals))
            if name not in order:
                order.append(name)
    return data, order


def main():
    data, order = parse(sys.argv[1])
    depths = sorted({d for d, k in data if k == "total"})
    print("### A. Search totals (bench, Threads 1, Hash 16; all 8 bench positions)\n")
    print("| depth | nodes | evals | evals/node | valid | scratch | updated evals | replayed plies | plies/updated eval "
          "| inc cols/node | moves/node | king moves | king moves/1000 nodes | null moves |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in depths:
        h = data[(d, "total")]["head"]
        upd = h["evals"] - h["evals_valid"] - h["scratch"]
        print(f"| {d} | {h['nodes']:,} | {h['evals']:,} | {h['evals'] / h['nodes']:.4f} | {h['evals_valid']:,} | {h['scratch']:,} "
              f"| {upd:,} | {h['replayed']:,} | {h['replayed'] / upd:.4f} | {2 * h['replayed_cols'] / h['nodes']:.4f} "
              f"| {h['moves'] / h['nodes']:.4f} | {h['king_moves']:,} | {1000 * h['king_moves'] / h['nodes']:.2f} | {h['null_moves']:,} |")
    print()
    for d in depths:
        h = data[(d, "total")]["head"]
        upd = h["evals"] - h["evals_valid"] - h["scratch"]
        inc = 2 * h["replayed_cols"] / h["nodes"]
        print(f"### B. Bench d{d}: refresh counts per layout (nodes {h['nodes']:,}, updated evals {upd:,})\n")
        print("| layout | keys | xm (king moves crossing) | xm/1000 nodes | xm/king move | xp | xp/updated eval | xe | "
              "xe/updated eval | xe/1000 nodes | cache cols/refresh | scratch cols/refresh | refresh cols/node cache "
              "| refresh cols/node scratch | cache refresh cols / inc cols | xe/xp |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for name in order:
            r = data[(d, "total")]["lay"][name]
            xe = max(r["xe"], 1)
            print(f"| {name} | {r['keys']} | {r['xm']:,} | {1000 * r['xm'] / h['nodes']:.3f} | {r['xm'] / max(h['king_moves'], 1):.3f} "
                  f"| {r['xp']:,} | {r['xp'] / upd:.4f} | {r['xe']:,} | {r['xe'] / upd:.4f} | {1000 * r['xe'] / h['nodes']:.3f} "
                  f"| {r['cache_cols'] / xe:.2f} | {r['scratch_cols'] / xe:.2f} | {r['cache_cols'] / h['nodes']:.4f} "
                  f"| {r['scratch_cols'] / h['nodes']:.4f} | {r['cache_cols'] / h['nodes'] / inc:.4f} | {r['xe'] / max(r['xp'], 1):.4f} |")
        print()
    for d in depths:
        positions = sorted(k for dd, k in data if dd == d and k != "total")
        if not positions:
            continue
        sel = [n for n in order if n.split("=")[0] in ("M1", "M4", "M8", "M16", "M32", "R4")]
        print(f"### C. Bench d{d} per position: king moves and perspective refreshes (xe) per updated evaluation\n")
        print("| pos | nodes | share of nodes | king moves/1000 nodes | " + " | ".join(f"{n} xe/upd" for n in sel) + " |")
        print("|---|---|---|---|" + "---|" * len(sel))
        for p in positions:
            h = data[(d, p)]["head"]
            upd = max(h["evals"] - h["evals_valid"] - h["scratch"], 1)
            cells = " | ".join(f"{data[(d, p)]['lay'][n]['xe'] / upd:.4f}" for n in sel)
            share = h["nodes"] / data[(d, "total")]["head"]["nodes"]
            print(f"| {p} | {h['nodes']:,} | {100 * share:.1f}% | {1000 * h['king_moves'] / h['nodes']:.2f} | {cells} |")
        tot = data[(d, "total")]["head"]
        check = sum(data[(d, p)]["head"]["nodes"] for p in positions)
        print(f"\n(per-position nodes sum {check:,} == total {tot['nodes']:,}: {check == tot['nodes']})\n")


if __name__ == "__main__":
    main()
