#!/usr/bin/env python3
"""Read raw harness transcripts and print the measurement table.

  python3 sum_raw.py honesty DIR PREFIX
  python3 sum_raw.py orun RAW_B RAW_OFF RAW_ON
"""
import sys


def info_nodes(line):
    if not line.startswith("info "):
        return None
    parts = line.split()
    if "nodes" not in parts:
        return None
    i = parts.index("nodes")
    if i + 1 >= len(parts) or not parts[i + 1].isdigit():
        return None
    return int(parts[i + 1])


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return [ln.rstrip("\n") for ln in f]


def parse_honesty(path, kind):
    nodes = None
    for line in read_lines(path):
        if kind == "bench" and line.startswith("info string bench depth "):
            nodes = info_nodes(line)
        elif kind == "perft" and line.startswith("nodes "):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                nodes = int(parts[1])
    if nodes is None:
        raise SystemExit(f"STOP: no nodes in {path}")
    return nodes


def parse_orun(path):
    rows = []
    segment = []
    for line in read_lines(path):
        if line.startswith(">> "):
            segment.append(line)
            continue
        segment.append(line)
        if line.startswith("bestmove "):
            nodes = None
            for prev in segment:
                got = info_nodes(prev)
                if got is not None:
                    nodes = got
            if nodes is None:
                raise SystemExit(f"STOP: bestmove without info nodes in {path} game-row {len(rows) + 1}")
            rows.append(nodes)
            segment = []
    return rows


def honesty_main(directory, prefix):
    jobs = [
        ("bench11", "bench", 312866),
        ("bench13", "bench", 862329),
        ("bench16", "bench", 3024920),
        ("perft5", "perft", 4865609),
    ]
    print(f"prefix {prefix}")
    miss = 0
    for tag, kind, expect in jobs:
        got = parse_honesty(f"{directory}/{prefix}_{tag}.txt", kind)
        flag = "ok" if got == expect else "MISS"
        if flag != "ok":
            miss += 1
        print(f"{tag} nodes {got} expect {expect} {flag}")
    print(f"honesty_miss {miss}")


def orun_main(raw_b, raw_off, raw_on):
    b = parse_orun(raw_b)
    off = parse_orun(raw_off)
    on = parse_orun(raw_on)
    print(f"positions B {len(b)} OFF {len(off)} ON {len(on)}")
    print(f"B sum {sum(b)} first3 {' / '.join(str(x) for x in b[:3])}")
    print(f"OFF sum {sum(off)} first3 {' / '.join(str(x) for x in off[:3])}")
    print(f"ON sum {sum(on)} first3 {' / '.join(str(x) for x in on[:3])}")
    if len(b) == len(off):
        differ_off = sum(1 for x, y in zip(b, off) if x != y)
        print(f"OFF positions differing from B {differ_off}")
    if len(b) == len(on):
        differ_on = sum(1 for x, y in zip(b, on) if x != y)
        print(f"ON positions differing from B {differ_on}")
    print(f"expect B sum 9500069 first3 41311 / 24872 / 28574")
    print(f"expect ON sum 10081213 first3 12481 / 31753 / 31668 differ 200")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "honesty":
        honesty_main(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "orun":
        orun_main(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
