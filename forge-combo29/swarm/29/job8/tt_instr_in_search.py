#!/usr/bin/env python3
"""Exact instruction count of the TT patch on a DEEP SEARCH rather than bench, where probe_body is 3.65-4.86 %
instead of 1.4-2.0 %. Instruction counts are deterministic, so this can resolve an effect that wall timing cannot.
Runs under callgrind; one process, one position, depth 12, cold.

Usage: tt_instr_in_search.py <forge> <fen> [depth]
"""
import subprocess, sys, re

exe, fen = sys.argv[1], sys.argv[2]
depth = sys.argv[3] if len(sys.argv) > 3 else "12"
cmds = ["uci", "setoption name Hash value 16", "setoption name Threads value 1",
        "setoption name OwnBook value false", "isready", f"position fen {fen}", f"go depth {depth}"]
# drive with a script so the search is DRAINED (19-F12) while under valgrind
script = "/tmp/_tt_instr_drive.py"
with open(script, "w") as f:
    f.write(
        "import subprocess\n"
        f"p=subprocess.Popen([{exe!r}],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,text=True,bufsize=1)\n"
        f"for c in {cmds[:-1]!r}:\n"
        "    p.stdin.write(c+'\\n'); p.stdin.flush()\n"
        "p.stdin.write(" + repr(cmds[-1] + "\n") + "); p.stdin.flush()\n"
        # read stdout to bestmove so the search completes
        "p.stdin.close() if False else None\n"
        "p.wait()\n")
# a drained version: read stdout, so use a pipe
with open(script, "w") as f:
    f.write(
        "import subprocess\n"
        f"p=subprocess.Popen([{exe!r}],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)\n"
        f"cmds={cmds!r}\n"
        "for c in cmds[:-1]:\n"
        "    p.stdin.write(c+'\\n'); p.stdin.flush()\n"
        "    if c=='isready':\n"
        "        for line in p.stdout:\n"
        "            if line.startswith('readyok'): break\n"
        "p.stdin.write(cmds[-1]+'\\n'); p.stdin.flush()\n"
        "for line in p.stdout:\n"
        "    if line.startswith('bestmove'): break\n"
        "p.stdin.write('quit\\n'); p.stdin.flush(); p.wait()\n")
out = f"/tmp/cg_search_{abs(hash((exe, fen, depth))) % 100000}.out"
subprocess.run(["valgrind", "--tool=callgrind", f"--callgrind-out-file={out}", "--cache-sim=no",
                sys.executable, script], capture_output=True)
rep = subprocess.run(["callgrind_annotate", out], capture_output=True, text=True).stdout
m = re.search(r"([0-9,]+) \(100\.0%\)\s+PROGRAM TOTALS", rep)
if not m:
    raise SystemExit("ABORT: callgrind produced no PROGRAM TOTALS -- refusing to report a number")
print(f"{exe}: {m.group(1)} instructions")
