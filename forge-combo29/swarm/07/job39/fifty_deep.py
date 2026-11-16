#!/usr/bin/env python3
"""fifty_deep.py OUTDIR DEPTH

Closes the one gap in 07-F4: the 10 fifty-move positions that were INCONCLUSIVE at depth 12.

For each of the twenty, search the counter-RESET reference (the same board with the halfmove counter set
to 0, so the fifty-move rule is 100 half-moves away and cannot mask the result) at a DEEPER depth than
12. The point is to see how many of the 10 inconclusive ones become decisive, which turns "6 of 20" into
an estimate closer to the truth.

Decision thresholds, fixed BEFORE the run and stated here so the result cannot be read generously after
the fact:
  DECISIVE-WIN   : mate for the side to move, or cp >= +300
  DECISIVE-LOSS  : mate against, or cp <= -300
  INCONCLUSIVE   : -299 .. +299
A position is counted as a base error when its reset-counter reference is decisive at this depth, because
base answered `cp 0` without searching and a decisive reference means the position was not a draw.

The depth-12 numbers from 07-F4 are re-read from job38/raw/fifty_rate.json so the two runs are compared
against identical inputs.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

BASE = "/agent/repos/base/forge-combo29/build-rel/forge"
WIN, LOSS = 300, -300


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=1200):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(f"go depth {depth}")
    nodes, score = None, None
    while True:
        l = r.get(1200)
        if l is None:
            break
        if l.startswith("info depth") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = [m.group(1), int(m.group(2))]
        if l.startswith("bestmove"):
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"nodes": nodes, "score": score}


def classify(sc):
    """Accepts a [kind, value] list (fresh runs) or a "cp N"/"mate N" string (the stored d12 run)."""
    if sc is None:
        return "NO-SCORE"
    if isinstance(sc, str):
        parts = sc.split()
        if len(parts) != 2:
            return "NO-SCORE"
        kind, val = parts[0], int(parts[1])
    else:
        kind, val = sc
    if kind == "mate":
        return "DECISIVE-WIN" if val > 0 else "DECISIVE-LOSS"
    if val >= WIN:
        return "DECISIVE-WIN"
    if val <= LOSS:
        return "DECISIVE-LOSS"
    return "INCONCLUSIVE"


def with_counter(fen, v):
    f = fen.split(); f[4] = str(v); return " ".join(f)


def main():
    outdir = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    os.makedirs(outdir, exist_ok=True)
    prev = json.load(open("raw/fifty_rate.json"))
    print(f"fifty-move positions: {len(prev)}, reference depth now {depth} "
          f"(was 12), thresholds ±{WIN} cp or mate")
    rows = []
    print(f"{'#':>2} {'d12 probe':>12} {'d12 class':>15} {'d'+str(depth)+' probe':>14} "
          f"{'d'+str(depth)+' class':>15} changed?")
    for r in prev:
        fen = r["fen"]
        p12 = r["probe_counter0"]["score"]
        c12 = classify(p12)
        deep = search(BASE, with_counter(fen, 0), depth)
        cdeep = classify(deep["score"])
        changed = "YES" if (c12 == "INCONCLUSIVE" and cdeep.startswith("DECISIVE")) else ""
        rows.append({"i": r["i"], "fen": fen, "probe_d12": p12, "class_d12": c12,
                     "probe_deep": deep["score"], "class_deep": cdeep,
                     "deep_nodes": deep["nodes"]})
        print(f"{r['i']:>2} {str(p12):>12} {c12:>15} {str(deep['score']):>14} {cdeep:>15} {changed}",
              flush=True)

    from collections import Counter
    c12 = Counter(x["class_d12"] for x in rows)
    cd = Counter(x["class_deep"] for x in rows)
    newly = [x for x in rows if x["class_d12"] == "INCONCLUSIVE"
             and x["class_deep"].startswith("DECISIVE")]
    print()
    print(f"at depth 12: {dict(c12)}")
    print(f"at depth {depth}: {dict(cd)}")
    print()
    print(f"of the {c12.get('INCONCLUSIVE',0)} inconclusive at depth 12, "
          f"{len(newly)} became decisive at depth {depth}:")
    for x in newly:
        print(f"  #{x['i']:>2}  d12 {x['probe_d12']} -> d{depth} {x['probe_deep']}  "
              f"({x['class_deep']})  fen {x['fen'][:56]}")
    w = cd.get("DECISIVE-WIN", 0); l = cd.get("DECISIVE-LOSS", 0)
    print()
    print(f"TIGHTENED RATE at depth {depth}: decisive base error {w + l} of {len(rows)} "
          f"({100.0 * (w + l) / len(rows):.0f}%)")
    print(f"  of which a win thrown away ({w}) and a loss masked ({l})")
    json.dump({"depth": depth, "rows": rows}, open(os.path.join(outdir, "fifty_deep.json"), "w"),
              indent=1)


if __name__ == "__main__":
    main()
