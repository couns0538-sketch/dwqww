#!/usr/bin/env python3
"""Verify BY EFFECT that every advertised boolean option reaches the search.

Each of these goes through uci.cpp:403-421's name-comparison chain into a bool*. A mis-wired
target, or a name missing from that chain, would be accepted silently and change nothing. For each
option: run a cold depth-12 search with the default, then with the opposite value, and require the
node count to differ. A pair of identical node counts means the flag did not reach the search.

Options that cannot show an effect on a bare depth-12 search (book, timing, protocol, spin options)
are excluded deliberately and listed as excluded, not silently skipped.
"""
import os
import queue
import subprocess
import sys
import threading

TARGETS = [
    "ContHist4PlyRead", "NonPawnCorrection", "LmrDeeperShallower", "ThreatHistory",
    "LmrSignedCorrection", "LmrLateParentRelief", "NullSeeVeto", "AspArmLate",
    "EvasionOrdering", "QuietExtinction", "TmFinishIteration",
    "HindsightDepth", "NullThreatVerify", "AspCappedReopen", "TmNodeShare",
    "SoundMatePruning", "EvalRule50Damp", "DeadMaterial", "UseNNUE",
]
EXCLUDED = {
    "Ponder": "affects the search protocol, not the tree",
    "OwnBook": "controls whether the book answers; tested in job17",
    "Hash": "spin", "Threads": "spin", "MultiPV": "spin", "Move Overhead": "spin",
}


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=180):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, opt, value, depth=12, fen=None):
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
        l = r.get(30)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + o)
        send("isready")
        drain()
    if opt is not None:
        send(f"setoption name {opt} value {value}")
        send("isready")
        drain()
    send("ucinewgame")
    send("isready")
    drain()
    send("position fen " + (fen or "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
    send("isready")
    drain()
    send(f"go depth {depth}")
    nodes = None
    while True:
        l = r.get(240)
        if l is None:
            raise RuntimeError("no bestmove")
        if l.startswith(f"info depth {depth}") and " nodes " in l:
            try:
                nodes = int(l.split(" nodes ")[1].split()[0])
            except Exception:
                pass
        if l.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if nodes is None:
        raise RuntimeError(f"no nodes for {opt}={value}")
    return nodes


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    base = search(exe, None, None)
    rows, noeffect = [], []
    print(f"baseline (all defaults): {base} nodes", flush=True)
    for opt in TARGETS:
        off = search(exe, opt, "false")
        on = search(exe, opt, "true")
        same = (off == on)
        rows.append((opt, off, on, same))
        print(f"{opt:24s} false {off:7d}  true {on:7d}  "
              f"{'NO EFFECT' if same else 'differs'}", flush=True)
        if same:
            noeffect.append(opt)
    with open(os.path.join(outdir, "result.txt"), "w") as fh:
        fh.write(f"baseline {base}\n")
        fh.write("excluded (deliberate):\n")
        for k, v in EXCLUDED.items():
            fh.write(f"  {k}: {v}\n")
        fh.write("option false true no_effect\n")
        for opt, off, on, same in rows:
            fh.write(f"{opt} {off} {on} {same}\n")
    print()
    if noeffect:
        print("NO-EFFECT options (" + ", ".join(noeffect) + "): either they do not reach the "
              "search, or their effect on startpos at this depth coincides with the other value")
        print(f"RESULT: {len(noeffect)} option(s) showed no effect")
        sys.exit(1)
    print(f"RESULT: all {len(rows)} boolean options measurably changed the search")


if __name__ == "__main__":
    main()
