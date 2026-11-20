#!/usr/bin/env python3
"""Read raw harness output and print the honesty and O-run tables. Numbers come only from the files."""
import re
import sys
from pathlib import Path

BENCH_RE = re.compile(r"^info string bench depth (\d+) nodes (\d+) ")
PERFT_RE = re.compile(r"^nodes (\d+)$")
INFO_RE = re.compile(r"^info depth \d+ .* nodes (\d+) ")


def honesty(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    benches = [m.group(2) for line in text if (m := BENCH_RE.match(line))]
    perfts = [m.group(1) for line in text if (m := PERFT_RE.match(line))]
    if benches:
        return benches[-1]
    if perfts:
        return perfts[-1]
    return "MISSING"


def o_nodes(path):
    nodes = []
    last = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = INFO_RE.match(line)
        if m:
            last = int(m.group(1))
        elif line.startswith("bestmove "):
            nodes.append(last if last is not None else -1)
            last = None
    return nodes


def show_o(label, path):
    nodes = o_nodes(path)
    total = sum(n for n in nodes if n >= 0)
    head = nodes[:3]
    print(f"{label} positions {len(nodes)} sum {total} first {head[0] if head else 'NA'} {head[1] if len(head)>1 else 'NA'} {head[2] if len(head)>2 else 'NA'}")
    return nodes


def main():
    folder = Path(sys.argv[1])
    expected = {
        "bench11": "312866",
        "bench13": "862329",
        "bench16": "3024920",
        "perft5": "4865609",
    }
    print("honesty")
    for who in ("B", "P"):
        for tag, want in expected.items():
            got = honesty(folder / f"honesty_{who}_{tag}.txt")
            mark = "ok" if got == want else "MISS"
            print(f"  {who} {tag} nodes {got} expected {want} {mark}")
    b = show_o("O B   ", folder / "o_B.txt")
    off = show_o("O off", folder / "o_P_off.txt")
    on = show_o("O on ", folder / "o_P_on.txt")
    if len(b) == len(off) and len(b) > 0:
        differ_off = sum(1 for x, y in zip(b, off) if x != y)
        print(f"off_vs_B differ {differ_off} of {len(b)}")
    else:
        print(f"off_vs_B length B {len(b)} off {len(off)}")
    if len(b) == len(on) and len(b) > 0:
        differ_on = sum(1 for x, y in zip(b, on) if x != y)
        print(f"on_vs_B differ {differ_on} of {len(b)}")
    else:
        print(f"on_vs_B length B {len(b)} on {len(on)}")


if __name__ == "__main__":
    main()
