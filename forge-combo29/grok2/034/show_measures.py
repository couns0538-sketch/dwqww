#!/usr/bin/env python3
"""Print honesty and O tables from the raw engine logs. Numbers are not typed."""
import sys
from pathlib import Path


def lines_of(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def bench_nodes(path):
    for line in lines_of(path):
        if line.startswith("info string bench "):
            parts = line.split()
            return int(parts[parts.index("nodes") + 1])
    raise SystemExit(f"no bench line in {path}")


def perft_nodes(path):
    found = None
    for line in lines_of(path):
        if line.startswith("nodes "):
            found = int(line.split()[1])
    if found is None:
        raise SystemExit(f"no perft nodes in {path}")
    return found


def position_nodes(path):
    nodes = []
    current = None
    for line in lines_of(path):
        if line.startswith("info ") and "nodes" in line.split():
            parts = line.split()
            current = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if current is None:
                raise SystemExit(f"bestmove without info nodes in {path}")
            nodes.append(current)
            current = None
    return nodes


def honesty_block(folder, tag):
    folder = Path(folder)
    got = {
        "bench11": bench_nodes(folder / f"honesty_{tag}_bench11.txt"),
        "bench13": bench_nodes(folder / f"honesty_{tag}_bench13.txt"),
        "bench16": bench_nodes(folder / f"honesty_{tag}_bench16.txt"),
        "perft5": perft_nodes(folder / f"honesty_{tag}_perft5.txt"),
    }
    expect = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
    print(f"honesty {tag}")
    for key in ("bench11", "bench13", "bench16", "perft5"):
        mark = "ok" if got[key] == expect[key] else "MISS"
        print(f"  {key} {got[key]} expect {expect[key]} {mark}")
    return all(got[key] == expect[key] for key in expect)


def write_rows(folder, name, nodes):
    text = "".join(f"{i} {n}\n" for i, n in enumerate(nodes, 1))
    (Path(folder) / name).write_text(text, encoding="utf-8")


def summarize_o(folder):
    folder = Path(folder)
    b = position_nodes(folder / "o_b.txt")
    off = position_nodes(folder / "o_p_off.txt")
    on = position_nodes(folder / "o_p_on.txt")
    write_rows(folder, "o_b.rows", b)
    write_rows(folder, "o_p_off.rows", off)
    write_rows(folder, "o_p_on.rows", on)
    print(f"positions b {len(b)} off {len(off)} on {len(on)}")
    print(f"sum b {sum(b)} off {sum(off)} on {sum(on)}")
    print(f"first3 b {b[0]} {b[1]} {b[2]}")
    print(f"first3 off {off[0]} {off[1]} {off[2]}")
    print(f"first3 on {on[0]} {on[1]} {on[2]}")
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"off positions differ from b {differ_off}")
    print(f"on positions differ from b {differ_on}")
    expect_sum = 9500069
    expect_first = (41311, 24872, 28574)
    on_sum = 9718009
    on_first = (17283, 17878, 31115)
    print(f"b sum vs 9500069 {'ok' if sum(b) == expect_sum else 'MISS'}")
    print(f"b first3 vs 41311 24872 28574 {'ok' if tuple(b[:3]) == expect_first else 'MISS'}")
    print(f"off identical {'yes' if differ_off == 0 and len(off) == len(b) == 200 else 'no'}")
    print(f"on sum vs 9718009 {'ok' if sum(on) == on_sum else 'MISS'}")
    print(f"on first3 vs 17283 17878 31115 {'ok' if tuple(on[:3]) == on_first else 'MISS'}")
    print(f"on differ vs 200 {'ok' if differ_on == 200 else 'MISS'}")


def main():
    folder = sys.argv[1]
    honesty_block(folder, "b")
    honesty_block(folder, "p")
    summarize_o(folder)


if __name__ == "__main__":
    main()
