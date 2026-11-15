#!/usr/bin/env python3
"""Job 8 step 2: the tiny-clock sweep.

For each cell (Threads, Hash, clock) every one of the 200 mate-in-one positions gets one
fresh search: `ucinewgame`, `position fen`, then `go wtime <clock> btime 1000` with the
mover's clock set. Per cell we count
  (a) played a mating move,
  (b) played after a search (at least one `info depth` line),
  (c) played with NO search (no `info depth` line, or the last info says nodes 0),
  (d) no answer inside 2 s,
and record the median and largest `go`->`bestmove` time and how often it exceeded the clock.

`Move Overhead` is read from the engine's `uci` output and reported, not changed.

Usage: j8_sweep.py <positions.json> <out.json> <threads> <hash> <clock_ms> [inc_ms]
"""
import json
import queue
import statistics
import subprocess
import sys
import threading
import time

sys.path.insert(0, '/tmp/ds')
from j8engine import Engine  # noqa: E402

ENGINE = "/tmp/ds/build-release/forge"


def move_overhead_default():
    proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    out, _ = proc.communicate("uci\nquit\n", timeout=60)
    for line in out.splitlines():
        if line.startswith("option name Move Overhead"):
            return line
    return "not listed"


def main():
    positions_path, out_path = sys.argv[1], sys.argv[2]
    threads, hash_mb, clock = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    inc = int(sys.argv[6]) if len(sys.argv) > 6 else None
    positions = json.load(open(positions_path))

    e = Engine(threads=threads, hash_mb=hash_mb)
    tally = {"positions": len(positions), "mating": 0, "searched": 0, "no_search": 0,
             "no_answer_2s": 0}
    times = []
    over_clock = 0
    examples = {"no_search": [], "miss_after_search": []}
    for p in positions:
        # ucinewgame clears the table; at Hash 512 that alone takes ~35 ms, which is not
        # search time. Wait for it to finish before starting the clock on `go`.
        e.send("ucinewgame")
        e.send("isready")
        e.until("readyok", 120)
        if inc is None:
            limit = f"wtime {clock} btime 1000"
        else:
            limit = f"wtime {clock} btime 1000 winc {inc} binc {inc}"
        mv, infos, ms, timed_out = e.go(f"position fen {p['fen']}", limit, timeout=2.0)
        depth_lines = [l for l in infos if " depth " in l or l.startswith("info depth")]
        last_nodes = None
        for line in infos:
            if " nodes " in line:
                try:
                    last_nodes = int(line.split(" nodes ")[1].split()[0])
                except (IndexError, ValueError):
                    pass
        if timed_out:
            tally["no_answer_2s"] += 1
            continue
        times.append(ms)
        if ms > clock:
            over_clock += 1
        searched = bool(depth_lines) and (last_nodes is None or last_nodes > 0)
        if searched:
            tally["searched"] += 1
        else:
            tally["no_search"] += 1
            if len(examples["no_search"]) < 3:
                examples["no_search"].append({"fen": p["fen"], "move": mv,
                                              "ms": round(ms, 3),
                                              "info_lines": len(infos),
                                              "last_info": infos[-1] if infos else None})
        if mv in p["mating_moves"]:
            tally["mating"] += 1
        elif searched and len(examples["miss_after_search"]) < 3:
            examples["miss_after_search"].append({"fen": p["fen"], "move": mv,
                                                  "mating": p["mating_moves"],
                                                  "ms": round(ms, 3),
                                                  "last_info": infos[-1] if infos else None})
    e.close()
    out = {"threads": threads, "hash_mb": hash_mb, "clock_ms": clock, "inc_ms": inc,
           "move_overhead_option": move_overhead_default(),
           "tally": tally,
           "time_ms": {"median": round(statistics.median(times), 3) if times else None,
                       "max": round(max(times), 3) if times else None,
                       "count": len(times)},
           "answers_later_than_clock": over_clock,
           "examples": examples}
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}))


if __name__ == "__main__":
    main()
