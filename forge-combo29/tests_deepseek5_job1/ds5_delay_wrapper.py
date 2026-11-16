#!/usr/bin/env python3
"""Control 2 wrapper: forwards engine UCI traffic but holds every bestmove back by DELAY ms."""
import sys
import time

DELAY = 0.030  # seconds

eng = subprocess.Engine if False else None
import subprocess
p = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)

import threading

def pump_in():
    for line in sys.stdin:
        p.stdin.write(line)
        p.stdin.flush()

threading.Thread(target=pump_in, daemon=True).start()
for line in p.stdout:
    if line.startswith("bestmove"):
        time.sleep(DELAY)
    sys.stdout.write(line)
    sys.stdout.flush()
