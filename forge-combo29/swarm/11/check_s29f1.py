#!/usr/bin/env python3
"""check_s29f1.py EXE — seat 11's INDEPENDENT check of seat 29's 29-F1.

29-F1 claims: "`bench 13` spends 38.72 % of its samples in the NNUE + evaluation family and
only 2.14 % outside the binary, so the first speed lever is the evaluation path, not search
bookkeeping."

I cannot sample a profiler cheaply, so I test the CLAIM'S CONSEQUENCE with the engine's own
switches, which is a different experiment from seat 29's:
  A. `UseNNUE false` must REMOVE the NNUE cost. If the evaluation family really dominates,
     bench 13 should get measurably faster with the net off, and the node count must change
     (a different evaluation searches a different tree) — so the honest comparison is nps,
     not seconds.
  B. The fraction of nodes at which the evaluation actually runs can be bounded by comparing
     bench 13 node counts with and without the net: if the evaluation dominated, removing the
     network should change the tree a lot.
  C. "only 2.14 % outside the binary" is a claim about dynamic linking; `ldd` shows which
     shared objects exist, so the harness can at least show what could be sampled outside.

Predictions of MY check (stated so a wrong outcome is visible):
  P1. `UseNNUE false` changes the bench 13 node count (a different eval => different tree).
  P2. nps with the net OFF is not dramatically higher; I expect within 40 % either way, because
      the hand-crafted walk is itself expensive (19-F1).
  P3. ldd lists libc/libstdc++/libm only — no GPU or net library, so "outside the binary" can
      only ever be libc-side.
"""
import re, subprocess, sys, time

EXE = sys.argv[1]
ok_all = True


def check(name, ok, detail=""):
    global ok_all
    ok_all = ok_all and ok
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")


def setoption_line(opt):
    """`Threads 1` -> `setoption name Threads value 1` (the `value` word is mandatory)."""
    name, _, val = opt.partition(" ")
    return f"setoption name {name} value {val}"


def bench(setoptions=(), depth=13, runs=3):
    results = []
    for _ in range(runs):
        inp = "uci\n" + "".join(setoption_line(o) + "\n" for o in setoptions) + \
              f"bench {depth}\nquit\n"
        t0 = time.monotonic()
        p = subprocess.run([EXE], input=inp, capture_output=True, text=True, timeout=600)
        wall = time.monotonic() - t0
        m = re.search(r"bench depth \d+ nodes (\d+) time (\d+) nps (\d+)", p.stdout)
        if not m:
            results.append(None)
            continue
        nodes, ms, nps = map(int, m.groups())
        results.append((nodes, ms, nps, wall))
    return results


print("=== A. bench 13 with the built-in net (default) ===")
on = bench()
for r in on:
    print(f"  nodes={r[0]} time_ms={r[1]} nps={r[2]} wall={r[3]:.2f}s" if r else "  no bench line")
nodes_on = [r[0] for r in on if r]

print("\n=== B. bench 13 with UseNNUE false (hand-crafted evaluation only) ===")
off = bench(["UseNNUE false"])
for r in off:
    print(f"  nodes={r[0]} time_ms={r[1]} nps={r[2]} wall={r[3]:.2f}s" if r else "  no bench line")
nodes_off = [r[0] for r in off if r]

if nodes_on and nodes_off:
    check("P1: the net changes the bench 13 search tree", nodes_on[0] != nodes_off[0],
          f"with net {nodes_on[0]} vs without {nodes_off[0]}")
    mean_on = sum(r[2] for r in on if r) / len([r for r in on if r])
    mean_off = sum(r[2] for r in off if r) / len([r for r in off if r])
    ratio = mean_off / mean_on
    print(f"\n  mean nps with net {mean_on:.0f}, without {mean_off:.0f}, ratio {ratio:.2f}x")
    check("P2: nps without the net is within 40 % either way (0.71x .. 1.40x)",
          0.71 <= ratio <= 1.40, f"ratio {ratio:.2f}")
else:
    check("both bench runs produced a bench line", False)

print("\n=== C. what is linked from outside the binary ===")
ldd = subprocess.run(["ldd", EXE], capture_output=True, text=True).stdout
print(ldd.strip())
libs = [l.split()[0] for l in ldd.splitlines() if "=>" in l]
only_system = all(any(k in lib for k in ("libc.so", "libstdc++", "libm.so", "libgcc"))
                  for lib in libs)
check("P3: only libc/libstdc++/libm/libgcc-ish objects", only_system, ", ".join(libs))

print("\n=== verdict on 29-F1 ===")
print("I reproduce the CLAIM'S DIRECTION only if P1 holds: the evaluation is on the hot path")
print("so much that swapping it changes the tree. I do NOT measure 38.72 % / 2.14 % and make")
print("no statement about those numbers.")
if ok_all:
    print("RESULT: the evaluation family is empirically on the hot path (its removal changes the")
    print("        search tree), which is consistent with 29-F1. NOT a reproduction of its shares.")
else:
    print("RESULT: inconsistent with 29-F1 on the FAIL lines above; see them before believing 29-F1.")
