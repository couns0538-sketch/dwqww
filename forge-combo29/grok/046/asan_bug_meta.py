#!/usr/bin/env python3
"""Meta for the scratch sanitizer run. The runner aborts on the heap read, so measure_set.py does not reach its own meta write."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
meta = Path(sys.argv[2])
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
id_name = ""
for line in proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break
meta.write_text(
    f"exe={exe}\nsha256={digest}\nid_name={id_name}\n"
    "runner=measure_set.py\nswitch=on\ndepth=10\n"
    "fen_file=asan_bug.fen\n"
    "note=same runner as asan_G100_d10; engine aborted before bestmove\n"
    "options:\n"
    "setoption name Threads value 1\n"
    "setoption name Hash value 16\n"
    "setoption name LmrQuietBase value 93\n"
    "setoption name LmrQuietDivisor value 205\n"
    "setoption name LmrNoisyBase value 13\n"
    "setoption name LmrNoisyDivisor value 333\n"
    "setoption name LmrHistoryDivisor value 5643\n"
    "setoption name NullMoveBase value 5\n"
    "setoption name LmpBase value 8\n"
    "setoption name HistoryPruneMultiplier value 2220\n"
    "setoption name HistoryBonusQuadratic value 24\n"
    "setoption name HistoryBonusLinear value 54\n"
    "setoption name HistoryBonusMax value 2212\n"
    "setoption name SingularDepth value 6\n"
    "setoption name IirDepth value 2\n"
    "setoption name NonPawnCorrection value true\n"
    "setoption name IdeaK7 value true\n"
    "setoption name IdeaK7_Weight value 100\n"
)
print(id_name)
