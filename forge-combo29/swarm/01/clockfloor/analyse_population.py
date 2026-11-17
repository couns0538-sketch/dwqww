#!/usr/bin/env python3
"""swarm seat 01: does the SAMPLE's node-ratio tail reproduce at POPULATION scale? (S-C62)

`S-C46`/`S-C54` rest on **116 pairs** taken at a 1 % stride from 11,192 positions. Everything about PC20's cost rests on
that sample: the median 0.926, the mean 1.214, the tail to 18.4x, and the claim that the node ratio is bimodal while
per-node cost is uniform.

**A stride sample is exactly the instrument that `S-C42` caught me using wrongly** - twelve hand-picked positions that
gave 50 % where the population gave 44 %. So the question this answers is not "is the sample roughly right" but:

  * does the **median** hold at population scale, or did the stride flatter it?
  * does the **mean** hold, or was it an artefact of a handful of positions?
  * how **heavy** is the tail - what fraction exceeds 2x, 5x, 10x - and is the 18.4x maximum representative?
  * does **per-node cost** stay uniform, or does it have a tail too?

The last one matters because `S-C54`'s reconciliation (uniform per-node tax x bimodal node count) depends on it, and a
per-node tail would break the decomposition.

Usage: analyse_population.py <pairs.jsonl> <outdir> [--sample-pairs N]
"""
import json
import statistics
import sys
from pathlib import Path


def load(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("ratio") and r.get("node_ratio"):
            rows.append(r)
    return rows


def q(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def summarise(rows, label):
    nr = [r["node_ratio"] for r in rows]
    wr = [r["ratio"] for r in rows]
    # implied per-node for each pair: wall / node
    pn = [r["ratio"] / r["node_ratio"] for r in rows if r["node_ratio"]]
    out = {
        "label": label, "n": len(rows),
        "node_median": statistics.median(nr), "node_mean": statistics.mean(nr),
        "node_q1": q(nr, .25), "node_q3": q(nr, .75), "node_min": min(nr), "node_max": max(nr),
        "wall_median": statistics.median(wr), "wall_mean": statistics.mean(wr),
        "pernode_median": statistics.median(pn), "pernode_q1": q(pn, .25), "pernode_q3": q(pn, .75),
        "pernode_max": max(pn), "pernode_min": min(pn),
        "frac_lt1": 100.0 * sum(1 for x in nr if x < 1) / len(nr),
        "gt2": sum(1 for x in nr if x > 2), "gt5": sum(1 for x in nr if x > 5),
        "gt10": sum(1 for x in nr if x > 10),
    }
    return out


def line_for(s):
    return ("%-22s n=%-6d node med %.3f mean %.3f Q1 %.3f Q3 %.3f max %5.2f | wall med %.3f | "
            "per-node med %.3f Q1 %.3f Q3 %.3f max %.2f | fewer on %.1f %%"
            % (s["label"], s["n"], s["node_median"], s["node_mean"], s["node_q1"], s["node_q3"], s["node_max"],
               s["wall_median"], s["pernode_median"], s["pernode_q1"], s["pernode_q3"], s["pernode_max"],
               s["frac_lt1"]))


def main():
    src, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rows = load(src)
    if not rows:
        print("NOTHING TO ANALYSE: no usable pairs in %s" % src)
        return 1

    # the earlier 1 % stride sample was 116 pairs from the same file; compare like with like
    n_sample = 116
    if "--sample-pairs" in sys.argv:
        n_sample = int(sys.argv[sys.argv.index("--sample-pairs") + 1])
    stride = max(1, len(rows) // n_sample)
    sample = rows[::stride][:n_sample]

    pop = summarise(rows, "POPULATION")
    smp = summarise(sample, "the old stride sample")

    L = ["S-C62: does the sample's node-ratio tail reproduce at population scale?",
         "source: %s" % src, ""]
    L.append(line_for(pop))
    L.append(line_for(smp))
    L.append("")
    L.append("TAIL SHAPE, population vs sample")
    L.append("  node ratio > 2x : population %d of %d (%.1f %%) | sample %d of %d (%.1f %%)"
             % (pop["gt2"], pop["n"], 100.0 * pop["gt2"] / pop["n"],
                smp["gt2"], smp["n"], 100.0 * smp["gt2"] / smp["n"]))
    L.append("  node ratio > 5x : population %d (%.2f %%) | sample %d (%.2f %%)"
             % (pop["gt5"], 100.0 * pop["gt5"] / pop["n"], smp["gt5"], 100.0 * smp["gt5"] / smp["n"]))
    L.append("  node ratio >10x : population %d (%.2f %%) | sample %d (%.2f %%)"
             % (pop["gt10"], 100.0 * pop["gt10"] / pop["n"], smp["gt10"], 100.0 * smp["gt10"] / smp["n"]))
    L.append("")
    L.append("PER-NODE COST, which S-C54's reconciliation depends on being UNIFORM")
    L.append("  population: median %.3f, Q1 %.3f, Q3 %.3f, range %.2f-%.2f"
             % (pop["pernode_median"], pop["pernode_q1"], pop["pernode_q3"],
                pop["pernode_min"], pop["pernode_max"]))
    L.append("  If Q1..Q3 is narrow and the range is not extreme, per-node cost is a near-constant multiplier and the")
    L.append("  bimodal node ratio is the whole story - which is what S-C54 claimed from 116 pairs.")
    L.append("")

    # does the sample's median survive?
    L.append("DOES THE SAMPLE HOLD?")
    L.append("  node median: population %.4f vs sample %.4f -> difference %.4f"
             % (pop["node_median"], smp["node_median"], smp["node_median"] - pop["node_median"]))
    L.append("  wall median: population %.4f vs sample %.4f -> difference %.4f"
             % (pop["wall_median"], smp["wall_median"], smp["wall_median"] - pop["wall_median"]))
    L.append("  mean node ratio: population %.4f vs sample %.4f -> difference %+.4f"
             % (pop["node_mean"], smp["node_mean"], smp["node_mean"] - pop["node_mean"]))
    L.append("")
    dmed = abs(smp["node_median"] - pop["node_median"])
    if dmed <= 0.02:
        L.append("VERDICT: the sample's median REPRODUCES at population scale (within 0.02), so S-C46's median stands.")
    else:
        L.append("VERDICT: the sample's median DOES NOT reproduce - it is off by %.3f, which is the S-C42 failure"
                 % dmed)
        L.append("  mode again: a stride sample that flattered the figure. The population number should replace it.")

    (out / "population_analysis.txt").write_text("\n".join(L) + "\n")
    (out / "population_analysis.json").write_text(json.dumps({"population": pop, "sample": smp}, indent=1))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
