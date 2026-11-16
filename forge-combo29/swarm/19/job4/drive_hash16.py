#!/usr/bin/env python3
"""drive_hash16.py EXE FENS OUTERR [HASH] : drive searches with Hash set explicitly, capture TT counters.

Exists to close the confound in REPORT_job4_tt.md: `bench` builds Searcher(16) with a 16 MB table, while my
earlier R_1911 driver left Hash at the UCI default (32 MB), so the two full-table rates were not measured
under the same table size. This driver sets Hash to a given value before the positions, so the comparison is
like-for-like.
"""
import subprocess
import sys

exe, fens, errpath = sys.argv[1], sys.argv[2], sys.argv[3]
hash_mb = sys.argv[4] if len(sys.argv) > 4 else "16"
depth, limit = 12, 200

positions = [l.strip() for l in open(fens) if l.strip()][:limit]
err = open(errpath, "w")
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=err, text=True, bufsize=1)


def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_to(pred):
    while True:
        line = proc.stdout.readline()
        if not line:
            return False
        if pred(line):
            return True


send("uci")
read_to(lambda l: l.startswith("uciok"))
for opt, val in (("Hash", hash_mb), ("OwnBook", "false")):
    send("setoption name %s value %s" % (opt, val))
    send("isready")
    read_to(lambda l: l.startswith("readyok"))

nodes_total = 0
zero = 0
for fen in positions:
    send("position fen " + fen)
    send("isready")
    read_to(lambda l: l.startswith("readyok"))
    send("go depth %d" % depth)
    best = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if " nodes " in line:
            try:
                best = max(best, int(line.split("nodes ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
        if line.startswith("bestmove"):
            break
    nodes_total += best
    if best == 0:
        zero += 1

send("quit")
proc.communicate(timeout=180)
err.close()
print("Hash %s MB | positions %d | total nodes %d | zero-node searches %d"
      % (hash_mb, len(positions), nodes_total, zero))
body = open(errpath).read().strip()
print(body.splitlines()[-1] if body else "(no counter line)")
