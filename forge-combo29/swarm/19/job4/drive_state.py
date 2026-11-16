#!/usr/bin/env python3
"""drive_state.py EXE FENS OUTERR MODE : same sweep as the TT recipe, but with an explicit COLD-STATE discipline.

Modes:
  warm      one process, nothing between positions (what drive_hash16.py does — the published counters)
  newgame   one process, `ucinewgame` + `isready` before EVERY position (cold table each time)
  proc      one fresh PROCESS per position (coldest)

Seat 10's rule: a cold baseline is a fresh process or `ucinewgame`, never `Clear Hash`. This exists to say
which of those the published 54.7 % replacement-scan figure was measured under, and how much it moves.
"""
import subprocess
import sys

exe, fens, errpath, mode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
depth, limit, hash_mb = 12, 200, "16"
positions = [l.strip() for l in open(fens) if l.strip()][:limit]
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    import os
    os.environ.pop(v, None)


def start():
    return subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)


def send(p, line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def readto(p, pred):
    while True:
        line = p.stdout.readline()
        if not line:
            return False
        if pred(line):
            return True


def handshake(p):
    send(p, "uci")
    readto(p, lambda l: l.startswith("uciok"))
    for opt, val in (("Hash", hash_mb), ("OwnBook", "false")):
        send(p, "setoption name %s value %s" % (opt, val))
        send(p, "isready")
        readto(p, lambda l: l.startswith("readyok"))


err = open(errpath, "w")
total_nodes = 0
zero = 0
proc = None
if mode in ("warm", "newgame"):
    proc = start()
    handshake(proc)

for i, fen in enumerate(positions):
    if mode == "proc":
        p = start()
        handshake(p)
    else:
        p = proc
        if mode == "newgame":
            send(p, "ucinewgame")
            send(p, "isready")
            readto(p, lambda l: l.startswith("readyok"))
    send(p, "position fen " + fen)
    send(p, "isready")
    readto(p, lambda l: l.startswith("readyok"))
    send(p, "go depth %d" % depth)
    best = 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if " nodes " in line:
            try:
                best = max(best, int(line.split("nodes ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
        if line.startswith("bestmove"):
            break
    total_nodes += best
    if best == 0:
        zero += 1
    if mode == "proc":
        send(p, "quit")
        try:
            _, e = p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            e = ""
        err.write((e or "") + "\n")

if proc is not None:
    send(proc, "quit")
    try:
        _, e = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        e = ""
    err.write((e or "") + "\n")
err.close()

print("mode=%s  positions %d  total nodes %d  zero-node searches %d" % (mode, len(positions), total_nodes, zero))
lines = [l for l in open(errpath).read().splitlines() if l.startswith("TTPROBE")]
if mode == "proc":
    # 200 processes: sum the per-process counters
    import re
    tot = [0] * 13
    for l in lines:
        m = re.search(r"calls=(\d+) hit=(\d+) stale_gen=(\d+) full=(\d+) empty_none=(\d+) "
                      r"hit_slot=([\d/]+) empty_slot=([\d/]+)", l)
        if m:
            vals = [int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))]
            vals += [int(x) for x in m.group(6).split("/")] + [int(x) for x in m.group(7).split("/")]
            tot = [a + b for a, b in zip(tot, vals)]
    print("TTPROBE(summed over %d processes) calls=%d hit=%d stale_gen=%d full=%d empty_none=%d "
          "hit_slot=%s empty_slot=%s" % (len(lines), tot[0], tot[1], tot[2], tot[3], tot[4],
                                         "/".join(map(str, tot[5:9])), "/".join(map(str, tot[9:13]))))
else:
    print(lines[-1] if lines else "(no counter line)")
