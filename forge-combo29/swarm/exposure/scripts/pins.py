#!/usr/bin/env python3
"""Verify the four honesty pins on both builds.

Pins, from LOCK.md and the seat-12/27/63 record:
  bench 11 = 312,866   bench 13 = 862,329   bench 16 = 3,024,920
  go perft 5 from startpos = 4,865,609

`bench` on this engine is a UCI command that runs a fixed FEN corpus at a depth
and prints `info string bench depth D nodes N`; `go perft` prints a bare
`nodes N` line and NO `bestmove`, so it cannot be read like a search.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import os

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}


def run(path: str, script: str) -> str:
    proc = subprocess.run([path], input=script, capture_output=True, text=True, timeout=900)
    return proc.stdout + "\n" + proc.stderr


def bench(path: str, depth: int) -> int:
    out = run(path, f"uci\nisready\nbench {depth}\nquit\n")
    m = re.search(r"info string bench depth \d+ nodes (\d+)", out)
    if not m:
        raise RuntimeError(f"no bench line in output:\n{out[-2000:]}")
    return int(m.group(1))


def perft(path: str, depth: int) -> int:
    out = run(path, f"uci\nisready\nposition startpos\ngo perft {depth}\nquit\n")
    m = re.search(r"^nodes (\d+)$", out, re.M)
    if not m:
        raise RuntimeError(f"no perft nodes line in output:\n{out[-2000:]}")
    return int(m.group(1))


def main() -> int:
    builds = {"base": os.path.join(ROOT, "build-base", "forge"),
              "patched": os.path.join(ROOT, "build-patched", "forge")}
    result = {}
    ok = True
    for name, path in builds.items():
        got = {"bench11": bench(path, 11), "bench13": bench(path, 13),
               "bench16": bench(path, 16), "perft5": perft(path, 5)}
        agree = {k: (got[k] == EXPECTED[k]) for k in EXPECTED}
        result[name] = {"got": got, "agree": agree}
        if not all(agree.values()):
            ok = False
        print(f"{name}: " + "  ".join(f"{k}={got[k]}{'' if agree[k] else ' MISMATCH'}"
                                      for k in ("bench11", "bench13", "bench16", "perft5")))
    print("PINS " + ("PASS" if ok else "FAIL"))
    print(json.dumps({"expected": EXPECTED, "result": result}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
