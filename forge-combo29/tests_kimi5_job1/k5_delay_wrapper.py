#!/usr/bin/env python3
"""kimi5 job1 Control 2: transparent pipe that holds every bestmove back by 30 ms.
Planted fault: with it, the T=20 line must show an overshoot in nearly every search.
Usage: k5_delay_wrapper.py <engine> [engine args...]"""
import subprocess
import sys
import threading
import time

DELAY_S = 0.030

engine = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, bufsize=1)


def pump_stdin():
    for line in sys.stdin:
        engine.stdin.write(line)
        engine.stdin.flush()


threading.Thread(target=pump_stdin, daemon=True).start()
for line in engine.stdout:
    if line.startswith("bestmove"):
        time.sleep(DELAY_S)
    sys.stdout.write(line)
    sys.stdout.flush()
