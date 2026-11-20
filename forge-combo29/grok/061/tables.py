#!/usr/bin/env python3
"""Read raw harness transcripts and print sums and comparisons. No hand-typed numbers."""

import argparse
import sys
from pathlib import Path


def searches(text):
    current = []
    blocks = []
    for line in text.splitlines():
        if line.startswith(">>> position fen ") or line.startswith("position fen "):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
            if line.startswith("bestmove "):
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    rows = []
    for block in blocks:
        fen = ""
        nodes = None
        score = ""
        best = ""
        for line in block:
            if line.startswith(">>> position fen "):
                fen = line[len(">>> position fen ") :]
            elif line.startswith("position fen "):
                fen = line[len("position fen ") :]
            if line.startswith("info depth ") and " nodes " in line:
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
                if "score" in parts:
                    score_at = parts.index("score")
                    score = " ".join(parts[score_at + 1 : score_at + 3]) if parts[score_at + 1] == "mate" else parts[score_at + 1]
            if line.startswith("bestmove "):
                best = line.split()[1]
        if fen:
            rows.append((fen, nodes, best, score))
    return rows


def honesty_nodes(text):
    found = []
    for line in text.splitlines():
        if line.startswith("info string bench "):
            parts = line.split()
            depth = parts[parts.index("depth") + 1]
            nodes = parts[parts.index("nodes") + 1]
            found.append(f"bench {depth} nodes {nodes}")
        elif line.startswith("nodes "):
            found.append("perft nodes " + line.split()[1])
    return found


def cmd_honesty(directory):
    order = ["honesty_bench11.txt", "honesty_bench13.txt", "honesty_bench16.txt", "honesty_perft5.txt"]
    for name in order:
        text = (Path(directory) / name).read_text(encoding="utf-8")
        parsed = honesty_nodes(text)
        if not parsed:
            print(f"{name} NO_NODES")
        for line in parsed:
            print(f"{name} {line}")


def cmd_sum(path):
    rows = searches(Path(path).read_text(encoding="utf-8"))
    total = 0
    missing = 0
    for index, (fen, nodes, best, score) in enumerate(rows, start=1):
        if nodes is None:
            missing += 1
            print(f"{index} MISSING {best} {fen}")
            continue
        total += nodes
        if index <= 3:
            print(f"{index} {nodes} {best} {score}")
    print(f"count {len(rows)}")
    print(f"missing {missing}")
    print(f"sum {total}")


def cmd_diff(left, right):
    a = searches(Path(left).read_text(encoding="utf-8"))
    b = searches(Path(right).read_text(encoding="utf-8"))
    n = min(len(a), len(b))
    differ = 0
    for index in range(n):
        if a[index][1] != b[index][1] or a[index][2] != b[index][2]:
            differ += 1
    print(f"left {len(a)}")
    print(f"right {len(b)}")
    print(f"compared {n}")
    print(f"differ {differ}")
    print(f"same {n - differ}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    honesty = sub.add_parser("honesty")
    honesty.add_argument("directory")
    total = sub.add_parser("sum")
    total.add_argument("transcript")
    diff = sub.add_parser("diff")
    diff.add_argument("left")
    diff.add_argument("right")
    args = parser.parse_args()
    if args.cmd == "honesty":
        cmd_honesty(args.directory)
    elif args.cmd == "sum":
        cmd_sum(args.transcript)
    else:
        cmd_diff(args.left, args.right)
    return 0


if __name__ == "__main__":
    sys.exit(main())
