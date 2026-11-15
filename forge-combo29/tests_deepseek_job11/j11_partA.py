#!/usr/bin/env python3
"""Job 11 step 3 (job 10 part A): stopped in mid-iteration.

For MultiPV in {1,2,4} and Threads in {1,2}: start `go infinite`, read the output until
line 1 shows a mate score for a COMPLETED depth (the engine knows the answer), then send
`stop` after a delay of 0, 1, 2, 5, 10 or 20 ms. Count per cell:
  * answer in the position's answer SET,
  * answer outside the set (record position, delay, last 12 lines for the first three),
  * answer later than 50 ms after `stop`,
  * an info line whose score and first move belong to different MultiPV lines.

Usage: j11_partA.py <positions.json> <out.json> [engine]
"""
import json
import re
import sys
import time

sys.path.insert(0, '/tmp/ds')
from j10engine import Engine  # noqa: E402

DELAYS = [0, 1, 2, 5, 10, 20]


def first_ply(line):
    m = re.search(r'\bpv (\S+)', line)
    return m.group(1) if m else None


def main():
    positions = json.load(open(sys.argv[1]))
    out_path = sys.argv[2]
    engine = sys.argv[3] if len(sys.argv) > 3 else None
    rows = []
    for multipv in (1, 2, 4):
        for threads in (1, 2):
            e = Engine(threads=threads, hash_mb=16, multipv=multipv,
                       engine=engine) if engine else Engine(threads=threads, hash_mb=16,
                                                            multipv=multipv)
            for delay in DELAYS:
                in_set = out_set = late = mismatched = 0
                examples = []
                done = 0
                for p in positions:
                    e.send("ucinewgame")
                    e.send(f"position fen {p['fen']}")
                    e.send("go depth 14")
                    # read until line 1 carries a mate score on a completed depth
                    saw_mate = False
                    guard = time.monotonic() + 20
                    while time.monotonic() < guard:
                        line = e.get(5)
                        if line is None:
                            break
                        if line.startswith("bestmove"):
                            break
                        # With MultiPV 1 the engine omits the multipv field entirely, so
                        # accept either form; for MultiPV > 1 only the first line counts.
                        is_line1 = (" multipv 1 " in line) if multipv > 1 else (" multipv " not in line)
                        if is_line1 and " score mate " in line:
                            saw_mate = True
                            break
                    if not saw_mate:
                        e.until("bestmove", 30)
                        continue
                    time.sleep(delay / 1000.0)
                    t_stop = time.monotonic()
                    e.send("stop")
                    tail = []
                    best = None
                    while True:
                        line = e.get(max(0.01, 20 - (time.monotonic() - t_stop)))
                        if line is None:
                            break
                        tail.append(line)
                        if line.startswith("bestmove"):
                            best = line.split()[1] if len(line.split()) > 1 else None
                            break
                    elapsed = (time.monotonic() - t_stop) * 1000.0
                    done += 1
                    if elapsed > 50:
                        late += 1
                    if best in p["answers"]:
                        in_set += 1
                    else:
                        out_set += 1
                        if len(examples) < 3:
                            examples.append({"fen": p["fen"], "delay_ms": delay,
                                             "bestmove": best,
                                             "answers": p["answers"],
                                             "last": tail[-12:]})
                    # mismatched: a pv first move repeated at two depths with different scores
                    depths = {}
                    for l in tail:
                        m = re.search(r' depth (\d+) .* score (\S+ \S+) .* pv (\S+)', l)
                        if m:
                            depths.setdefault(int(m.group(1)), []).append((m.group(2),
                                                                           m.group(3)))
                    for d, entries in depths.items():
                        if len({mv for _, mv in entries}) > 1:
                            mismatched += 1
                            break
                rows.append({"multipv": multipv, "threads": threads, "delay_ms": delay,
                             "positions_run": done, "in_answer_set": in_set,
                             "outside_set": out_set, "later_than_50ms": late,
                             "info_lines_inconsistent": mismatched,
                             "examples": examples})
                print(json.dumps({k: v for k, v in rows[-1].items() if k != "examples"}),
                      flush=True)
            e.close()
    json.dump(rows, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
