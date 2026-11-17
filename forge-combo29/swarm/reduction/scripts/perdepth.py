#!/usr/bin/env python3
"""perdepth.py EXE FEN --depth N [--json OUT]

Dump the reduction counters of EVERY completed depth iteration, so a per-depth
profile can be compared between builds rather than only the final totals.

Why this exists: the totals in loneking11.py are dominated by the largest iteration.
If the cap's effect on a board is a per-depth phenomenon (it changes where the tree
stops growing), a final-totals comparison cannot see it. This is the comparison the
instrument was asked for.
"""
import argparse
import json
import re
import subprocess
import sys


def parse(line):
    kv = {}
    for key in ("applied", "research", "rej", "cap_gate", "cap_clamp"):
        m = re.search(rf"\b{key} (\d+)", line)
        if m:
            kv[key] = int(m.group(1))
    m = re.search(r"\brmean (-|[\d.]+)", line)
    kv["rmean"] = None if (not m or m.group(1) == "-") else float(m.group(1))
    m = re.search(r"\bcap_rmean (-|[\d.]+)", line)
    kv["cap_rmean"] = None if (not m or m.group(1) == "-") else float(m.group(1))
    m = re.search(r"\bmag((?: r-?\d+=\d+)+)", line)
    kv["mag"] = {int(t.split("=")[0][1:]): int(t.split("=")[1]) for t in m.group(1).split()} if m else {}
    m = re.search(r"\bcap_mag((?: r-?\d+=\d+)+)", line)
    kv["cap_mag"] = {int(t.split("=")[0][1:]): int(t.split("=")[1]) for t in m.group(1).split()} if m else {}
    return kv


def run(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            if line.lower().startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR {fen}: {line}")
            if pred(line):
                return line

    send("uci")
    until(lambda l: l.startswith("uciok"))
    for k, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {k} value {v}")
        send("isready")
        until(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"position fen {fen}")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"go depth {depth}")
    until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=60)
    return p.stdout  # already drained by until(); parse from collected lines below


def collect(exe, fen, depth):
    """Run, and return the ordered list of (depth, totals, {root: block}) and the info lines."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            lines.append(line)
            if line.lower().startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR {fen}: {line}")
            if pred(line):
                return line

    send("uci")
    until(lambda l: l.startswith("uciok"))
    for k, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {k} value {v}")
        send("isready")
        until(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"position fen {fen}")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"go depth {depth}")
    until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=60)

    iters = {}
    nodes_at = {}
    for line in lines:
        m = re.match(r"^info depth (\d+) .*? nodes (\d+) ", line)
        if m and " info string " not in line:
            nodes_at[int(m.group(1))] = int(m.group(2))
        if not line.startswith("info string lmr depth "):
            continue
        body = line[len("info string lmr "):]
        head, _, tail = body.partition(" applied ")
        htok = head.split()
        if len(htok) < 4:
            continue
        d = int(htok[1])
        root = htok[3]
        kv = parse(line)
        iters.setdefault(d, {"all": None, "roots": {}})
        if root == "all":
            iters[d]["all"] = kv
        else:
            iters[d]["roots"][root] = kv
    return iters, nodes_at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fen")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    iters, nodes_at = collect(a.exe, a.fen, a.depth)
    print(f"exe {a.exe}\nfen {a.fen}\ngo depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print(f"{'d':>3s} {'nodes':>9s} {'dNodes':>8s} {'applied':>8s} {'rmean':>6s} "
          f"{'research':>8s} {'rej':>7s} {'capgate':>8s} {'clamp':>7s} {'caprmean':>8s}")
    prev = 0
    for d in sorted(iters):
        t = iters[d]["all"] or {}
        n = nodes_at.get(d)
        dn = (n - prev) if n is not None else None
        prev = n if n is not None else prev
        print(f"{d:>3d} {n if n is not None else -1:>9d} {dn if dn is not None else -1:>8d} "
              f"{t.get('applied',0):>8d} {t.get('rmean') if t.get('rmean') is not None else 0:>6.2f} "
              f"{t.get('research',0):>8d} {t.get('rej',0):>7d} {t.get('cap_gate',0):>8d} "
              f"{t.get('cap_clamp',0):>7d} "
              f"{t.get('cap_rmean') if t.get('cap_rmean') is not None else 0:>8.2f}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"iters": {str(k): v for k, v in iters.items()},
                       "nodes_at": {str(k): v for k, v in nodes_at.items()}}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
