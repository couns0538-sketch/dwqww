#!/usr/bin/env python3
"""Read O-run transcripts and print one row per position plus the summary."""
import sys


def rows(path):
    nodes = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith(">>"):
            continue
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in last_info:
                sys.exit(f"STOP: no nodes on last info before bestmove in {path}: {last_info}")
            parts = last_info.split()
            n = int(parts[parts.index("nodes") + 1])
            nodes.append(n)
            last_info = None
    return nodes


def show(label, path):
    ns = rows(path)
    print(f"# {label} {path} count {len(ns)} sum {sum(ns)}")
    for i, n in enumerate(ns, 1):
        print(f"{i} {n}")
    return ns


def main():
    labels = sys.argv[1:]
    # pairs: label path label path ...
    if len(labels) % 2 != 0:
        sys.exit("usage: o_table.py LABEL PATH [LABEL PATH ...]")
    parsed = []
    for i in range(0, len(labels), 2):
        parsed.append((labels[i], show(labels[i], labels[i + 1])))
    base = parsed[0][1]
    print(f"SUMMARY {parsed[0][0]} sum {sum(base)} first {base[0]} {base[1]} {base[2]}")
    for label, ns in parsed[1:]:
        differ = sum(1 for a, b in zip(base, ns) if a != b)
        print(f"SUMMARY {label} sum {sum(ns)} first {ns[0]} {ns[1]} {ns[2]} differ {differ}")


if __name__ == "__main__":
    main()
