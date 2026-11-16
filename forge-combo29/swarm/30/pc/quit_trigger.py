#!/usr/bin/env python3
"""quit_trigger.py -- WHICH stdin event fabricates the bestmove, and is the answer legal?

19-F12 / my 30-F21-22: closing stdin mid-search yields a fabricated bestmove. This narrows it:
  * `quit` sent mid-search (the normal GUI shutdown),
  * stdin CLOSED with no `quit` at all (a script that just closes the pipe),
  * `stop` mid-search (a legal UCI interruption -- must NOT be fabricated),
  * `isready` mid-search (must NOT be),
  * EOF after `go infinite` (long search, pipe closed).

For each: does a bestmove appear, with how many info lines, is the move legal on the board, and is
it the same move the uninterrupted search gives.

usage: quit_trigger.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXES = {"base": "/home/ubuntu/b/rel/forge", "pc": "/home/ubuntu/b/pc/forge"}
POS = "position startpos"
GO = "go depth 12"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}


def spawn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()
    return p, out, lock


def analyse(out, mark, fen):
    blk = out[mark:]
    infos = [l for l in blk if l.startswith("info depth")]
    bms = [l.split()[1] for l in blk if l.startswith("bestmove") and len(l.split()) > 1]
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    legal = None
    if bms:
        b = chess.Board(fen)
        legal = bms[0] == "0000" or any(m.uci() == bms[0] for m in b.legal_moves)
    return {"info_lines": len(infos), "bestmove": bms[0] if bms else None,
            "n_bestmoves": len(bms), "nodes": nodes, "legal": legal}


def run(exe, action, wait_s=1.5):
    """Start a depth-12 search, then apply `action`."""
    p, out, lock = spawn(exe)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    time.sleep(0.05)
    send("isready")
    time.sleep(0.05)
    send(POS)
    with lock:
        mark = len(out)
    send(GO)
    time.sleep(wait_s)
    rec = {"action": action}
    try:
        if action == "quit":
            send("quit")
        elif action == "close_stdin":
            p.stdin.close()
        elif action == "stop":
            send("stop")
            time.sleep(1.0)
        elif action == "isready":
            send("isready")
            time.sleep(1.0)
            rec["saw_readyok"] = any(x.strip() == "readyok" for x in out[mark:])
    except Exception as e:
        rec["send_error"] = repr(e)
    try:
        p.wait(timeout=20)
    except Exception:
        if action == "stop":
            send("quit")
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
        else:
            p.kill()
    time.sleep(0.1)
    with lock:
        rec.update(analyse(out, mark, chess.STARTING_FEN))
    return rec


def control(exe):
    """The uninterrupted answer for comparison."""
    p, out, lock = spawn(exe)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    time.sleep(0.05)
    send("isready")
    time.sleep(0.05)
    send(POS)
    with lock:
        mark = len(out)
    send(GO)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 120:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.005)
    with lock:
        r = analyse(out, mark, chess.STARTING_FEN)
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        pass
    return r


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    report = {"go": GO, "position": POS, "rows": []}
    for bname, exe in EXES.items():
        ctrl = control(exe)
        print("== %s control (uninterrupted): bm=%s nodes=%s legal=%s" % (
            bname, ctrl["bestmove"], ctrl["nodes"], ctrl["legal"]))
        for action in ("quit", "close_stdin", "stop", "isready"):
            r = run(exe, action)
            r["build"], r["control_bestmove"] = bname, ctrl["bestmove"]
            r["same_as_control"] = r["bestmove"] == ctrl["bestmove"]
            r["fabricated"] = r["info_lines"] == 0 and r["bestmove"] is not None
            report["rows"].append(r)
            print("   %-12s bm=%-6s infos=%-4s nodes=%-9s legal=%-5s same=%s%s" % (
                action, r["bestmove"], r["info_lines"], r["nodes"], r["legal"],
                r["same_as_control"], "   <-- FABRICATED" if r["fabricated"] else ""))
    with open(os.path.join(outdir, "quit_trigger.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    fab = [r for r in report["rows"] if r["fabricated"]]
    print("fabricated cases:", len(fab), "of", len(report["rows"]))
    for r in fab:
        print("  ", r["build"], r["action"], "->", r["bestmove"], "(control", r["control_bestmove"], ")")


if __name__ == "__main__":
    main()
