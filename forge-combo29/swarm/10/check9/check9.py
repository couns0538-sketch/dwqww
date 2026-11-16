#!/usr/bin/env python3
"""check9.py OUTDIR -- THIRD confirmation of the MultiPV x Hash collapse, on a DIFFERENT measure.

The first two confirmations measured DEPTH REACHED in a 5 s clock. This one measures NODES SEARCHED in a
fixed clock, which is an independent quantity, and adds a mechanism probe:

  P1/P2/P3  grid: Hash in {16,64,256,2048} x MultiPV in {1,2,5,8}, `go movetime 3000`, Threads 1, PC r15 PC20.
            Records nodes, depth, elapsed.
  P4        cost of ONE `setoption name Clear Hash` at each Hash size, timed separately (a fresh process,
            no search after it, measuring wall time of the isready round-trip that follows).

Threads 1 everywhere; fresh process per cell; read to `bestmove` (EOF-safe).

Usage: check9.py OUTDIR
"""
import json
import os
import subprocess
import sys
import time

PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(extra, go, tag, timeout=300):
    lines = ["uci", "isready", "setoption name Threads value 1"]
    if not any(k == "Hash" for k, _ in extra):
        lines.append("setoption name Hash value 16")
    lines += ["setoption name %s value %s" % kv for kv in PC20]
    lines += ["setoption name %s value %s" % kv for kv in extra]
    lines += ["isready", "ucinewgame", "isready", "position startpos", "isready", go]
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    t0 = time.monotonic()
    for l in lines:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        out.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    wall = time.monotonic() - t0
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    infos = [l for l in out if l.startswith("info depth")]
    last = infos[-1] if infos else ""
    nodes = depth = None
    if " nodes " in last:
        try:
            nodes = int(last.split(" nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    if last.startswith("info depth"):
        try:
            depth = int(last.split("depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    rec = {"tag": tag, "extra": extra, "go": go, "nodes": nodes, "depth": depth,
           "info_lines": len(infos), "wall_s": round(wall, 3)}
    with open(os.path.join(OUT, "check9_raw.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def clear_cost(h):
    """time a single Clear Hash at Hash=h: setup, then time the setoption+isready round trip"""
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in ["uci", "isready", "setoption name Threads value 1",
              "setoption name Hash value %d" % h] + \
             ["setoption name %s value %s" % kv for kv in PC20] + ["isready"]:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    # drain to the last readyok
    while True:
        line = p.stdout.readline()
        if line.strip() == "readyok":
            break
    t0 = time.monotonic()
    p.stdin.write("setoption name Clear Hash\n")
    p.stdin.flush()
    p.stdin.write("isready\n")
    p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if line.strip() == "readyok":
            break
    dt = time.monotonic() - t0
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return round(dt, 4)


grid = {}
for h in (16, 64, 256, 2048):
    for m in (1, 2, 5, 8):
        r = run([("Hash", str(h)), ("MultiPV", str(m))], "go movetime 3000",
                "H%d_M%d" % (h, m))
        grid["H%d_M%d" % (h, m)] = r
        print("H=%-5d M=%-2d nodes %-9s depth %-3s wall %.2fs"
              % (h, m, r["nodes"], r["depth"], r["wall_s"]), flush=True)

clears = {h: clear_cost(h) for h in (16, 64, 256, 2048)}
print("single Clear Hash cost:", clears)

out = {"grid": grid, "clear_hash_seconds": clears}
with open(os.path.join(OUT, "check9.json"), "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")


def ratio(a, b):
    if a and b and b > 0:
        return round(a / b, 1)
    return None


s = {
    "P1_nodes_H16_over_H2048_at_M8": ratio(grid["H16_M8"]["nodes"], grid["H2048_M8"]["nodes"]),
    "P2_nodes_H16_over_H2048_at_M1": ratio(grid["H16_M1"]["nodes"], grid["H2048_M1"]["nodes"]),
    "P3a_monotone_in_multipv_at_H2048": [grid["H2048_M%d" % m]["nodes"] for m in (1, 2, 5, 8)],
    "P3b_monotone_in_hash_at_M8": [grid["H%d_M8" % h]["nodes"] for h in (16, 64, 256, 2048)],
    "P4_clear_seconds": clears,
}
out["summary"] = s
with open(os.path.join(OUT, "check9.json"), "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")
print(json.dumps(s, indent=2))
