#!/usr/bin/env python3
"""Read raw honesty files and O-run transcripts. Prints only numbers taken from those files.

python3 otable.py honesty <prefix_files...>
python3 otable.py oruns <B.txt> <Poff.txt> <Pon.txt>
"""
import re
import sys


def honesty_nodes(path):
    bench = []
    perft = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("info string bench depth "):
            parts = line.split()
            bench.append(int(parts[parts.index("nodes") + 1]))
        elif line.startswith("nodes "):
            perft.append(int(line.split()[1]))
    if bench:
        return bench[-1]
    if perft:
        return perft[-1]
    raise SystemExit(f"no nodes line in {path}")


def search_nodes(path):
    nodes = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            match = re.search(r" nodes (\d+)", last_info or "")
            if not match:
                raise SystemExit(f"no nodes on last info before bestmove in {path}: {last_info}")
            nodes.append(int(match.group(1)))
            last_info = None
    return nodes


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: otable.py honesty <files...> | oruns <B> <off> <on>")
    mode = sys.argv[1]
    if mode == "honesty":
        for path in sys.argv[2:]:
            print(f"{path} {honesty_nodes(path)}")
        return
    if mode != "oruns":
        sys.exit("mode must be honesty or oruns")
    b_path, off_path, on_path = sys.argv[2:5]
    base = search_nodes(b_path)
    off = search_nodes(off_path)
    on = search_nodes(on_path)
    differ_off = sum(1 for a, b in zip(base, off) if a != b)
    differ_on = sum(1 for a, b in zip(base, on) if a != b)
    print(f"positions B {len(base)} off {len(off)} on {len(on)}")
    print(f"B sum {sum(base)} first {base[0]} {base[1]} {base[2]}")
    print(f"off sum {sum(off)} first {off[0]} {off[1]} {off[2]} differ {differ_off}")
    print(f"on sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ {differ_on}")
    if differ_off:
        print("off mismatches:")
        for i, (a, b) in enumerate(zip(base, off), start=1):
            if a != b:
                print(f"{i} B {a} off {b}")
    if len(base) != len(off) or len(base) != len(on):
        print("length mismatch")


if __name__ == "__main__":
    main()
