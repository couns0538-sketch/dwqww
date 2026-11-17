#!/usr/bin/env python3
"""eval_microbench.py EXE NET — measure the v3 evaluation cost DIRECTLY, without -pg distortion.
Issues N `eval` commands in ONE process and times them, so we get a real per-call cost for the
forward pass, which can then be multiplied by the true call count to get an undistorted share."""
import subprocess, sys, time, re, os
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from pc20 import PC20
EXE, NET = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
opts = PC20 + [f"NNUEArchFile {NET}", "NNUEArch true"]
inp = ["uci"] + [f"setoption name {o.partition(' ')[0]} value {o.partition(' ')[2]}" for o in opts]
inp += ["position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        "isready", "eval"]
inp += ["eval"] * N
inp += ["quit"]
t0 = time.monotonic()
out = subprocess.run([EXE], input="\n".join(inp) + "\n",
                     capture_output=True, text=True, timeout=600).stdout
el = (time.monotonic() - t0) * 1000.0
evs = [l for l in out.splitlines() if "info string eval" in l]
per = el / max(1, len(evs))
print(f"  evals issued {N}, eval lines {len(evs)}, total {el:.1f} ms, per eval {per*1000:.2f} us")
print(f"  last line: {evs[-1] if evs else 'NONE'}")
