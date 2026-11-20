#!/usr/bin/env python3
"""Compare a depth_run.py raw file with a partner row file of 'index nodes ...'. """
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("depth_sum", HERE / "depth_sum.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def mine(path: str) -> list[int]:
    text = open(path, encoding="utf-8").read().splitlines()
    out = []
    current = None
    last = None
    for line in text:
        if line.startswith("### position "):
            current = int(line.split()[2])
            last = None
            continue
        if line.startswith(">>> go "):
            last = None
            continue
        if line.startswith("<<< ") and current is not None:
            body = line[4:]
            found = mod.nodes_re.findall(body)
            if found and not body.startswith("bestmove"):
                last = int(found[-1])
            if body.startswith("bestmove ") and last is not None:
                out.append(last)
                current = None
                last = None
    return out


def theirs(path: str) -> list[int]:
    rows = []
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            rows.append(int(parts[1]))
    return rows


def main() -> None:
    a = mine(sys.argv[1])
    b = theirs(sys.argv[2])
    n = min(len(a), len(b))
    differ = [i + 1 for i in range(n) if a[i] != b[i]]
    print(f"mine {sys.argv[1]}")
    print(f"theirs {sys.argv[2]}")
    print(f"mine_positions {len(a)}")
    print(f"their_positions {len(b)}")
    print(f"compared {n}")
    print(f"mine_sum {sum(a)}")
    print(f"their_sum {sum(b[:n])}")
    print(f"equal {n - len(differ)}")
    print(f"differ {len(differ)}")


if __name__ == "__main__":
    main()
