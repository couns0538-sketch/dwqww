"""Render GRID.md from a grid JSON, with every denominator printed literally."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--patch", default=None)
    ap.add_argument("--title", default="Grid")
    args = ap.parse_args()

    with open(args.base) as fh:
        data = json.load(fh)
    cells = {(c["hash"], c["mpv"]): c for c in data["cells"]}
    hashes, mpvs = data["hashes"], data["mpvs"]
    n_pos, n_rep = len(data["positions"]), data["repeats"]
    n_runs = data["runs_done"]

    print(f"# {args.title}\n")
    print(f"Engine: `{data['engine']}`  ")
    print(f"Budget: `go nodes {data['nodes_budget']}` (literal), Threads 1, fresh process per cell  ")
    print(f"Positions per cell: {n_pos} (listed below), repeats per position: {n_rep}  ")
    print(f"Runs completed: {n_runs}/{data['runs_total']} in {data['wall_s']:.1f} s  ")
    print(f"Cells: {len(data['cells'])}/{len(hashes) * len(mpvs)} "
          f"({len(hashes)} Hash x {len(mpvs)} MultiPV)\n")

    print("Every number below is `median [min, max]` over "
          f"{n_pos * n_rep} engine runs per cell "
          f"({n_pos} positions x {n_rep} repeats).\n")

    print("## Median wall milliseconds to `bestmove`\n")
    hdr = "| Hash MB |" + "".join(f" MPV {m} |" for m in mpvs)
    print(hdr)
    print("|---:|" + "---:|" * len(mpvs))
    for h in hashes:
        row = f"| {h} |"
        for m in mpvs:
            c = cells[(h, m)]
            row += f" {c['ms_median']:.1f} |"
        print(row)

    print("\n## Min / max wall milliseconds per cell\n")
    for h in hashes:
        print(f"### Hash {h} MB\n")
        print("| MultiPV | median | min | max | nodes (median) | depth |")
        print("|---:|---:|---:|---:|---:|---:|")
        for m in mpvs:
            c = cells[(h, m)]
            print(f"| {m} | {c['ms_median']:.1f} | {c['ms_min']:.1f} | {c['ms_max']:.1f} "
                  f"| {int(c['nodes_median'])} | {max(r['depth'] for r in c['runs'])} |")
        print()

    print("## Ratio to MultiPV 1 at the same Hash\n")
    print("> 1.00 means slower than the single-line search on the same Hash setting. "
          "`!` marks cells above 1.5x.\n")
    print(hdr)
    print("|---:|" + "---:|" * len(mpvs))
    for h in hashes:
        base = cells[(h, 1)]["ms_median"]
        row = f"| {h} |"
        for m in mpvs:
            r = cells[(h, m)]["ms_median"] / base
            row += f" {r:.2f}{'!' if r > 1.5 else ''} |"
        print(row)

    print("\n## Nodes actually searched (not the budget)\n")
    print("`go nodes N` stops when a *finished iteration* crosses the budget, so the "
          "reported count is below N and varies by cell. The budget is shared with the "
          "alternate lines, which is why nodes fall as MultiPV rises.\n")
    print(hdr)
    print("|---:|" + "---:|" * len(mpvs))
    for h in hashes:
        row = f"| {h} |"
        for m in mpvs:
            row += f" {int(cells[(h, m)]['nodes_median'])} |"
        print(row)

    print("\n## Positions\n")
    for i, fen in enumerate(data["positions"]):
        print(f"{i}. `{fen}`")

    print("\n## Assertion status per cell\n")
    bad = [c for c in data["cells"] if c["bad"]]
    nondet = [c for c in data["cells"] if c["distinct_position_shapes"] != c["expected_shapes"]]
    print(f"- cells with a failed assertion: {len(bad)}/{len(data['cells'])}")
    print(f"- cells that were nondeterministic: {len(nondet)}/{len(data['cells'])}")
    if bad:
        for c in bad:
            print(f"  - Hash {c['hash']} MPV {c['mpv']}: {c['bad'][:2]}")

    if args.patch:
        with open(args.patch) as fh:
            pdata = json.load(fh)
        pcells = {(c["hash"], c["mpv"]): c for c in pdata["cells"]}
        print(f"\n# Patched build (between-line `tt.clear()` removed)\n")
        print(f"Runs completed: {pdata['runs_done']}/{pdata['runs_total']} "
              f"in {pdata['wall_s']:.1f} s\n")
        print("## Median wall milliseconds, patched\n")
        print(hdr)
        print("|---:|" + "---:|" * len(mpvs))
        for h in hashes:
            row = f"| {h} |"
            for m in mpvs:
                row += f" {pcells[(h, m)]['ms_median']:.1f} |"
            print(row)
        print("\n## Ratio to patched MultiPV 1 at the same Hash\n")
        print(hdr)
        print("|---:|" + "---:|" * len(mpvs))
        for h in hashes:
            base = pcells[(h, 1)]["ms_median"]
            row = f"| {h} |"
            for m in mpvs:
                r = pcells[(h, m)]["ms_median"] / base
                row += f" {r:.2f}{'!' if r > 1.5 else ''} |"
            print(row)
        print("\n## Speedup from the patch (base ms / patched ms), per cell\n")
        print(hdr)
        print("|---:|" + "---:|" * len(mpvs))
        for h in hashes:
            row = f"| {h} |"
            for m in mpvs:
                row += f" {cells[(h, m)]['ms_median'] / pcells[(h, m)]['ms_median']:.2f} |"
            print(row)
        pbad = [c for c in pdata["cells"] if c["bad"]]
        print(f"\n- patched cells with a failed assertion: {len(pbad)}/{len(pdata['cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
