#!/usr/bin/env python3
"""Job 5 P2: option OFF must be the old engine, on 2,000 UHO positions.

Each position: `ucinewgame`, `position fen`, `go depth 9`; record bestmove, the
final score and the node count.  ONE sha256 over every answer of a run, plus the
smallest node count, so an empty run cannot pass.

Two invocations are compared by their hash lines.
"""

import hashlib
import json
import queue
import subprocess
import sys
import threading
import time

ENGINE = sys.argv[1]
EPD = sys.argv[2]
COUNT = int(sys.argv[3])
OUT = sys.argv[4]
OPTION = sys.argv[5] if len(sys.argv) > 5 else ""

DEPTH = 9
MIN_NODE_TOTAL = 1000        # a run whose positions all searched nothing cannot pass


def main():
    fens = []
    with open(EPD, errors="ignore") as f:
        for line in f:
            head = line.split(";")[0].split()
            if len(head) < 4:
                continue
            fens.append(" ".join(head[:4]) + " 0 1")
            if len(fens) >= COUNT:
                break
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def until(tok, limit=60.0):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if ln.startswith(tok):
                return got
        return got

    send("uci")
    until("uciok", 20)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    if OPTION:
        send(f"setoption name ContHistDeep value {OPTION}")
    send("isready")
    until("readyok", 20)

    answers = []
    t0 = time.time()
    for i, fen in enumerate(fens):
        send("ucinewgame")
        send("position fen " + fen)
        send(f"go depth {DEPTH}")
        got = until("bestmove", 120)
        best = None
        score = None
        nodes = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln.split()[1]
            if ln.startswith("info") and " score " in ln:
                t = ln.split()
                j = t.index("score")
                score = t[j + 1] + " " + t[j + 2]
                if " nodes " in ln:
                    nodes = int(ln.split(" nodes ")[1].split()[0])
        answers.append(f"{fen}|{best}|{score}|{nodes}")
        if (i + 1) % 250 == 0:
            print(f"{i+1}/{len(fens)} {time.time()-t0:.0f}s", flush=True)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    h = hashlib.sha256("\n".join(answers).encode()).hexdigest()
    node_list = []
    for a in answers:
        try:
            node_list.append(int(a.rsplit("|", 1)[1]))
        except Exception:
            node_list.append(0)
    total = sum(node_list)
    lo = min(node_list) if node_list else 0
    json.dump({"engine": ENGINE, "option": OPTION, "positions": len(answers),
               "sha256": h, "min_nodes": lo, "total_nodes": total,
               "answers": answers}, open(OUT, "w"))
    print(f"option={OPTION or 'none'}: {len(answers)} positions, sha256 {h}, "
          f"min nodes {lo}, total {total}")
    if total < MIN_NODE_TOTAL:
        print("IDENTITY PROOF VACUOUS: total nodes too small")
        sys.exit(1)


if __name__ == "__main__":
    main()
