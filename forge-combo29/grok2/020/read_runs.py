#!/usr/bin/env python3
"""Read raw harness files and print the tables for REPORT.md.

  python3 read_runs.py honesty <prefix>...
  python3 read_runs.py orun <label> <raw> [<base_raw>]
"""
import sys


def bench_nodes(path):
    last = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info string bench "):
            parts = line.split()
            last = int(parts[parts.index("nodes") + 1])
        elif line.startswith("nodes "):
            last = int(line.split()[1])
    return last


def cmd_honesty(prefixes):
    names = ("bench11", "bench13", "bench16", "perft5")
    expected = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
    print("file\tnodes\texpected\tmatch")
    for prefix in prefixes:
        for name in names:
            path = "%s_%s.txt" % (prefix, name)
            got = bench_nodes(path)
            exp = expected[name]
            print("%s\t%s\t%s\t%s" % (path, got, exp, "yes" if got == exp else "NO"))


def position_nodes(path):
    nodes = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in (" " + last_info + " "):
                nodes.append(None)
            else:
                parts = last_info.split()
                nodes.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    return nodes


def cmd_orun(label, raw, base):
    nodes = position_nodes(raw)
    print("%s positions %d" % (label, len(nodes)))
    if any(n is None for n in nodes):
        missing = [i + 1 for i, n in enumerate(nodes) if n is None]
        print("missing nodes at %s" % missing[:10])
        return
    print("sum %d" % sum(nodes))
    print("first %d %d %d" % (nodes[0], nodes[1], nodes[2]))
    if base:
        base_nodes = position_nodes(base)
        differ = sum(1 for a, b in zip(nodes, base_nodes) if a != b)
        print("differ_from_base %d of %d" % (differ, len(base_nodes)))
        if len(nodes) != len(base_nodes):
            print("length mismatch %d vs %d" % (len(nodes), len(base_nodes)))


def cmd_rows(raw, out):
    nodes = position_nodes(raw)
    with open(out, "w", encoding="utf-8") as f:
        for i, n in enumerate(nodes, 1):
            f.write("%d\t%s\n" % (i, n))
    print("rows %s %d" % (out, len(nodes)))


def main():
    if sys.argv[1] == "honesty":
        cmd_honesty(sys.argv[2:])
    elif sys.argv[1] == "orun":
        base = sys.argv[4] if len(sys.argv) > 4 else None
        cmd_orun(sys.argv[2], sys.argv[3], base)
    elif sys.argv[1] == "rows":
        cmd_rows(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
