#!/usr/bin/env python3
"""matchpath.py : the PC's match path. `go nodes N` and the 6s+0.06 clock, fresh process per run.

Records, from the engine's own output: bestmove, the last reported nodes, every info depth/nodes pair, any
repeated depth number (a partial-depth line), and for the clock the wall time from `go` to `bestmove` on a
monotonic clock.

usage: matchpath.py EXE OPTFILE MODE OUT.json FENS [params...]
  MODE=go_nodes  params = N [N ...]
  MODE=clock     params = wtime winc     (run twice on the whole set so the spread can be seen)
"""
import hashlib
import json
import re
import subprocess
import sys
import time

EXE, OPTFILE, MODE, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
FENS = sys.argv[5]
PARAMS = [int(x) for x in sys.argv[6:]]

INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")


def start():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = [l.strip() for l in open(OPTFILE) if l.strip() and not l.startswith("#")]
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("died in uci")
        line = line.strip()
        if line.startswith("option name "):
            names.add(line.split("option name ")[1].split(" type ")[0])
        if line == "uciok":
            break
    for line in opts:
        name = line.split("name ")[1].split(" value ")[0]
        if name not in names:
            raise RuntimeError("STOP: %r not in the engine's uci list" % name)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while True:
            l2 = p.stdout.readline()
            if not l2:
                raise RuntimeError("died on option")
            if "unknown option" in l2 or "invalid value" in l2 or "ERROR" in l2:
                raise RuntimeError("STOP on %r" % l2.strip())
            if l2.strip() == "readyok":
                break
    return p, opts


def run_one(fen, gocmd):
    p, opts = start()
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    t0 = time.monotonic()
    p.stdin.write(gocmd + "\n"); p.stdin.flush()
    depths = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("died in search")
        line = line.strip()
        m = INFO.match(line)
        if m:
            depths.append([int(m.group(1)), int(m.group(2))])
        if line.startswith("bestmove"):
            wall = time.monotonic() - t0
            p.stdin.write("quit\n"); p.stdin.flush()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
            seen = {}
            partial = False
            for d, _ in depths:
                seen[d] = seen.get(d, 0) + 1
                if seen[d] > 1:
                    partial = True
            return {"fen": fen, "go": gocmd, "bestmove": line.split()[1],
                    "last_nodes": depths[-1][1] if depths else 0, "depths": depths,
                    "partial_depth_line": partial, "wall_ms": round(wall * 1000, 1)}


records = []
fens = [l.strip() for l in open(FENS) if l.strip()]
if MODE == "go_nodes":
    for n in PARAMS:
        for rep in range(5):
            for fen in fens:
                r = run_one(fen, "go nodes %d" % n)
                r["n"] = n
                r["rep"] = rep
                records.append(r)
elif MODE == "clock":
    wtime, winc = PARAMS[0], PARAMS[1]
    for phase in (1, 2):
        for fen in fens:
            r = run_one(fen, "go wtime %d btime %d winc %d binc %d" % (wtime, wtime, winc, winc))
            r["phase"] = phase
            records.append(r)
else:
    raise SystemExit("unknown MODE " + MODE)

meta = {"exe": EXE, "sha256": hashlib.sha256(open(EXE, "rb").read()).hexdigest(),
        "options": [l.strip() for l in open(OPTFILE) if l.strip()],
        "mode": MODE, "params": PARAMS, "fens": fens,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump({"meta": meta, "records": records}, open(OUT, "w"), indent=1)
print("wrote %d records to %s" % (len(records), OUT))
