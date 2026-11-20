#!/usr/bin/env python3
"""Compare my search_set transcript to a partner row file of 'index nodes fen'."""
import subprocess, sys
from pathlib import Path

def mine(path: Path) -> list[int]:
    script = Path(__file__).with_name("summarize_nodes.py")
    text = subprocess.check_output([sys.executable, str(script), str(path)], text=True)
    out = []
    for line in text.splitlines():
        if "\t" not in line:
            continue
        out.append(int(line.split("\t", 1)[1]))
    return out

def theirs(path: Path) -> list[int]:
    out = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            out.append(int(parts[1]))
    return out

def main() -> int:
    a = mine(Path(sys.argv[1]))
    b = theirs(Path(sys.argv[2]))
    n = min(len(a), len(b))
    differ = sum(x != y for x, y in zip(a[:n], b[:n]))
    print("mine_n", len(a), "mine_sum", sum(a))
    print("theirs_n", len(b), "theirs_sum", sum(b))
    print("compared", n, "differ", differ)
    if n and a[0] != b[0]:
        print("first_mine", a[0], "first_theirs", b[0])
    elif n:
        print("first_both", a[0])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
