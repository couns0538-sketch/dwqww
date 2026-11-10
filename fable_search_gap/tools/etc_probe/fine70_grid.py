"""Tabulate the pawn-ending perturbation grid (standard library only).

usage: fine70_grid.py OUT.md OUT.tsv BASELINE.tsv GRID_o40.tsv GRID_o38.tsv ...

Each input is a TSV written by etc_probe.exe on positions_fine70.epd (one position, depths 24 to 40).
BASELINE.tsv is the run with the default history offset (-32). Every GRID file is the same set of runs
with one history constant changed by a small amount. The change is not a mechanism: it is a placebo
applied to the plain search and to every setting of the mechanism alike.

The winning move is a1b1. For every setting the table counts in how many of the perturbed copies the
best move is a1b1 at every depth, and in how many it is not at some depth.
"""
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinguard  # noqa: E402

WIN = "a1b1"
ORDER = ["off", "etc_cut4", "etc_cut6", "etc_cut6_ns", "etc_cut6_fh", "etc_cut8", "etc_cut8_ns", "etc_cut8_fh", "etc_all3"]
NAMES = {"off": "plain", "etc_cut4": "cut4", "etc_cut6": "cut6", "etc_cut6_ns": "cut6, no store",
         "etc_cut6_fh": "cut6, return beta", "etc_cut8": "cut8", "etc_cut8_ns": "cut8, no store",
         "etc_cut8_fh": "cut8, return beta", "etc_all3": "all3"}


def load(path):
    by_run = defaultdict(list)
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            by_run[r["run"]].append(r)
    return by_run


def main():
    pinguard.ensure()
    out_md, out_tsv, baseline = sys.argv[1], sys.argv[2], sys.argv[3]
    grids = sys.argv[4:]
    files = [("baseline", load(baseline))] + [(os.path.basename(p), load(p)) for p in grids]
    with open(out_tsv, "w", encoding="utf-8", newline="\n") as o:
        o.write("file\trun\tdepth\tbest\tscore\tnodes\taborted\n")
        for name, by_run in files:
            for run in ORDER:
                for r in by_run.get(run, []):
                    o.write(f"{name}\t{run}\t{r['depth']}\t{r['best']}\t{r['score']}\t{r['nodes']}\t{r['aborted']}\n")
    lines = ["# Pawn ending (Fine 70) under placebo-size changes", "",
             f"Baseline plus {len(grids)} perturbed copies. Each copy changes one history constant of the replica by a small",
             "amount and is run plain and with every setting of the mechanism, at depths 24, 26, 28, 30, 32, 34, 36 and 40.",
             "The winning move is 1.Kb1 (`a1b1`). Terms: `tools/etc_probe/summarize.py`.", "",
             "| Setting | Baseline | Perturbed copies with Kb1 at every depth | Copies with another move at some depth | "
             "Copies with another move at depth 40 | Nodes at depth 40: smallest to largest over the copies |",
             "|---|---|---|---|---|---|"]
    for run in ORDER:
        base_rows = files[0][1].get(run, [])
        base_bad = [r["depth"] for r in base_rows if r["best"] != WIN]
        base_txt = "Kb1 at every depth" if not base_bad else "other move at depth " + ", ".join(base_bad)
        good = bad = bad40 = capped = 0
        nodes40 = []
        for _name, by_run in files[1:]:
            rr = by_run.get(run, [])
            if not rr:
                continue
            if any(int(r["aborted"]) for r in rr):
                capped += 1
                continue
            if all(r["best"] == WIN for r in rr):
                good += 1
            else:
                bad += 1
            last = [r for r in rr if r["depth"] == "40"]
            if last:
                nodes40.append(int(last[0]["nodes"]))
                if last[0]["best"] != WIN:
                    bad40 += 1
        span = f"{min(nodes40) / 1e6:.2f} M to {max(nodes40) / 1e6:.2f} M" if nodes40 else "-"
        note = f" ({capped} stopped by the node cap)" if capped else ""
        lines.append(f"| {NAMES[run]} | {base_txt} | {good} of {good + bad}{note} | {bad} of {good + bad} | {bad40} of {good + bad} | {span} |")
    lines.append("")
    text = "\n".join(lines) + "\n"
    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
