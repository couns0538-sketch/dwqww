#!/usr/bin/env python3
"""label_stats.py - Opus R14-B item 2: descriptive statistics of a relabel2.py labels.tsv (own code, stdlib only).

usage: python -I -B label_stats.py LABELS.tsv [LABELS2.tsv ...]
Reads one or more labels.tsv files (a job's final/labels.tsv or its shards' labels.tsv) and prints: rows, search depth
and nodes, how far the new label is from the old self-play score (median / mean absolute difference, Pearson
correlation inside +-2000 cp, same sign), mate-range labels (|score| >= 30000), and how often the sign of each score
(White's view) matches the game result for decisive games. Descriptive only: no claim about training value.
"""

import math
import statistics
import sys

MATE = 30000


def main(paths) -> int:
    n = 0
    depth = {}
    nodes_sum = 0
    absdiff = []
    sx = sy = sxx = syy = sxy = 0.0
    m = 0
    same_sign = nonzero = 0
    mate_new = mate_old = 0
    agree = {"new": 0, "old": 0}
    decisive = 0
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            col = {name: i for i, name in enumerate(header)}
            for line in fh:
                f = line.rstrip("\n").split("\t")
                new, old = int(f[col["score_stm"]]), int(f[col["old_score_stm"]])
                d = int(f[col["depth"]])
                depth[d] = depth.get(d, 0) + 1
                nodes_sum += int(f[col["nodes"]])
                n += 1
                absdiff.append(abs(new - old))
                mate_new += abs(new) >= MATE
                mate_old += abs(old) >= MATE
                if abs(new) < 2000 and abs(old) < 2000:
                    m += 1
                    sx += new
                    sy += old
                    sxx += new * new
                    syy += old * old
                    sxy += new * old
                if new and old:
                    nonzero += 1
                    same_sign += (new > 0) == (old > 0)
                result = f[col["result"]]
                if result in ("0", "0.0", "1", "1.0"):  # decisive game: compare the sign in White's view
                    decisive += 1
                    white = f[col["fen"]].split()[1] == "w"
                    win = 1 if result in ("1", "1.0") else -1
                    for key, score in (("new", new), ("old", old)):
                        sw = score if white else -score
                        agree[key] += (sw > 0 and win > 0) or (sw < 0 and win < 0)
    if not n:
        print("no rows")
        return 1
    corr = (m * sxy - sx * sy) / math.sqrt((m * sxx - sx * sx) * (m * syy - sy * sy)) if m > 1 else float("nan")
    absdiff.sort()
    print(f"rows {n:,} from {len(paths)} file(s); mean nodes {nodes_sum / n:,.0f}")
    print("depth: " + " ".join(f"{d}:{100 * c / n:.1f}%" for d, c in sorted(depth.items())))
    print(f"|new - old| cp: median {statistics.median(absdiff):.0f}, mean {sum(absdiff) / n:.1f}, "
          f"p90 {absdiff[int(0.9 * (n - 1))]}, p99 {absdiff[int(0.99 * (n - 1))]}")
    print(f"Pearson r(new, old) on {m:,} rows with both |score| < 2000: {corr:.4f}; same sign {100 * same_sign / max(1, nonzero):.1f}% "
          f"of {nonzero:,} rows with both nonzero")
    print(f"mate-range (|score| >= {MATE}): new {mate_new:,}, old {mate_old:,}")
    if decisive:
        print(f"decisive-game rows {decisive:,}: score sign (White's view) = game result for new {100 * agree['new'] / decisive:.1f}%, "
              f"old {100 * agree['old'] / decisive:.1f}%")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
