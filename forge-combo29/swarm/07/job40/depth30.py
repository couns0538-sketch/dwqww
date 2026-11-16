#!/usr/bin/env python3
"""depth30.py -- final convergence check: the five decisive fifty-move cases plus the artefact #7,
at depth 30. Reports whether any changes category.

Categories (thresholds fixed before the run, same as job39): DECISIVE-WIN (mate for the side to move,
or cp >= +300), DECISIVE-LOSS (mate against, or cp <= -300), INCONCLUSIVE otherwise.
Reference board = the same position with the halfmove counter set to 0.
Base build, Threads 1, Hash 16, OwnBook false.
"""
import json
import queue
import re
import subprocess
import sys
import threading

BASE = "/agent/repos/base/forge-combo29/build-rel/forge"
CASES = [0, 4, 7, 10, 11, 13]     # five decisive (0,4,10,11,13) + the artefact (7)


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=3000):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = R(p.stdout)

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
    score, nodes = None, None
    while True:
        l = r.get(3000)
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
    try: p.wait(timeout=60)
    except subprocess.TimeoutExpired: p.kill()
    return {"score": score, "nodes": nodes}


def cls(sc):
    if sc is None:
        return "NO-SCORE"
    k, v = sc
    if k == "mate":
        return "DECISIVE-WIN" if v > 0 else "DECISIVE-LOSS"
    if v >= 300:
        return "DECISIVE-WIN"
    if v <= -300:
        return "DECISIVE-LOSS"
    return "INCONCLUSIVE"


def main():
    prev = json.load(open("../job38/raw/fifty_rate.json"))
    deep = json.load(open("../job38/raw/fifty_deep.json"))
    print(f"{'#':>2} {'d18':>14} {'d24':>14} {'d30':>14}  d18 class        d30 class        changed?")
    rows = []
    for i in CASES:
        fen = prev[i]["fen"]
        f = fen.split(); f[4] = "0"
        ref = " ".join(f)
        r18 = [x for x in deep["rows"] if x["i"] == i][0]["probe_deep"]
        r30 = search(BASE, ref, 30)
        c18 = cls(r18 if isinstance(r18, list) else [r18.split()[0], int(r18.split()[1])])
        c30 = cls(r30["score"])
        changed = "YES" if c18 != c30 else ""
        rows.append({"i": i, "fen": fen, "d18": r18, "d30": r30["score"],
                     "d30_nodes": r30["nodes"], "class_d18": c18, "class_d30": c30})
        print(f"{i:>2} {str(r18):>14} {'(see conv)':>14} {str(r30['score']):>14}  "
              f"{c18:>15} {c30:>15} {changed}", flush=True)
    import os
    os.makedirs("raw", exist_ok=True)
    json.dump(rows, open("raw/depth30.json", "w"), indent=1)
    changed = [r for r in rows if r["class_d18"] != r["class_d30"]]
    print()
    print(f"categories changed between depth 18 and depth 30: {len(changed)}")
    for r in changed:
        print(f"  #{r['i']} {r['class_d18']} -> {r['class_d30']} ({r['d18']} -> {r['d30']})")
    if not changed:
        print("RESULT: every one of the six holds its category at depth 30. The rate is settled.")


if __name__ == "__main__":
    main()
