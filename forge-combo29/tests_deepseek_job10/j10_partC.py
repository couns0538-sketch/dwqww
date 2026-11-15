#!/usr/bin/env python3
"""Job 10 part C: a node limit with several threads (the reviewer's third case).

For `go nodes` 50/100/200/500/2000 and Threads 1/2/4/8 on the mate-in-2 positions:
  * how often the answer is the key move,
  * how often no `info depth` line was printed at all (answered without searching),
  * the largest total node count reported, against the limit asked for.

`nodes N` is a soft target in this engine (there is a separate `softnodes`), so the last
column is a measurement, not an expectation.
"""
import json
import queue
import re
import statistics
import subprocess
import sys
import threading

sys.path.insert(0, '/tmp/ds')
from j10engine import Engine  # noqa: E402


def main():
    positions = json.load(open(sys.argv[1]))["mate2"]
    out_path = sys.argv[2]
    rows = []
    for threads in (1, 2, 4, 8):
        e = Engine(threads=threads, hash_mb=16, multipv=1)
        for limit in (50, 100, 200, 500, 2000):
            key = 0
            no_info = 0
            max_nodes = 0
            for p in positions:
                e.send("ucinewgame")
                e.send(f"position fen {p['fen']}")
                e.send(f"go nodes {limit}")
                infos = []
                best = None
                while True:
                    line = e.get(30)
                    if line is None:
                        break
                    if line.startswith("info"):
                        infos.append(line)
                    elif line.startswith("bestmove"):
                        best = line.split()[1] if len(line.split()) > 1 else None
                        break
                if best == p["key"]:
                    key += 1
                if not any(" depth " in l for l in infos):
                    no_info += 1
                for l in infos:
                    m = re.search(r" nodes (\d+)", l)
                    if m:
                        max_nodes = max(max_nodes, int(m.group(1)))
            rows.append({"threads": threads, "nodes_limit": limit,
                         "positions": len(positions), "key_move": key,
                         "no_info_depth_line": no_info,
                         "max_nodes_reported": max_nodes})
            print(json.dumps(rows[-1]), flush=True)
        e.close()
    json.dump(rows, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
