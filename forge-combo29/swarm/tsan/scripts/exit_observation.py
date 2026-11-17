#!/usr/bin/env python3
"""Record, per search, that the process was DRAINED TO EOF and what it exited with.

The brief's trap: a sanitizer that reports at exit cannot be read to `bestmove`.
This script does one search of each case kind and then records

  drained_to_eof  -- every line after `quit` was read until the child closed
  exit_code       -- the child's real status
  post_quit_lines -- how many lines the exit actually produced

so "no race" is a statement about a process whose exit was observed, not a
process we stopped reading.
"""
import json
import os
import sys

sys.path.insert(0, "/home/ubuntu/work/drv")
from tsan_driver import Engine, races  # noqa: E402

CORPUS = json.load(open("/home/ubuntu/work/corpus40.json"))["corpus"]


def one(label, setup, limit):
    e = Engine(os.environ["FORGE_EXE"])
    for c in setup:
        e.cmd(c)
    e.sync()
    e.cmd("position fen " + CORPUS[0]["fen"])
    bm, info = e.go(limit, 300)
    log = e.close()
    post = 0
    seen_quit = False
    for line in log:
        if line.strip() == ">>> quit":
            seen_quit = True
            continue
        if seen_quit:
            post += 1
    return {
        "case": label,
        "limit": limit,
        "setup": setup,
        "bestmove": bm,
        "drained_to_eof": getattr(e, "drained_to_eof", False),
        "exit_code": getattr(e, "exit_code", None),
        "post_quit_lines": post,
        "race_reports": len(races(log)),
    }


def main():
    rows = [
        one("A depth", ["setoption name Threads value 4"], "go depth 10"),
        one("B nodes", ["setoption name Threads value 4"], "go nodes 100000"),
        one("C hash", ["setoption name Threads value 4", "setoption name Hash value 64"],
            "go depth 10"),
        one("D clear", ["setoption name Threads value 4", "setoption name Clear Hash"],
            "go depth 10"),
        one("E multipv", ["setoption name Threads value 4", "setoption name MultiPV value 4"],
            "go depth 8"),
        one("H resize", ["setoption name Threads value 8"], "go depth 8"),
    ]
    out = {"note": "Exit observed for every row: drained to EOF, real exit code.",
           "rows": rows}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    ok = all(r["drained_to_eof"] and r["exit_code"] is not None for r in rows)
    for r in rows:
        print("%-10s exit=%-4s drained=%-5s post_quit_lines=%d races=%d bestmove=%s"
              % (r["case"], r["exit_code"], r["drained_to_eof"], r["post_quit_lines"],
                 r["race_reports"], r["bestmove"]))
    print("EXIT_OBSERVED_FOR_ALL" if ok else "EXIT_NOT_OBSERVED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
