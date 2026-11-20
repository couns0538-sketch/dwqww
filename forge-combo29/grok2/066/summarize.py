#!/usr/bin/env python3
"""summarize.py DIR

Reads the raw honesty and O-run files written by harness.py and prints the
tables. Numbers in REPORT.md are this script's stdout, pasted.
"""
import re
import sys
from pathlib import Path


EXPECTED_HONESTY = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
EXPECTED_ON = {
    "sum": 9547450,
    "first": (41442, 24989, 28711),
    "differ": 200,
}


def nodes_from_honesty(text, stem):
    lines = [line for line in text.splitlines() if line]
    if stem.startswith("bench"):
        hits = []
        for line in lines:
            match = re.search(r"bench depth (\d+) nodes (\d+)", line)
            if match:
                hits.append((int(match.group(1)), int(match.group(2))))
        if len(hits) != 1:
            return f"MISS lines={hits}"
        return hits[0][1]
    hits = [int(match.group(1)) for line in lines if (match := re.fullmatch(r"nodes (\d+)", line))]
    if len(hits) != 1:
        return f"MISS lines={hits}"
    return hits[0]


def position_nodes(text):
    blocks = []
    current = []
    for line in text.splitlines():
        current.append(line)
        if line.startswith("bestmove "):
            blocks.append(current)
            current = []
    nodes = []
    for block in blocks:
        infos = [line for line in block if line.startswith("info ")]
        if not infos:
            nodes.append(None)
            continue
        match = re.search(r" nodes (\d+)", infos[-1])
        nodes.append(int(match.group(1)) if match else None)
    return nodes


def main():
    folder = Path(sys.argv[1])
    print("honesty")
    for tag in ("B", "P"):
        for stem, expected in EXPECTED_HONESTY.items():
            path = folder / f"honesty_{tag}_{stem}.txt"
            got = nodes_from_honesty(path.read_text(encoding="utf-8"), stem) if path.exists() else "MISSING FILE"
            mark = "ok" if got == expected else "MISS"
            print(f"{tag} {stem} nodes {got} expected {expected} {mark}")
    print("orun")
    runs = {}
    for stem in ("o1_B", "o2_Poff", "o3_Pon"):
        path = folder / f"{stem}.txt"
        if not path.exists():
            print(f"{stem} MISSING FILE")
            runs[stem] = None
            continue
        nodes = position_nodes(path.read_text(encoding="utf-8"))
        missing = sum(1 for item in nodes if item is None)
        total = sum(item for item in nodes if item is not None)
        first = tuple(nodes[:3])
        print(f"{stem} positions {len(nodes)} missing {missing} sum {total} first {first[0] if len(first) > 0 else '-'} {first[1] if len(first) > 1 else '-'} {first[2] if len(first) > 2 else '-'}")
        runs[stem] = nodes
    base = runs.get("o1_B")
    off = runs.get("o2_Poff")
    on = runs.get("o3_Pon")
    if base and off and len(base) == len(off):
        differ = sum(1 for a, b in zip(base, off) if a != b)
        print(f"o2_vs_o1 differ {differ}")
    if base and on and len(base) == len(on):
        differ = sum(1 for a, b in zip(base, on) if a != b)
        print(f"o3_vs_o1 differ {differ}")
        if None not in on and len(on) >= 3:
            total = sum(on)
            first = (on[0], on[1], on[2])
            on_ok = total == EXPECTED_ON["sum"] and first == EXPECTED_ON["first"] and differ == EXPECTED_ON["differ"]
            print(f"o3 expected sum {EXPECTED_ON['sum']} first {EXPECTED_ON['first'][0]} {EXPECTED_ON['first'][1]} {EXPECTED_ON['first'][2]} differ {EXPECTED_ON['differ']}")
            print(f"o3_ok {str(on_ok).lower()}")


if __name__ == "__main__":
    main()
