#!/usr/bin/env python3
"""Read honesty transcripts and O-run raw files. Print the STEP 2 table."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECT_H = {
    "bench11": "312866",
    "bench13": "862329",
    "bench16": "3024920",
    "perft5": "4865609",
}


def honesty_nodes(text, key):
    lines = text.splitlines()
    if key == "perft5":
        for line in reversed(lines):
            if line.startswith("nodes "):
                return line.split()[1]
        return ""
    last = ""
    for line in lines:
        if " nodes " in line:
            last = line.split(" nodes ", 1)[1].split()[0]
    return last


def o_nodes(text):
    nodes = []
    last_info = ""
    for line in text.splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if " nodes " not in last_info:
                raise SystemExit(f"bestmove without nodes info: {last_info}")
            nodes.append(int(last_info.split(" nodes ", 1)[1].split()[0]))
            last_info = ""
    return nodes


def main():
    print("honesty")
    for tag in ("B", "P"):
        for key, expect in EXPECT_H.items():
            got = honesty_nodes((HERE / f"honesty_{tag}_{key}.txt").read_text(encoding="utf-8"), key)
            print(f"  {tag} {key} {got} expect {expect} {'OK' if got == expect else 'MISS'}")
    series = {name: o_nodes((HERE / f"o_{name}.raw").read_text(encoding="utf-8")) for name in ("B", "Poff", "Pon")}
    for name, rows in series.items():
        print(f"{name} n {len(rows)} sum {sum(rows)} first {' / '.join(str(n) for n in rows[:3])}")
    off_same = series["B"] == series["Poff"]
    differ = sum(1 for a, b in zip(series["B"], series["Pon"]) if a != b)
    print(f"off_identical {off_same}")
    print(f"on_differ {differ}")


if __name__ == "__main__":
    main()
