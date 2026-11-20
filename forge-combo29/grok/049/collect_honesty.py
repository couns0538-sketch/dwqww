#!/usr/bin/env python3
"""Print the honesty node lines from the raw bench and perft transcripts."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
FILES = [
    ("bench 11", "honesty_b_bench11.txt", "312866"),
    ("bench 13", "honesty_b_bench13.txt", "862329"),
    ("bench 16", "honesty_b_bench16.txt", "3024920"),
    ("perft 5", "honesty_b_perft5.txt", "4865609"),
]


def node_line(path):
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(text):
        if "nodes " in line:
            return line
    return "MISSING"


def main():
    lines = []
    ok = True
    for label, name, expect in FILES:
        found = node_line(ROOT / name)
        got = ""
        parts = found.split()
        if "nodes" in parts:
            got = parts[parts.index("nodes") + 1]
        status = "ok" if got == expect else "MISMATCH"
        if status != "ok":
            ok = False
        lines.append(f"{label}\texpect {expect}\tgot {got}\t{status}\t{found}")
    report = ROOT / "HONESTY_B.txt"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.write(report.read_text(encoding="utf-8"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
