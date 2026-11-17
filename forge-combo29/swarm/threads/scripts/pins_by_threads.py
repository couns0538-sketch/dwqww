#!/usr/bin/env python3
"""The four honesty pins at Threads 1/2/4/8, reported separately from the Threads-1 gate.

Two DIFFERENT questions, and the output keeps them apart:
  Q1 reproducibility -- is the number the same on every repeat AT THIS thread count?
  Q2 pin identity    -- does it equal the documented Threads-1 value (312866 etc.)?

For `go depth N` and `go nodes N` the node field is a SUM over workers
(search.cpp:2696-2705), so Q2 is expected to fail at Threads > 1 and that is
arithmetic, not a broken pin. For `bench` the searcher is built as Searcher(16)
(uci.cpp:611), whose thread argument defaults to 1, so Q2 is expected to HOLD at
every thread count -- bench does not consult the Threads option at all.

perft is single-threaded in the UCI loop (uci.cpp perft branch runs on this thread
only), so its count must be identical everywhere.

Usage: python3 pins_by_threads.py <exe> <out.json> [reps]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

DOC = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
THREADS = (1, 2, 4, 8)


def bench(exe, threads, depth):
    e = Engine(exe, {"Threads": threads}, timeout=900.0)
    try:
        e.send(f"bench {depth}")
        line = e.read_until(("info string bench",), 900.0)[-1]
    finally:
        e.close()
    toks = line.split()
    return int(toks[toks.index("nodes") + 1]), line


def perft(exe, threads, depth):
    e = Engine(exe, {"Threads": threads}, timeout=1800.0)
    try:
        e.position(None)
        e.send(f"go perft {depth}")
        lines = []
        while True:
            got = e.read_until(("nodes ",), 1800.0)
            lines += got
            if got[-1].startswith("nodes "):
                break
    finally:
        e.close()
    for line in reversed(lines):
        if line.startswith("nodes "):
            return int(line.split()[1]), line
    raise RuntimeError("no nodes line")


def main():
    exe = os.path.abspath(sys.argv[1])
    out_path = sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    rows = []
    for threads in THREADS:
        for name, fn, arg in (("bench11", bench, 11), ("bench13", bench, 13),
                              ("bench16", bench, 16), ("perft5", perft, 5)):
            vals = []
            line = ""
            for _ in range(reps):
                v, line = fn(exe, threads, arg)
                vals.append(v)
            reproducible = len(set(vals)) == 1
            equals_pin = vals[0] == DOC[name]
            rows.append({"threads": threads, "pin": name, "values": vals,
                         "documented": DOC[name], "reproducible": reproducible,
                         "equals_documented": equals_pin, "line": line})
            print(f"Threads {threads:>2}  {name:<8} values={vals} documented={DOC[name]} "
                  f"reproducible={'YES' if reproducible else 'NO '} "
                  f"equals_pin={'YES' if equals_pin else 'NO '}", flush=True)
        print(flush=True)
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
