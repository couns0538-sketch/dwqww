#!/usr/bin/env python3
"""validate_warm_cold.py -- prove my tables are COLD (fresh process per measurement).

Seat 10's rule: two identical searches in ONE process give 56,720 / 4,951 / 4,516 nodes, while
three separate processes give 56,720 three times; `ucinewgame` restores cold, `Clear Hash` does
not. So a node-count table is only cold if each row came from a fresh process (or ucinewgame).

This script proves it for MY two node-bearing tables by running the SAME case twice, in-process
repetition vs fresh-process repetition, and showing which one my harness actually produces:

  A. warm: one process, `go depth 12` three times back to back
  B. cold: three processes, one `go depth 12` each
  C. my check2 harness: the same FEN+depth requested twice -> must give identical nodes
     (if my harness were warm, the second call would differ)

usage: validate_warm_cold.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "check2"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "c2", os.path.join(HERE, "..", "check2", "check_s05f3.py"))
c2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c2)

FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"


def warm(exe, fen, depth, times=3):
    """Three searches in ONE process, nothing between them (no ucinewgame, no Clear Hash)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def pump():
        for l in p.stdout:
            with lock:
                out.append(l.rstrip("\n"))

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    time.sleep(0.05)
    send("isready")
    time.sleep(0.05)
    send("position fen " + fen)
    nodes = []
    for _ in range(times):
        with lock:
            mark = len(out)
        send("go depth %d" % depth)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 120:
            with lock:
                blk = out[mark:]
            if any(x.startswith("bestmove") for x in blk):
                break
            time.sleep(0.005)
        with lock:
            blk = out[mark:]
        infos = [x for x in blk if x.startswith("info") and " pv" in x]
        n = None
        if infos:
            t = infos[-1].split()
            if "nodes" in t:
                n = t[t.index("nodes") + 1]
        nodes.append(n)
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        pass
    return nodes


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    res = {"exe": os.path.realpath(exe), "fen": FEN, "depth": 12}
    res["A_warm_one_process_three_searches"] = warm(exe, FEN, 12, 3)
    res["B_cold_three_processes"] = [c2.run(exe, FEN, 12)["nodes"] for _ in range(3)]
    a = c2.run(exe, FEN, 12)["nodes"]
    b = c2.run(exe, FEN, 12)["nodes"]
    res["C_my_check2_harness_twice"] = [a, b]
    res["C_identical"] = a == b
    res["verdict"] = ("my harness is COLD: repeated calls through it agree, and they agree with "
                      "the fresh-process arm, not the warm arm"
                      if (res["C_identical"]
                          and len(set(res["B_cold_three_processes"])) == 1
                          and len(set(res["A_warm_one_process_three_searches"])) > 1)
                      else "INSPECT: the arms did not separate as expected")
    print(json.dumps(res, indent=1))
    with open(os.path.join(outdir, "warm_cold.json"), "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
