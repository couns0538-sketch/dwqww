#!/usr/bin/env python3
"""E1.py -- establish the EOF trap rigorously, with raw output for each variant.

Variants (all startpos, all one process each):
  V1  all lines written at once, stdin CLOSED after the go      -> search aborted?
  V2  all lines written at once then stdin HELD OPEN 5 s        -> search completes?
  V3  interactive (one command at a time, read until reply)     -> search completes?
  V4  V3 but the go is `go movetime 300` (time-based)           -> completes?
  V5  V3 with `go depth 12` on a REAL G position (black to move) -> legal bestmove for black?
  V6  V3 on the same G position with `OwnBook false`            -> is the book the reason for speed?
Also: does the engine play a BOOK move by default (`OwnBook` default true)? The book is a separate
source of instantly-returned moves and would mask a broken harness.

Usage: E1.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_io

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)

G = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
res = {}


def save(tag, text):
    with open(os.path.join(OUT, tag + ".txt"), "w") as f:
        f.write(text)


# V1: stdin closed immediately after the go
t0 = time.monotonic()
p = subprocess.run([EXE], input="uci\nisready\nposition startpos\nisready\ngo depth 12\n",
                   capture_output=True, text=True, timeout=300)
t1 = time.monotonic()
res["V1_stdin_closed"] = {"elapsed_s": round(t1 - t0, 3),
                          "info_lines": sum(1 for l in p.stdout.splitlines() if l.startswith("info depth")),
                          "bestmove": [l for l in p.stdout.splitlines() if l.startswith("bestmove")],
                          "rc": p.returncode}
save("E1_V1_stdin_closed", p.stdout + "\n=== stderr\n" + p.stderr)

# V2: all lines, then hold stdin open 5 s
t0 = time.monotonic()
p = subprocess.run(["bash", "-c",
                    "printf 'uci\\nisready\\nposition startpos\\nisready\\ngo depth 12\\n'; sleep 5"],
                   capture_output=True, text=True, timeout=300)
# that pipes nothing into the engine; redo properly
pr = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE, text=True, bufsize=1)
pr.stdin.write("uci\nisready\nposition startpos\nisready\ngo depth 12\n")
pr.stdin.flush()
lines2 = []
t0 = time.monotonic()
import select
deadline = t0 + 60
while time.monotonic() < deadline:
    r, _, _ = select.select([pr.stdout], [], [], 0.5)
    if r:
        line = pr.stdout.readline()
        if not line:
            break
        lines2.append(line.rstrip())
        if line.startswith("bestmove"):
            break
t1 = time.monotonic()
res["V2_stdin_held_open"] = {"elapsed_s": round(t1 - t0, 3),
                             "info_lines": sum(1 for l in lines2 if l.startswith("info depth")),
                             "bestmove": [l for l in lines2 if l.startswith("bestmove")],
                             "last_info": [l for l in lines2 if l.startswith("info depth")][-1:]}
save("E1_V2_stdin_held_open", "\n".join(lines2))
pr.kill()

# V3 + V4 + V5 + V6: interactive helper
e = forge_io.Engine(EXE)
e.uci()
e.isready()
e.setoption("OwnBook", "false")
e.isready()
e.position("position startpos")
n3, b3, l3 = e.go("go depth 12")
res["V3_interactive_depth12"] = {"nodes": n3, "bestmove": b3,
                                 "info_lines": sum(1 for l in l3 if l.startswith("info depth"))}
save("E1_V3_interactive", "\n".join(l3))
n4, b4, l4 = e.go("go movetime 300")
res["V4_movetime300"] = {"nodes": n4, "bestmove": b4}
save("E1_V4_movetime", "\n".join(l4))
e.position("position fen " + G)
n5, b5, l5 = e.go("go depth 12")
res["V5_G_position_depth12"] = {"nodes": n5, "bestmove": b5, "fen": G,
                                "last_info": [l for l in l5 if l.startswith("info depth")][-1:]}
save("E1_V5_G_position", "\n".join(l5))
e.close()

# V6: is a book move being played by default?
e2 = forge_io.Engine(EXE)
e2.uci()
e2.isready()
e2.position("position startpos")
n6, b6, l6 = e2.go("go movetime 500")
res["V6_book_default_on"] = {"nodes": n6, "bestmove": b6,
                             "book_lines": [l for l in l6 if "book" in l]}
save("E1_V6_book_default", "\n".join(l6))
e2.close()

with open(os.path.join(OUT, "E1_summary.json"), "w") as f:
    json.dump(res, f, indent=2)
    f.write("\n")
print(json.dumps(res, indent=2))
