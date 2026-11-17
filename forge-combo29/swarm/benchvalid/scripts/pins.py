#!/usr/bin/env python3
"""Four honesty pins. bench N goes in on STDIN as a UCI command, never argv."""
import json, subprocess, sys, hashlib, os

from common import BUILD
EXE = sys.argv[1] if len(sys.argv) > 1 else str(BUILD)
EXPECT = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}

def run(cmds):
    p = subprocess.run([EXE], input="\n".join(cmds) + "\n", capture_output=True, text=True, timeout=1200)
    return p.stdout, p.stderr, p.returncode

def bench(d):
    out, err, rc = run(["uci", "isready", f"bench {d}", "quit"])
    nodes = None
    for line in out.splitlines():
        if line.startswith("info string bench"):
            f = line.split()
            nodes = int(f[f.index("nodes") + 1])
    return {"depth": d, "nodes": nodes, "rc": rc, "line": [l for l in out.splitlines() if "bench" in l]}

def perft(d):
    out, err, rc = run(["uci", "isready", "position startpos", f"go perft {d}", "quit"])
    n = None
    for line in out.splitlines():
        f = line.split()
        if len(f) == 2 and f[0] == "nodes" and f[1].isdigit():
            n = int(f[1])
    return {"depth": d, "nodes": n, "rc": rc}

res = {}
for d in (11, 13, 16):
    res[f"bench{d}"] = bench(d)
res["perft5"] = perft(5)
sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
res["binary_sha256"] = sha
res["exe"] = EXE
gates = {}
for k, v in EXPECT.items():
    got = res[k]["nodes"]
    gates[k] = {"expected": v, "got": got, "pass": got == v}
res["gates"] = gates
res["all_pass"] = all(g["pass"] for g in gates.values())
print(json.dumps(res, indent=2))
