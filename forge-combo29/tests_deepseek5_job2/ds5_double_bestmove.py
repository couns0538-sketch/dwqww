#!/usr/bin/env python3
"""Planted fault S4: forwards every bestmove line TWICE."""
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
while True:
    line = p.stdout.readline()
    if not line:
        break
    sys.stdout.write(line); sys.stdout.flush()
    if line.startswith("bestmove"):
        sys.stdout.write(line); sys.stdout.flush()
