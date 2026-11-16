#!/usr/bin/env python3
"""plant_threads_mate.py — seat 20 job 30: PLANTED, 10-repetition test of the S-F37 observation.

The observation: on 8/8/1p6/8/p3p3/8/2Kpk3/8 w at depth 12, Threads 1 gives `mate -7` (wrong; the true distance is 8
plies = mate -4) while Threads 2 and 4 give `mate -4`. If multithreading reliably makes the search MORE correct,
that is the most consequential thing found tonight; if the distance varies run to run at Threads 4 the way seat 04
and seat 28 found scores vary, then it is the same nondeterminism and nothing more.

RULES APPLIED HERE
  * Rule 1 (a zero needs a planted one): before the real arms, the SAME detector runs on a fake engine whose score
    is random per run and whose score is constant per run. The first must be flagged variable, the second stable,
    or the detector itself is not shown to work and the real result is not reported.
  * Threads are stated in every line (this job is explicitly about threading, which the swarm rule permits).
  * Fresh process per run.
  * Ten repetitions per arm, exactly as asked.

usage: plant_threads_mate.py <base-exe> <pc-exe> <outdir>
"""
import json
import os
import stat
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

BASE, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
REPS = 10

# ---------------- planted controls -----------------------------------------------------------------
FAKE_RANDOM = r'''#!/usr/bin/env python3
import sys, random
random.seed()
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-RANDOM", flush=True)
        print("option name Threads type spin default 1 min 1 max 256", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        v = random.choice([4, 7, 9, 12])
        n = random.randint(15000, 31000000)
        print(f"info depth 12 seldepth 20 score mate -{v} nodes {n} nps 1 hashfull 0 time 1 pv c2b1", flush=True)
        print("bestmove c2b1", flush=True)
'''

FAKE_STABLE = r'''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-STABLE", flush=True)
        print("option name Threads type spin default 1 min 1 max 256", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        print("info depth 12 seldepth 20 score mate -4 nodes 20000 nps 1 hashfull 0 time 1 pv c2b1", flush=True)
        print("bestmove c2b1", flush=True)
'''


def write_fake(name, body):
    p = os.path.join(OUT, name)
    open(p, "w").write(body)
    os.chmod(p, 0o755)
    return p


def arm(exe, threads, reps=REPS, opts_extra=()):
    """threads=None means 'send no Threads option at all'."""
    scores, moves, nodes, depths = [], [], [], []
    for _ in range(reps):
        opts = list(opts_extra)
        if threads is not None:
            opts = [("Threads", threads)] + opts
        e = Engine(exe, opts=opts)
        try:
            e.position(FEN)
            r = e.search("go depth 12", 400)
        finally:
            e.close()
        if r["hang"]:
            scores.append("HANG")
            moves.append(None)
            nodes.append(0)
            depths.append(None)
            continue
        scores.append(r["score"])
        moves.append(r["bestmove"])
        nodes.append(r["nodes"])
        d = None
        if r["last_info"]:
            import re
            m = re.search(r"depth (\d+)", r["last_info"])
            d = int(m.group(1)) if m else None
        depths.append(d)
    return {"scores": scores, "moves": moves, "nodes": nodes, "depths": depths,
            "distinct_scores": len({str(s) for s in scores}),
            "distinct_moves": len({str(m) for m in moves}),
            "distinct_nodes": len({n for n in nodes}),
            "nodes_min": min(nodes), "nodes_max": max(nodes)}


def show(label, a):
    print(f"  {label:34s} scores={a['scores']}")
    print(f"  {'':34s} moves={sorted(set(str(m) for m in a['moves']))}  "
          f"distinct scores={a['distinct_scores']} distinct nodes={a['distinct_nodes']} "
          f"nodes {a['nodes_min']}..{a['nodes_max']}")


results = {}

print("== PART 1: PLANTED CONTROLS — the detector must flag a random engine and pass a stable one")
planted_random = write_fake("planted_random.py", FAKE_RANDOM)
planted_stable = write_fake("planted_stable.py", FAKE_STABLE)
a_rand = arm(planted_random, 4)
a_stab = arm(planted_stable, 4)
show("PLANTED random-score engine", a_rand)
show("PLANTED stable-score engine", a_stab)
assert a_rand["distinct_scores"] > 1, "detector FAILED to see a planted random score — abort"
assert a_stab["distinct_scores"] == 1, "detector wrongly flagged a planted stable score — abort"
print("  -> detector shown able to fire and able to stay quiet. The real arms below count.")
print()
results["planted_random"] = a_rand
results["planted_stable"] = a_stab

print("== PART 2: the real engine, ten repetitions per arm, Threads stated")
print(f"  fen {FEN}   go depth 12   fresh process per run")
for name, exe in (("base", BASE), ("pc-r15", PC)):
    for t in (None, 1, 2, 4, 8):
        lab = "no Threads option" if t is None else f"Threads {t}"
        a = arm(exe, t)
        results[f"{name}_t{t}"] = a
        print(f"\n  [{name}] {lab}")
        show(lab, a)

with open(os.path.join(OUT, "plant_threads_mate.json"), "w") as f:
    json.dump({"fen": FEN, "reps": REPS, "arms": results}, f, indent=1)
print("\nwrote plant_threads_mate.json")
