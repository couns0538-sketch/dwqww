#!/usr/bin/env python3
"""Forge 6.4 isolated UCI repro; saves raw stdout/stderr. No dependencies."""
import pathlib, queue, re, subprocess, sys, threading, time
if len(sys.argv) != 2:
    sys.exit("Usage: python3 probe_qsearch_stalemate.py /path/to/forge")
exe = str(pathlib.Path(sys.argv[1]).resolve())
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
q = queue.Queue()
def reader():
    for line in p.stdout: q.put(line)
    q.put(None)
threading.Thread(target=reader, daemon=True).start()
cmds = [
    "uci", "setoption name OwnBook value false",
    "setoption name UseNNUE value false", "setoption name Threads value 1",
    "setoption name Clear Hash", "isready",
    "position fen 7k/5K2/8/6Q1/8/8/8/8 w - - 0 1",
    "go depth 1 searchmoves g5g6",
]
for command in cmds: p.stdin.write(command + "\n")
p.stdin.flush()
out = []
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    try: line = q.get(timeout=max(.01, deadline - time.monotonic()))
    except queue.Empty: break
    if line is None: break
    out.append(line)
    if line.startswith("bestmove "): break
p.stdin.write("quit\n")
p.stdin.flush()
try: p.wait(timeout=5)
except subprocess.TimeoutExpired:
    p.kill()
    p.wait(timeout=5)
while not q.empty():
    line = q.get_nowait()
    if line is not None: out.append(line)
output = "".join(out)
pathlib.Path("qsearch_horizon_stdout.txt").write_text(output)
pathlib.Path("qsearch_horizon_stderr.txt").write_text(p.stderr.read())
scores = [int(v) for v in re.findall(r"^info depth 1\\b[^\\n]*\\bscore cp (-?\\d+)", output, re.M)]
bests = re.findall(r"^bestmove (\\S+)", output, re.M)
print("scores_cp:",scores,"bestmoves:",bests,"exit:",p.returncode)
if not bests or bests[-1] != "g5g6": sys.exit("FAIL: forced legal root move not returned")
if not scores: sys.exit("INCONCLUSIVE: no depth-1 centipawn score")
if scores[-1] != 0: sys.exit("FAIL: forced stalemate scored nonzero")
print("PASS: stalemate horizon scored 0 cp")
