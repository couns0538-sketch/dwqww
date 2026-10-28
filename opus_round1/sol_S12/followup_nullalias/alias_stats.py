#!/usr/bin/env python3
"""Run `bench <d>` on a FORGE_NNUE_LAZY_ACC=1 build with NnueLazyAcc=true and sum the per-search
"info string NnueLazyAcc stats ..." lines (refreshes, updates, zero_dirty_edges, copies_avoided, alias_hits,
evaluations). Also checks the bench node count against the AL1 pins.
usage: alias_stats.py <forge_exe> [depth ...]   (default depths 13 16 20)"""
import re
import subprocess
import sys

REF_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
FIELDS = ("refreshes", "updates", "zero_dirty_edges", "copies_avoided", "alias_hits", "evaluations")

exe = sys.argv[1]
depths = [int(d) for d in sys.argv[2:]] or [13, 16, 20]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def wait(pat, on_line=None):
    rx = re.compile(pat)
    for line in p.stdout:
        if on_line is not None:
            on_line(line)
        m = rx.search(line)
        if m:
            return m
    raise SystemExit("engine exited before matching " + pat)


send("uci")
wait(r"^uciok")
for o in ("Threads value 1", "Hash value 16", "OwnBook value false", "NnueLazyAcc value true"):
    send("setoption name " + o)
send("isready")
wait(r"^readyok")
ok = True
active = []
for d in depths:
    totals = dict.fromkeys(FIELDS, 0)
    searches = [0]

    def collect(line):
        if line.startswith("info string NnueLazyAcc active"):
            active.append(line.strip())
        if line.startswith("info string NnueLazyAcc stats"):
            searches[0] += 1
            for k, v in re.findall(r"(\w+) (\d+)", line[len("info string NnueLazyAcc stats"):]):
                totals[k] += int(v)

    send(f"bench {d}")
    m = wait(rf"bench depth {d} nodes (\d+)", collect)
    nodes = int(m.group(1))
    good = nodes == REF_BENCH.get(d)
    ok &= good
    ev = totals["evaluations"] or 1
    print(f"bench d{d} nodes {nodes} ref {REF_BENCH.get(d)} {'OK' if good else 'FAIL'}; searches {searches[0]}; "
          + " ".join(f"{k} {totals[k]}" for k in FIELDS)
          + f"; alias_hits/evaluations {totals['alias_hits'] / ev:.4%}; zero_dirty_edges/evaluations "
          f"{totals['zero_dirty_edges'] / ev:.4%}", flush=True)
    # copies_avoided counts null edges that borrowed the parent's accumulator instead of copying it (the saving);
    # alias_hits counts evaluations at a null child itself, which are rare and may be 0 at low depth.
    if totals["copies_avoided"] == 0 or totals["copies_avoided"] != totals["zero_dirty_edges"]:
        ok = False
        print(f"  no alias activity at d{d}", flush=True)
send("quit")
p.wait(timeout=30)
print("active line: " + (active[0] if active else "MISSING"))
ok &= bool(active)
print("ALIAS ACTIVE, NODES OK" if ok else "CHECK FAILED")
sys.exit(0 if ok else 1)
