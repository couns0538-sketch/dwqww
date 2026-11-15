#!/usr/bin/env python3
"""Job 2 part C: `go` lines with a missing or bad value.

For each keyword and each fault the job lists, send one `go` line from the start
position, wait at most 5 s, then `stop`.  Record time to bestmove, nodes and
whether `stop` was needed.

The invariant: a line that carries a clock for the side to move must be answered
within that clock.  The clock here is 2000 ms; the pass bound is 2200 ms (the
engine charges its own Move Overhead, default 50 ms).  A line carrying no clock
at all has no clock bound and is recorded as such, not counted as a pass.
"""

import json
import subprocess
import sys
import time

ENGINE = sys.argv[1]
OUT = sys.argv[2]
WAIT = 5.0
BOUND_MS = 2200

KEYWORDS = ["wtime", "btime", "winc", "binc", "movestogo", "depth", "nodes", "mate", "movetime"]
FAULTS = [
    ("missing_at_end", "{kw}"),
    ("missing_before_keyword", "{kw} winc 100"),
    ("negative", "{kw} -500"),
    ("zero", "{kw} 0"),
    ("not_a_number", "{kw} abc"),
    ("huge", "{kw} 99999999999999999999"),
]
CLOCKED = {"wtime", "btime", "movetime"}
INCREMENTAL = {"winc", "binc"}


def one(line):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def read_until(tok, timeout):
        t0 = time.time()
        got = []
        while time.time() - t0 < timeout:
            ln = p.stdout.readline()
            if ln == "":
                return got, False
            got.append(ln.rstrip())
            if ln.startswith(tok):
                return got, True
        return got, False

    send("uci")
    read_until("uciok", 10)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    read_until("readyok", 10)
    send("position startpos")
    t0 = time.time()
    send(line)
    got, answered = read_until("bestmove", WAIT)
    elapsed = (time.time() - t0) * 1000.0
    needed_stop = False
    if not answered:
        send("stop")
        more, answered2 = read_until("bestmove", WAIT)
        got += more
        answered = answered2
        needed_stop = True
        elapsed = (time.time() - t0) * 1000.0
    lines += got
    nodes = None
    for ln in lines:
        if " nodes " in ln:
            try:
                nodes = int(ln.split(" nodes ")[1].split()[0])
            except Exception:
                pass
    send("quit")
    try:
        p.wait(timeout=5)
        exit_code = p.returncode
    except Exception:
        p.kill()
        exit_code = "killed"
    return {"answered": answered, "ms": round(elapsed), "nodes": nodes,
            "stop_needed": needed_stop, "exit": exit_code,
            "last_info": ([l for l in lines if l.startswith("info")][-1:] or []),
            "bestmove": ([l for l in lines if l.startswith("bestmove")][:1])}


def classify(r):
    if r["kind"] == "control":
        if r["line"] == "go infinite":
            return "ok (needs stop)" if r["stop_needed"] else "WRONG (ended by itself)"
        return "ok" if (not r["stop_needed"] and r["ms"] <= BOUND_MS) else "FAIL"
    kw = r["keyword"]
    clocked = kw in CLOCKED or (kw in INCREMENTAL and r["line"].startswith("go wtime"))
    if not clocked:
        return "no clock in line"
    return "ok" if (not r["stop_needed"] and r["ms"] <= BOUND_MS) else "FAIL"


def main():
    rows = []
    controls = [("CONTROL well-formed clock", "go wtime 2000 btime 2000"),
                ("CONTROL infinite", "go infinite"),
                ("CONTROL well-formed depth+clock", "go depth 8 wtime 2000 btime 2000")]
    for name, line in controls:
        r = one(line)
        rows.append({"kind": "control", "name": name, "line": line, **r})
        print(f"control {name}: {r['ms']} ms stop={r['stop_needed']} nodes={r['nodes']}", flush=True)

    for kw in KEYWORDS:
        for fname, template in FAULTS:
            line = "go " + template.format(kw=kw) + " wtime 2000 btime 2000"
            r = one(line)
            rows.append({"kind": "fault", "keyword": kw, "fault": fname, "line": line, **r})
            print(f"{kw:10s} {fname:22s} {r['ms']:6d} ms stop={r['stop_needed']} nodes={r['nodes']}",
                  flush=True)

    for r in rows:
        r["verdict"] = classify(r)
    json.dump({"bound_ms": BOUND_MS, "rows": rows}, open(OUT, "w"), indent=1)
    fails = [r for r in rows if r["verdict"] == "FAIL"]
    print(f"rows={len(rows)} fails={len(fails)}")
    for r in fails:
        print("  FAIL", r["line"], r["ms"], "ms stop=", r["stop_needed"], "nodes=", r["nodes"])


if __name__ == "__main__":
    main()
