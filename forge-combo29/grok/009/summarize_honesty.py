#!/usr/bin/env python3
"""Read honesty raw files and print the node check. Does not run the engine."""
import sys
from pathlib import Path

EXPECTED = {
    "bench11": "312866",
    "bench13": "862329",
    "bench16": "3024920",
    "perft5": "4865609",
}

def nodes_of(text: str) -> str | None:
    last = None
    for line in text.splitlines():
        tokens = line.split()
        if "nodes" in tokens:
            last = tokens[tokens.index("nodes") + 1]
    return last

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_honesty.py OUTDIR TAG", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    tag = sys.argv[2]
    ok = True
    rows = []
    for name, expect in EXPECTED.items():
        raw = outdir / f"honesty_{tag}_{name}.txt"
        got = nodes_of(raw.read_text()) if raw.exists() else None
        status = "OK" if got == expect else "FAIL"
        if status != "OK":
            ok = False
        line = raw.read_text().strip().splitlines()[-1] if raw.exists() else "MISSING"
        rows.append(f"{name} expected {expect} got {got} {status} line {line}")
    rows.append(f"HONESTY_{tag} {'PASS' if ok else 'FAIL'}")
    sys.stdout.write("\n".join(rows) + "\n")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
