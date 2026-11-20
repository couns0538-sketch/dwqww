#!/usr/bin/env python3
"""Read raw O-run transcripts and print node rows. Numbers come only from the files."""
import sys


def nodes_of(path):
    rows = []
    pending = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.rstrip("\n")
            if text.startswith("bestmove "):
                info = [item for item in pending if item.startswith("info ")]
                if not info:
                    raise SystemExit(f"STOP: {path} bestmove with no info line")
                last = info[-1]
                parts = last.split()
                if "nodes" not in parts:
                    raise SystemExit(f"STOP: {path} last info has no nodes: {last}")
                rows.append(int(parts[parts.index("nodes") + 1]))
                pending = []
            else:
                pending.append(text)
    return rows


def show(path):
    rows = nodes_of(path)
    print(f"file {path}")
    print(f"count {len(rows)}")
    print(f"sum {sum(rows)}")
    first = " ".join(str(n) for n in rows[:3])
    print(f"first {first}")
    return rows


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: otable.py <raw> [<baseline-raw>]")
    rows = show(sys.argv[1])
    if len(sys.argv) > 2:
        base = nodes_of(sys.argv[2])
        if len(base) != len(rows):
            raise SystemExit(f"STOP: length {len(rows)} vs {len(base)}")
        differ = sum(1 for a, b in zip(rows, base) if a != b)
        print(f"compared {sys.argv[2]}")
        print(f"differ {differ} of {len(rows)}")
        print(f"equal {differ == 0}")
        for index, (got, expected) in enumerate(zip(rows, base), start=1):
            if got != expected:
                print(f"row {index} {got} baseline {expected}")


if __name__ == "__main__":
    main()
