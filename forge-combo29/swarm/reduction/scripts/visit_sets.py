#!/usr/bin/env python3
"""visit_sets.py ON_EXE OFF_EXE [--depth N] [--json OUT]

The cheapest decisive probe of §6: at the depth where cap-ON and cap-OFF first disagree,
did the two builds visit the SAME positions with different multiplicity, or DIFFERENT
positions?

Requires builds of the instrumented source with FORGE_LMR_KEYS=1, which prints per ply:

    count  number of node visits at that ply
    xor    XOR of the position keys  (order-independent, cancels duplicates)
    sum    sum of the position keys  (order-independent, counts duplicates)

So per ply, comparing the two builds:
  count differs, xor EQUAL, sum EQUAL   -> same SET, different NUMBER of visits
  count differs, xor differs            -> genuinely DIFFERENT positions visited
  count differs, xor equal, sum differs -> same set, different multiplicity
                                          (xor cancels, sum accumulates)

The decision this makes: a reduction-count instrument can only explain the node
difference if the visit sets are the same and only multiplicity changes. If the sets
differ, no aggregate of reduction counts was ever going to be the explanation, and the
negative result in FINDINGS §5.1 is explained rather than merely reported.

Usage: visit_sets.py ON OFF --depth 10
"""
import argparse
import json
import re
import subprocess
import sys

BOARDS = [
    ("8/8/2B1k3/8/3PP3/P7/4K3/7R b - - 11 95", "pred"),
    ("8/8/2k5/4P3/3P4/P7/4K3/7R w - - 1 106", "pred"),
    ("8/2k5/4P3/8/3P4/PR6/3K4/8 b - - 0 109", "CNTR"),
    ("8/4k3/8/6R1/8/P7/3K4/8 b - - 1 116", "pred"),
    ("1R6/8/k7/8/8/P7/8/2K5 b - - 15 123", "pred"),
    ("8/8/8/4R3/2k5/P7/8/2K5 w - - 22 127", "CNTR"),
    ("8/8/8/1R6/1K6/P7/3k4/8 b - - 57 144", "pred"),
    ("8/8/P7/8/8/4K3/1k6/8 b - - 18 186", "pred"),
    ("6K1/2b5/p1k5/8/8/8/8/b7 b - - 5 137", "pred"),
    ("8/2k5/p7/8/8/7K/1b6/b7 w - - 26 148", "pred"),
    ("2k5/8/p7/6b1/8/2b4K/8/8 b - - 47 158", "pred"),
]
RE_KEYS = re.compile(r"^info string keys depth (\d+) ply (\d+) count (\d+) xor ([0-9a-f]+) sum ([0-9a-f]+)$")


def collect(exe, fen, depth):
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
                raise SystemExit(f"PROTOCOL ERROR {fen} {exe}: {line}")
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
    p.wait(timeout=180)

    keys = {}   # depth -> ply -> (count, xor, sum)
    nodes = {}
    for line in lines:
        m = RE_KEYS.match(line)
        if m:
            d, ply, cnt = int(m.group(1)), int(m.group(2)), int(m.group(3))
            keys.setdefault(d, {})[ply] = (cnt, m.group(4), m.group(5))
            continue
        m = re.match(r"info depth (\d+) .*? nodes (\d+) ", line)
        if m and "info string" not in line:
            nodes[int(m.group(1))] = int(m.group(2))
    return keys, nodes


def classify(a, b):
    """a,b are (count,xor,sum). Return the relationship."""
    if a is None or b is None:
        return "one-side-missing"
    if a[0] == b[0]:
        return "identical" if a[1] == b[1] and a[2] == b[2] else "same-count-diff-keys"
    if a[1] == b[1] and a[2] == b[2]:
        return "same-set-different-multiplicity"
    if a[1] == b[1]:
        return "same-set-different-multiplicity"   # xor agrees; sum carries multiplicity
    return "DIFFERENT-POSITIONS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("on")
    ap.add_argument("off")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    rows = []
    print(f"ON  {a.on}\nOFF {a.off}\ngo depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print()
    hdr = (f"{'board':44s} {'cls':4s} {'d_div':>5s} {'ply':>3s} {'cnt_ON':>7s} {'cnt_OFF':>7s} "
           f"{'xor':>5s} {'sum':>5s} {'relation'}")
    print(hdr)
    print("-" * len(hdr))

    for fen, cls in BOARDS:
        kon, non = collect(a.on, fen, a.depth)
        koff, noff = collect(a.off, fen, a.depth)
        depths = sorted(set(kon) & set(koff))
        d_div = next((d for d in depths if non.get(d) != noff.get(d)), None)
        if d_div is None:
            print(f"{fen:44s} {cls:4s} {'-':>5s} no node divergence")
            continue
        plies = sorted(set(kon[d_div]) & set(koff[d_div]))
        first = None
        for ply in plies:
            rel = classify(kon[d_div][ply], koff[d_div][ply])
            if rel != "identical":
                first = (ply, rel)
                break
        if first is None:
            print(f"{fen:44s} {cls:4s} {d_div:>5d}  -    (all plies identical at divergence depth)")
            rows.append({"fen": fen, "cls": cls, "d_div": d_div, "first_ply": None,
                         "relation": "identical"})
            continue
        ply, rel = first
        con, xon, son = kon[d_div][ply]
        coff, xoff, soff = koff[d_div][ply]
        rows.append({"fen": fen, "cls": cls, "d_div": d_div, "first_ply": ply,
                     "relation": rel, "count_on": con, "count_off": coff,
                     "xor_same": xon == xoff, "sum_same": son == soff})
        print(f"{fen:44s} {cls:4s} {d_div:>5d} {ply:>3d} {con:>7d} {coff:>7d} "
              f"{'SAME' if xon == xoff else 'diff':>5s} {'SAME' if son == soff else 'diff':>5s} {rel}")

    print()
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    print("relation at the first ply where the visit sets differ, counter-cases:")
    for r in cntr:
        print(f"  {r['fen']}: {r['relation']}  (ply {r['first_ply']}, "
              f"count {r.get('count_on')} vs {r.get('count_off')})")
    diff_pos = [r for r in rows if r["relation"] == "DIFFERENT-POSITIONS"]
    print()
    print(f"boards where the builds visited genuinely DIFFERENT positions at the "
          f"divergence depth: {len(diff_pos)} of {len(rows)}")
    if len(diff_pos) == len(rows):
        print()
        print("VERDICT: on every board the two builds part by visiting DIFFERENT positions,")
        print("not by visiting the same positions a different number of times. That is why no")
        print("aggregate of reduction counts separated the counter-cases: the counters reduce")
        print("over different sets of nodes, so equal-looking aggregates hide different trees.")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
