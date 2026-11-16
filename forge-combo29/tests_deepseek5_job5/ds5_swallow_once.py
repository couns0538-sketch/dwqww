#!/usr/bin/env python3
"""H4 planted fault: swallow the FIRST bestmove only."""
import os, subprocess, sys, threading
ENGINE = os.environ.get("DS5ENGINE", "/tmp/ds13_base/build/forge")
p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
def pump_in():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        p.stdin.write(line); p.stdin.flush()
threading.Thread(target=pump_in, daemon=True).start()
first = True
while True:
    line = p.stdout.readline()
    if not line:
        break
    if line.startswith("bestmove") and first:
        first = False
        continue
    sys.stdout.write(line); sys.stdout.flush()
