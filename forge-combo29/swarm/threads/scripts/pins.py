#!/usr/bin/env python3
"""Honesty gate for forge-combo29 at base 6b98f217.

Four pins, DEFAULT options, Threads 1, fresh process per pin, raw output written
beside the result. Exits 0 only when all four match.

Usage: python3 pins.py <exe> <outdir>
Writes <outdir>/pin_bench{11,13,16}.raw.txt, <outdir>/pin_perft5.raw.txt,
       <outdir>/pin_summary.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine  # noqa: E402

PINS = [
    ("bench11", dict(kind="bench", arg="11"), 312866),
    ("bench13", dict(kind="bench", arg="13"), 862329),
    ("bench16", dict(kind="bench", arg="16"), 3024920),
    ("perft5", dict(kind="perft", arg="5"), 4865609),
]


def run_bench(exe, depth, raw_path):
    """bench prints one `info string bench depth N nodes X time T nps P` line."""
    e = Engine(exe, timeout=600.0)
    try:
        e.send(f"bench {depth}")
        lines = e.read_until(("info string bench",), 600.0)
    finally:
        e.close()
    with open(raw_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    for line in lines:
        if line.startswith("info string bench"):
            toks = line.split()
            for i, t in enumerate(toks):
                if t == "nodes":
                    return int(toks[i + 1]), line
    raise RuntimeError("bench line not found: " + repr(lines[-3:]))


def run_perft(exe, depth, raw_path):
    e = Engine(exe, timeout=900.0)
    try:
        e.position(None)
        e.send(f"go perft {depth}")
        lines = []
        # perft ends with a bare `nodes N` line (trap 5c: no bestmove).
        while True:
            got = e.read_until(("nodes ",), 900.0)
            lines += got
            if got[-1].startswith("nodes "):
                break
    finally:
        e.close()
    with open(raw_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    for line in reversed(lines):
        if line.startswith("nodes "):
            return int(line.split()[1]), line
    raise RuntimeError("perft nodes line not found")


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    results = {}
    ok = True
    for name, spec, expected in PINS:
        raw = os.path.join(outdir, f"pin_{name}.raw.txt")
        if spec["kind"] == "bench":
            got, line = run_bench(exe, spec["arg"], raw)
        else:
            got, line = run_perft(exe, spec["arg"], raw)
        match = got == expected
        ok = ok and match
        results[name] = {"expected": expected, "got": got, "match": match, "line": line}
        print(f"{'PASS' if match else 'FAIL'}  {name}: expected {expected}  got {got}   [{line}]")
    results["_exe"] = exe
    results["_exe_sha256"] = os.popen(f"sha256sum {exe}").read().split()[0]
    results["_all_match"] = ok
    with open(os.path.join(outdir, "pin_summary.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"GATE: {'PASS' if ok else 'FAIL'}   exe sha256 {results['_exe_sha256']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
