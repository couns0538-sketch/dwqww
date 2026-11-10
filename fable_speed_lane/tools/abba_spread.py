"""abba_spread.py - how much do the arms of one or more `spd_uci.py abba` runs scatter, and with what?

For each run folder: cycles per node of every arm (CPU cycles of the engine process over the timed bench
divided by its nodes), their spread per letter, the spread of the block ratios, and how many different
image load addresses were seen. Used to show the size of the per-file effect: byte-identical copies of one
exe, each run from its own new file, do not cost the same number of cycles.

usage: abba_spread.py RUN_DIR [RUN_DIR ...] [--arms]
"""
import argparse
import json
import os
import statistics


def pct(x):
    return f"{100 * x:+.2f} %"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dirs", nargs="+")
    p.add_argument("--arms", action="store_true", help="also list every arm")
    a = p.parse_args()
    for d in a.dirs:
        with open(os.path.join(d, "SAMPLES.json"), encoding="utf-8") as f:
            s = json.load(f)
        with open(os.path.join(d, "SUMMARY.json"), encoding="utf-8") as f:
            u = json.load(f)
        with open(os.path.join(d, "PROTOCOL.json"), encoding="utf-8") as f:
            c = json.load(f)
        cpn = [1e9 * x["cpu_s"] / x["nodes"] for x in s]
        med = statistics.median(cpn)
        rel = [x / med - 1 for x in cpn]
        bases = sorted({x.get("image_base", "?") for x in s})
        ratios = [r - 1 for r in u.get("cpu_block_ratios", [])]
        print(f"== {d}")
        print(f"   {c.get('timed')}, net/options {c.get('options')}, recopy: {c.get('recopy', 'none')}, "
              f"fixed base: {c.get('fixed_base', False)}")
        print(f"   {len(s)} arms, median {med:.0f} cycles/node; arm spread around the median: "
              f"sd {100 * statistics.pstdev(rel):.2f} %, min {pct(min(rel))}, max {pct(max(rel))}")
        if ratios:
            q = statistics.quantiles(ratios, n=4, method="inclusive") if len(ratios) >= 2 else [ratios[0]] * 3
            print(f"   {len(ratios)} block ratios (B against A, cycles): median {pct(statistics.median(ratios))}, "
                  f"mean {pct(statistics.mean(ratios))}, sd {100 * statistics.pstdev(ratios):.2f} %, "
                  f"IQR {pct(q[0])} .. {pct(q[2])}, min {pct(min(ratios))}, max {pct(max(ratios))}; "
                  f"standard error of the mean {100 * statistics.pstdev(ratios) / max(len(ratios), 1) ** 0.5:.2f} %")
        print(f"   distinct image load addresses: {len(bases)}" + (f" ({', '.join(bases[:6])}{' ...' if len(bases) > 6 else ''})"))
        if a.arms:
            for x, r in zip(s, rel):
                print(f"     block {x['block']:3d} {x['letter']} base {x.get('image_base', '?'):>14} "
                      f"{1e9 * x['cpu_s'] / x['nodes']:7.0f} cycles/node {pct(r)}")


if __name__ == "__main__":
    main()
