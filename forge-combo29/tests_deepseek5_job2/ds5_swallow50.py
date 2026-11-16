#!/usr/bin/env python3
"""Planted fault S1: swallows every 50th bestmove line (does not forward it)."""
import subprocess, sys, threading
p = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
def pump_in():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        p.stdin.write(line); p.stdin.flush()
threading.Thread(target=pump_in, daemon=True).start()
count = 0
while True:
    line = p.stdout.readline()
    if not line:
        break
    if line.startswith("bestmove"):
        count += 1
        if count % 50 == 0:
            continue
    sys.stdout.write(line); sys.stdout.flush()
