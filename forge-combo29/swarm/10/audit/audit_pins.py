#!/usr/bin/env python3
"""audit_pins.py -- K6 and K7: the honesty pins under three option regimes and two builds.

K6: bench 11/13/16 + perft 5 with (a) DEFAULT options, (b) the S14 setoptions, (c) a second
    independent build of the same source (passed as argv 4).
K7: the same four pins on a portable x86-64-v3 build (argv 4), to test whether the ISA switches
    change the tree.

Usage: audit_pins.py EXE OUTDIR [SECOND_EXE]
"""
import hashlib
import os
import re
import subprocess
import sys

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)
SECOND = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

EXPECT = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}


def opts(kind):
    base = ["setoption name Threads value 1", "setoption name Hash value 16"]
    if kind == "s14":
        base += ["setoption name %s value %s" % kv for kv in S14]
    return base


def measure(exe, kind, tag):
    res = {}
    for name in ("bench11", "bench13", "bench16"):
        n = name[-2:]
        lines = ["uci", "isready"] + opts(kind) + ["isready", "ucinewgame", "isready",
                                                   "bench " + n]
        p = subprocess.run([exe], input="\n".join(lines) + "\nquit\n",
                           capture_output=True, text=True, timeout=1800)
        with open(os.path.join(OUT, "%s_%s.txt" % (tag, name)), "w") as f:
            f.write("=== exe %s (%s)\n" % (exe, kind))
            for l in lines:
                f.write("  " + l + "\n")
            f.write(p.stdout)
            f.write("=== stderr\n" + p.stderr)
        m = re.search(r"bench depth \d+ nodes (\d+)", p.stdout)
        res[name] = int(m.group(1)) if m else None
    lines = ["uci", "isready"] + opts(kind) + ["isready", "position startpos", "isready",
                                               "go perft 5"]
    p = subprocess.run([exe], input="\n".join(lines) + "\nquit\n",
                       capture_output=True, text=True, timeout=1800)
    with open(os.path.join(OUT, "%s_perft5.txt" % tag), "w") as f:
        f.write("=== exe %s (%s)\n" % (exe, kind))
        for l in lines:
            f.write("  " + l + "\n")
        f.write(p.stdout)
        f.write("=== stderr\n" + p.stderr)
    n = None
    for l in p.stdout.splitlines():
        if l.startswith("nodes "):
            n = int(l.split()[1])
    res["perft5"] = n
    return res


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


import json

out = {"exe": EXE, "sha256": sha(EXE),
       "second_exe": SECOND, "second_sha256": sha(SECOND) if SECOND else None}
out["default"] = measure(EXE, "default", "default")
out["s14"] = measure(EXE, "s14", "s14")
if SECOND:
    out["second_default"] = measure(SECOND, "default", "second_default")

out["K6a_all_pins_hold_on_defaults"] = all(out["default"][k] == v for k, v in EXPECT.items())
out["K6b_s14_differs_from_pins"] = any(out["s14"][k] != v for k, v in EXPECT.items())
out["K6c_two_builds_identical"] = (SECOND is not None and
                                   out.get("second_default") == out["default"])

with open(os.path.join(OUT, "pins.json"), "w") as f:
    json.dump(out, f, indent=2)
    f.write("\n")
print(json.dumps(out, indent=2))
