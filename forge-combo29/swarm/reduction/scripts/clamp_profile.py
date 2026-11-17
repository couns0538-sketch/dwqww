#!/usr/bin/env python3
"""clamp_profile.py ON_EXE OFF_EXE [--depth N] [--json OUT]

For each of the 11 boards, per depth: how much of the reduction work is clamped, and
how the node count responds. Then a summary that asks whether the counter-cases show a
distinguishable clamp profile in the ITERATION WHERE THE TREES DIVERGE.

This is the sharpest form of the question the lead poses: the final totals do not
separate the classes (separation.py), so look at the iteration where the difference
is created rather than at its sum.

Reported per board:
  d_div        first depth at which the two builds' node counts differ
  clamp%_div   clamp/gate at that depth under cap-ON
  r_ON_div     mean reduction at that depth under cap-ON
  r_OFF_div    mean reduction at that depth under cap-OFF
  drop         r_OFF_div - r_ON_div  (how much the cap removed at that depth)
  dn_div       node difference at that depth
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
    p.wait(timeout=120)

    nodes, iters = {}, {}
    for line in lines:
        if line.startswith("info string lmr depth "):
            body = line[len("info string lmr "):]
            head, _, tail = body.partition(" applied ")
            h = head.split()
            if len(h) < 4 or h[3] != "all":
                continue
            d = int(h[1])
            kv = {"applied": int(tail.split()[0]) if tail.split() else 0}
            for key in ("cap_gate", "cap_clamp", "research", "rej"):
                m = re.search(rf"\b{key} (\d+)", body)
                kv[key] = int(m.group(1)) if m else 0
            m = re.search(r"\brmean (-|[\d.]+)", body)
            kv["rmean"] = None if (not m or m.group(1) == "-") else float(m.group(1))
            iters[d] = kv
            continue
        if line.startswith("info depth "):
            m = re.match(r"info depth (\d+) .*? nodes (\d+) ", line)
            if m:
                nodes[int(m.group(1))] = int(m.group(2))
    return nodes, iters


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
    hdr = (f"{'board':44s} {'cls':4s} {'d_div':>5s} {'clamp%':>6s} {'r_ON':>5s} {'r_OFF':>5s} "
           f"{'drop':>5s} {'dn_div':>7s} {'gate_div':>8s}")
    print(hdr)
    print("-" * len(hdr))
    for fen, cls in BOARDS:
        non, ion = collect(a.on, fen, a.depth)
        noff, ioff = collect(a.off, fen, a.depth)
        depths = sorted(set(non) & set(noff))
        d_div = next((d for d in depths if non[d] != noff[d]), None)
        if d_div is None:
            print(f"{fen:44s} {cls:4s} {'-':>5s} NO DIVERGENCE")
            continue
        ton, toff = ion.get(d_div, {}), ioff.get(d_div, {})
        gate = ton.get("cap_gate", 0)
        clamp = ton.get("cap_clamp", 0)
        share = 100.0 * clamp / gate if gate else 0.0
        ron = ton.get("rmean") or 0.0
        roff = toff.get("rmean") or 0.0
        row = {"fen": fen, "cls": cls, "d_div": d_div, "clamp_share": share,
               "r_on": ron, "r_off": roff, "drop": roff - ron,
               "dn_div": non[d_div] - noff[d_div], "gate": gate,
               "clamp": clamp, "nodes_on": non, "nodes_off": noff}
        rows.append(row)
        print(f"{fen:44s} {cls:4s} {d_div:>5d} {share:>5.1f}% {ron:>5.2f} {roff:>5.2f} "
              f"{roff-ron:>5.2f} {row['dn_div']:>+7d} {gate:>8d}")

    pred = [r for r in rows if r["cls"] == "pred"]
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    print()
    for name, key in (("clamp% at divergence", "clamp_share"), ("r drop at divergence", "drop"),
                      ("r_ON at divergence", "r_on"), ("r_OFF at divergence", "r_off")):
        pv = sorted(r[key] for r in pred)
        cv = [r[key] for r in cntr]
        inside = [v for v in cv if pv[0] <= v <= pv[-1]]
        print(f"{name:24s} predicted [{pv[0]:.3f}, {pv[-1]:.3f}]  counter "
              f"{['%.3f' % v for v in cv]}  inside-range {len(inside)}/{len(cv)}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
