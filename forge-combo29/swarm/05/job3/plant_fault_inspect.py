#!/usr/bin/env python3
"""plant_fault.py -- writes a copy of the engine source with ONE planted fault behind input the runner controls,
so a sanitizer run can be PROVED able to report something (the brief's second proof for a sanitizer run).

Fault: on a special FEN (the position command containing the marker "planted-fault-check" -- actually we key on a
special move counter, because the FEN must stay a FEN), read one element past the end of a small heap array.
Concretely: in uci.cpp's position-fen handler, if the FEN's halfmove field equals 777, do a heap over-read.
Written as a unified diff so it is a TEXT PATCH, and the patched tree is built in /tmp only.
"""
import os
import sys

SRC = sys.argv[1]
DST = sys.argv[2]

# The fault goes into the loop over uci commands: when the raw `position fen ...` line ends with "777 1",
# we allocate 4 ints and read index 4 (one past the end) -- a heap-buffer-overflow ASan must catch.
target = os.path.join(SRC, "src", "uci.cpp")
text = open(target).read()

anchor = 'command.rfind("position", 0)'
print("looking for the position handler in", target)
lines = text.splitlines()
hit = None
for i, l in enumerate(lines):
    if "position" in l and ("rfind" in l or "starts_with" in l or "substr" in l):
        hit = i
        break
print("candidate line", hit, ":", lines[hit] if hit is not None else "(none)")
print()
print("first 40 lines mentioning position:")
for i, l in enumerate(lines):
    if "position" in l:
        print(f"  {i+1}: {l[:140]}")
