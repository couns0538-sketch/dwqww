#!/usr/bin/env python3
"""Harness audit against seat 19's finding 19-F12 (fabricated bestmove when stdin closes / quit mid-search).

This does NOT re-test the engine (that is seat 19's finding, not mine).  It only answers: could any result I have
recorded so far come from a pipelined `position / go / quit` harness?

Checks:
  A  code audit of every runner I have used: does it read stdout until `bestmove` before sending the next command,
     and does it ever close stdin (or send quit) while a search is running?
  B  data audit: in every recorded result line, does the bestmove row carry real `info depth` lines with nodes > 0?
     Seat 19's artefact signature is `bestmove a2a3` with NO info lines and 0 nodes.
  C  a direct demonstration on my own build that the artefact exists at all, so the audit's signature is the right
     one: `printf 'go depth 12\\nquit\\n'` vs. the same search read to bestmove (this is a check of the report only).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)          # forge-combo29/swarm/24
EXE = "/agent/repos/base/forge-combo29/build-rel/forge"

print("=== A. code audit ===")
files = [os.path.join(SW, "job1", "driver.py"), os.path.join(SW, "job2", "churn.py"),
         os.path.join(SW, "job3", "infinite_stop.py"), os.path.join(HERE, "check_02f2.py")]
for f in files:
    src = open(f).read()
    reads_to_bestmove = "bestmove" in src and "read_until" in src
    sends_quit_inside = bool(re.search(r'go[^\n]*\n[^\n]*send\("quit"\)', src))
    print(f"{os.path.relpath(f, SW):40s} reads_until(bestmove)={reads_to_bestmove} "
          f"quit_inside_go_block={sends_quit_inside} "
          f"quit_only_in_close={src.count('send(\"quit\")') == 1}")

print()
print("=== B. data audit: recorded bestmoves that carry no real search ===")
bad = 0
checked = 0
for rel, sep, bmcol, infocol in [
    ("job1/t2.results", "|", 2, 5), ("job1/t4.results", "|", 2, 5),
    ("job1/t8.results", "|", 2, 5), ("job2/churn.steps", "|", 6, 9),
    ("job3/inf8.rounds", "|", 4, 7),
]:
    p = os.path.join(SW, rel)
    if not os.path.exists(p):
        print(f"{rel:22s} (not written yet)")
        continue
    n = 0
    a2a3_zero = 0
    for line in open(p):
        if line.startswith("#") or "|STOP" in line or "|CRASH" in line or "|HANG" in line or "|TIMEOUT" in line:
            continue
        parts = line.rstrip("\n").split(sep)
        if len(parts) <= infocol:
            continue
        n += 1
        info = parts[infocol]
        bm = parts[bmcol]
        if bm == "a2a3" and ("nodes 0 " in info or not info.strip()):
            a2a3_zero += 1
    print(f"{rel:22s} rows={n:5d} rows_shaped_like_the_artefact(a2a3+0 nodes or no info)={a2a3_zero}")
    bad += a2a3_zero
    checked += n
print(f"TOTAL rows checked {checked}, rows shaped like the artefact: {bad}")

print()
print("=== C. does the artefact exist on my build? (report check only, the finding is seat 19's) ===")
p1 = subprocess.run([EXE], input=b"position startpos\ngo depth 12\nquit\n", capture_output=True, timeout=120)
out1 = p1.stdout.decode(errors="replace")
bm1 = [l for l in out1.splitlines() if l.startswith("bestmove")]
inf1 = [l for l in out1.splitlines() if l.startswith("info depth")]
print(f"pipelined `go depth 12` + `quit`: bestmove lines={bm1} info depth lines={len(inf1)}")

p2 = subprocess.run(["bash", "-c",
                     f"{{ printf 'position startpos\\ngo depth 12\\n'; sleep 3; printf 'quit\\n'; }} | {EXE}"],
                    capture_output=True, timeout=180)
out2 = p2.stdout.decode(errors="replace")
bm2 = [l for l in out2.splitlines() if l.startswith("bestmove")]
inf2 = [l for l in out2.splitlines() if l.startswith("info depth")]
print(f"same search, quit 3 s later          : bestmove lines={bm2} info depth lines={len(inf2)}")
if inf2:
    print("last info line:", inf2[-1])
