#!/usr/bin/env python3
"""identity40.py -- the flag-on/flag-off identity proof.

Runs N positions on two builds and compares, per position, the bestmove, the final
depth, the score and the node count. The claim to be tested is that FORGE_LMR_STATS=1
changes nothing but printed lines.

Outputs a machine-readable summary plus a return code: 0 only if every position
matched on all four fields.

Usage: identity40.py EXE_A EXE_B FENS [--depth N] [--limit N] [--json OUT]
"""
import argparse
import json
import re
import subprocess
import sys

RE_INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*? nodes (\d+) ")
RE_BEST = re.compile(r"^bestmove (\S+)")


def search(exe, fen, depth):
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
            low = line.lower()
            if low.startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR {exe} {fen}: {line}")
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
    best = None
    depth_seen = 0
    score = None
    nodes = None
    while True:
        line = until(lambda l: l.startswith("bestmove") or RE_INFO.match(l))
        if line is None:
            break
        m = RE_BEST.match(line)
        if m:
            best = m.group(1)
            break
        m = RE_INFO.match(line)
        if m:
            depth_seen = int(m.group(1))
            score = f"{m.group(2)}{m.group(3)}"
            nodes = int(m.group(4))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=30)
    return {"bestmove": best, "depth": depth_seen, "score": score, "nodes": nodes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("fens")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    fens = [l.strip() for l in open(a.fens) if l.strip() and not l.strip().startswith("#")]
    fens = fens[: a.limit]
    rows = []
    bad = 0
    print(f"A {a.a}\nB {a.b}\nregime = go depth {a.depth}, Threads 1 Hash 16 OwnBook false")
    print(f"{'#':>3s} {'fen':44s} {'A move':7s} {'B move':7s} {'A nodes':>8s} {'B nodes':>8s} {'A sc':>8s} {'B sc':>8s}  same")
    for i, fen in enumerate(fens, 1):
        ra = search(a.a, fen, a.depth)
        rb = search(a.b, fen, a.depth)
        same = (ra["bestmove"] == rb["bestmove"] and ra["nodes"] == rb["nodes"]
                and ra["score"] == rb["score"] and ra["depth"] == rb["depth"])
        if not same:
            bad += 1
        rows.append({"i": i, "fen": fen, "a": ra, "b": rb, "same": same})
        print(f"{i:>3d} {fen[:44]:44s} {str(ra['bestmove']):7s} {str(rb['bestmove']):7s} "
              f"{ra['nodes'] if ra['nodes'] is not None else -1:>8d} "
              f"{rb['nodes'] if rb['nodes'] is not None else -1:>8d} "
              f"{str(ra['score']):>8s} {str(rb['score']):>8s}  {'yes' if same else 'NO'}")
    print()
    print(f"IDENTICAL {len(rows) - bad} of {len(rows)}; differing {bad}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
