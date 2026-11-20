#!/usr/bin/env python3
"""Read harness raw files and print node sums and position-by-position diffs."""
import re
import sys

NODE = re.compile(r"\bnodes (\d+)")


def nodes_of(path):
    found = []
    last = None
    with open(path) as handle:
        for line in handle:
            match = NODE.search(line)
            if match and line.startswith("info "):
                last = int(match.group(1))
            if line.startswith("bestmove "):
                found.append(last)
                last = None
    return found


def main():
    if len(sys.argv) < 2:
        print("usage: summarize_depth.py label=raw.txt ...", file=sys.stderr)
        sys.exit(2)
    series = []
    for arg in sys.argv[1:]:
        label, path = arg.split("=", 1)
        rows = nodes_of(path)
        series.append((label, path, rows))
        blank = sum(1 for value in rows if value is None)
        total = sum(value or 0 for value in rows)
        print(f"{label} positions={len(rows)} missing={blank} sum={total} file={path}")
        if rows:
            head = " ".join(str(value) for value in rows[:3])
            print(f"{label} first3={head}")
    if len(series) >= 2:
        base_label, _, base_rows = series[0]
        for label, _, rows in series[1:]:
            if len(rows) != len(base_rows):
                print(f"diff {label} vs {base_label} length {len(rows)} != {len(base_rows)}")
                continue
            differ = 0
            for index, (left, right) in enumerate(zip(base_rows, rows)):
                if left != right:
                    differ += 1
                    if differ <= 5:
                        print(f"diff {label} index={index} {base_label}={left} {label}={right}")
            print(f"diff {label} vs {base_label} differ={differ} of {len(base_rows)}")


if __name__ == "__main__":
    main()
