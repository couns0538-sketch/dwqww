"""micro_table.py - opus2 SMP pack helper: markdown table from tt_microbench outputs (advisory numbers only).

Usage: python -I -B micro_table.py <label>=<file> [<label>=<file> ...]
Each file is one tt_microbench run. Per (hash, keys, threads) row and label: the X/L ratio of every run with that label,
reported as the median over its runs, with the run count and the A/L (legacy A/A) range of the same runs as the noise
reference. Labels with several files (e.g. old=a.txt old=b.txt) are pooled.
"""
import statistics
import sys
from collections import defaultdict


def parse(path):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split("|")
            if len(parts) < 4:
                continue
            head = parts[0].split()
            if len(head) != 3 or not head[0].isdigit():
                continue
            ratios = parts[2].split()
            rows[(int(head[0]), head[1], int(head[2]))] = (float(ratios[0]), float(ratios[1]))
    return rows


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = defaultdict(lambda: defaultdict(list))  # label -> key -> [(x_l, a_l)]
    labels = []
    for arg in argv[1:]:
        label, _, path = arg.partition("=")
        if not path:
            print(f"bad argument {arg!r}: expected label=file")
            return 2
        if label not in labels:
            labels.append(label)
        for key, value in parse(path).items():
            data[label][key].append(value)
    keys = sorted({k for label in labels for k in data[label]}, key=lambda k: (k[0], k[1], k[2]))
    header = "| hash MB | keys | T | " + " | ".join(f"X/L {lb} (runs)" for lb in labels) + " | A/L range (all runs) |"
    print(header)
    print("|" + "---|" * (4 + len(labels)))
    for key in keys:
        cells = []
        aas = []
        for lb in labels:
            vals = data[lb].get(key, [])
            if vals:
                cells.append(f"{statistics.median(v[0] for v in vals):.3f} ({len(vals)})")
                aas.extend(v[1] for v in vals)
            else:
                cells.append("-")
        rng = f"{min(aas):.3f}-{max(aas):.3f}" if aas else "-"
        print(f"| {key[0]} | {key[1]} | {key[2]} | " + " | ".join(cells) + f" | {rng} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
