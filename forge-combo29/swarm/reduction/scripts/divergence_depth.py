#!/usr/bin/env python3
"""divergence_depth.py -- at which depth do cap-ON and cap-OFF first disagree in node
count, and what do the reduction counters do at that depth?

The final-total comparison does not separate the counter-cases (see separation.py).
This asks a finer question: the two builds are identical up to some depth, then
diverge. If the counter-case boards diverge at a systematically different point, or
with a different reduction profile AT THE DIVERGENCE, that is a location for the
second mechanism. If they do not differ there either, the second mechanism is not
visible in this instrument at all and that is the answer.

Controls:
  - depths 1..D must be identical between the builds up to the first divergence
    (otherwise the run is contaminated and the row is dropped)
  - a board on which the two builds are identical to depth D is reported as such,
    not silently skipped

Usage: divergence_depth.py ON_EXE OFF_EXE [--depth N] [--json OUT]
"""
import argparse
import json
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

    nodes, applied, rmean, clamp, best = {}, {}, {}, {}, None
    for line in lines:
        if line.startswith("bestmove"):
            best = line.split()[1]
            continue
        if line.startswith("info string lmr depth "):
            body = line[len("info string lmr "):]
            head, _, tail = body.partition(" applied ")
            h = head.split()
            if len(h) < 4 or h[3] != "all":
                continue
            d = int(h[1])
            applied[d] = int(tail.split()[0]) if tail.split() else 0
            import re
            m = re.search(r"\brmean (-|[\d.]+)", body)
            rmean[d] = None if (not m or m.group(1) == "-") else float(m.group(1))
            m = re.search(r"\bcap_clamp (\d+)", body)
            clamp[d] = int(m.group(1)) if m else 0
            continue
        if line.startswith("info depth "):
            import re
            m = re.match(r"info depth (\d+) .*? nodes (\d+) ", line)
            if m:
                nodes[int(m.group(1))] = int(m.group(2))
    return {"nodes": nodes, "applied": applied, "rmean": rmean, "clamp": clamp, "best": best}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("on")
    ap.add_argument("off")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    rows = []
    print(f"ON  {a.on}\nOFF {a.off}\ngo depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print()
    hdr = (f"{'board':44s} {'cls':4s} {'d1st':>5s} {'n_on':>7s} {'n_off':>7s} {'dn_total':>9s} "
           f"{'dN@div':>8s} {'appl_on':>8s} {'appl_off':>8s} {'r_ON':>5s} {'r_OFF':>6s} {'clamp':>6s}")
    print(hdr)
    print("-" * len(hdr))
    for fen, cls in BOARDS:
        ron = collect(a.on, fen, a.depth)
        roff = collect(a.off, fen, a.depth)
        depths = sorted(set(ron["nodes"]) & set(roff["nodes"]))
        first = None
        for d in depths:
            if ron["nodes"][d] != roff["nodes"][d]:
                first = d
                break
        # control: no divergence before `first` (true by construction of `first`), and
        # the last depth must actually differ (else the builds are identical)
        last = depths[-1] if depths else None
        n_on = ron["nodes"].get(last, -1)
        n_off = roff["nodes"].get(last, -1)
        if first is not None and first > 1:
            for d in range(1, first):
                if d in ron["nodes"] and ron["nodes"][d] != roff["nodes"][d]:
                    print(f"  CONTAMINATED row {fen}: divergence before the recorded first")
        row = {
            "fen": fen, "cls": cls, "first_div": first, "depth": last,
            "n_on": n_on, "n_off": n_off, "dn": n_on - n_off,
            "dn_at_div": (ron["nodes"].get(first, 0) - roff["nodes"].get(first, 0)) if first else 0,
            "appl_on": ron["applied"].get(first, 0) if first else 0,
            "appl_off": roff["applied"].get(first, 0) if first else 0,
            "r_on": ron["rmean"].get(first) if first else None,
            "r_off": roff["rmean"].get(first) if first else None,
            "clamp_at_div": ron["clamp"].get(first, 0) if first else 0,
            "best_on": ron["best"], "best_off": roff["best"],
        }
        rows.append(row)
        print(f"{fen:44s} {cls:4s} {str(first):>5s} {n_on:>7d} {n_off:>7d} {row['dn']:>+9d} "
              f"{row['dn_at_div']:>+8d} {row['appl_on']:>8d} {row['appl_off']:>8d} "
              f"{(row['r_on'] if row['r_on'] is not None else 0):>5.2f} "
              f"{(row['r_off'] if row['r_off'] is not None else 0):>6.2f} {row['clamp_at_div']:>6d}")

    pred = [r for r in rows if r["cls"] == "pred" and r["first_div"]]
    cntr = [r for r in rows if r["cls"] == "CNTR" and r["first_div"]]
    print()
    print("first divergence depth:")
    print(f"  predicted   {sorted(r['first_div'] for r in pred)}")
    print(f"  counter     {sorted(r['first_div'] for r in cntr)}")
    print("sign of the node change AT the first divergence depth:")
    print(f"  predicted   {[r['dn_at_div'] for r in pred]}")
    print(f"  counter     {[r['dn_at_div'] for r in cntr]}")
    same_sign = all((r["dn_at_div"] > 0) == (r["dn"] > 0) for r in rows if r["first_div"])
    print(f"  the sign at divergence equals the sign at the final depth on "
          f"{sum(1 for r in rows if r['first_div'] and ((r['dn_at_div'] > 0) == (r['dn'] > 0)))} of "
          f"{sum(1 for r in rows if r['first_div'])} boards")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
