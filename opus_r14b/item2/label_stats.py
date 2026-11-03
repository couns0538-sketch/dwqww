#!/usr/bin/env python3
"""label_stats.py - Opus R14-B item 2: descriptive statistics of a relabel2.py labels.tsv (own code, stdlib only).

usage: python -I -B label_stats.py LABELS.tsv [LABELS2.tsv ...]
Reads one or more labels.tsv files (a job's final/labels.tsv or its shards' labels.tsv) and prints: rows, search depth
and nodes, how far the new label is from the old self-play score (median / mean absolute difference, Pearson
correlation inside +-2000 cp, same sign), mate-range labels (|score| >= 30000), and how often the sign of each score
(White's view) matches the game result for decisive games. Descriptive only: no claim about training value.
Exit 0 = statistics printed; 1 = the files hold no rows; 2 = bad usage, or a file that is missing, not a labels.tsv
or has a damaged row (named with its line number; no statistics are printed then).
"""

import math
import statistics
import sys

MATE = 30000
NEEDED = ("fen", "score_stm", "old_score_stm", "result", "depth", "nodes")  # columns of relabel2's LABELS_HEADER used


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
        ln = 1
        try:  # a missing, wrong or damaged file used to end in a Python traceback (bug hunt #14)
            with open(path, "rb") as fh:  # bytes, decoded per line: a bad byte is reported with its line number
                header = fh.readline().decode("utf-8").rstrip("\r\n").split("\t")
                col = {name: i for i, name in enumerate(header)}
                missing = [c for c in NEEDED if c not in col]
                if missing:
                    print(f"{path}: not a relabel2 labels.tsv (no column {', '.join(missing)} in the first line)",
                          file=sys.stderr)
                    return 2
                for ln, raw in enumerate(fh, 2):
                    f = raw.decode("utf-8").rstrip("\r\n").split("\t")
                    new, old = int(f[col["score_stm"]]), int(f[col["old_score_stm"]])
                    d = int(f[col["depth"]])
                    nodes = int(f[col["nodes"]])
                    result, white = f[col["result"]], f[col["fen"]].split()[1] == "w"
                    depth[d] = depth.get(d, 0) + 1
                    nodes_sum += nodes
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
                    if result in ("0", "0.0", "1", "1.0"):  # decisive game: compare the sign in White's view
                        decisive += 1
                        win = 1 if result in ("1", "1.0") else -1
                        for key, score in (("new", new), ("old", old)):
                            sw = score if white else -score
                            agree[key] += (sw > 0 and win > 0) or (sw < 0 and win < 0)
        except OSError as e:
            print(f"{path}: cannot read: {e.strerror or e}", file=sys.stderr)
            return 2
        except UnicodeDecodeError as e:
            print(f"{path}:{ln}: not UTF-8 text: {e.reason}", file=sys.stderr)
            return 2
        except (ValueError, IndexError) as e:
            print(f"{path}:{ln}: damaged row ({type(e).__name__}: {e})", file=sys.stderr)
            return 2
    if not n:
        print(f"no rows in {', '.join(paths)}")
        return 1
    den = (m * sxx - sx * sx) * (m * syy - sy * sy)  # 0 when either score is constant (a ZeroDivisionError before hunt #14)
    corr = (m * sxy - sx * sy) / math.sqrt(den) if m > 1 and den > 0 else float("nan")
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
    if len(sys.argv) < 2 or any(a.startswith("-") for a in sys.argv[1:]):  # --help used to be read as a file name
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
