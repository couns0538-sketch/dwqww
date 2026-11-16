#!/usr/bin/env python3
"""hang_repro.py — is the Threads-4 hang on 5R2/1p5k/6p1/8/1K6/5q2/8/8 real and reproducible?

Part 1 of the hang investigation. Every run is a FRESH engine process, driven one command at a
time, and stdout is read until `bestmove` before anything else is written (so 19-F12's
fabricated bestmove cannot be mistaken for a completion).

Each run records: wall time from `go` to `bestmove`, the last depth reached, the last node count,
the exit code, and -- if it hit the limit -- a flag HANG. A run that never prints bestmove within
the limit is a hang. After a hang the process is left running for stack capture by another
script, or killed here when --kill is given.

Usage:
  hang_repro.py EXE OUTDIR TAG --runs N --threads T --depth D|inf [--limit S] [--fen FEN]
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

FEN = "5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"


def new_engine(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr],
                     daemon=True).start()
    return p, q, err


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def drain(q, p, until=None, limit=60.0):
    got = []
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        try:
            ln = q.get(timeout=0.05)
        except queue.Empty:
            if p.poll() is not None and q.empty():
                break
            continue
        got.append(ln)
        if until and (ln == until or ln.startswith(until)):
            return got, True
    return got, False


def one(exe, threads, depth, limit, fen):
    p, q, err = new_engine(exe)
    try:
        for c in ["uci", "isready",
                  "setoption name Hash value 16",
                  "setoption name Threads value %d" % threads]:
            send(p, c)
            if c != "uci":
                send(p, "isready")
                drain(q, p, until="readyok", limit=20.0)
        # ucinewgame MUST come before `position`: it clears the board back to startpos, so
        # sending it afterwards silently searches startpos and the FEN is never measured.
        send(p, "ucinewgame")
        send(p, "isready")
        drain(q, p, until="readyok", limit=20.0)
        send(p, "position fen " + fen)
        ans = drain(q, p, until="readyok", limit=20.0)  # isready is sent below
        send(p, "isready")
        ans2 = drain(q, p, until="readyok", limit=20.0)
        setup_lines = ans[0] + ans2[0]
        for ln in setup_lines:
            if ("invalid FEN" in ln or "unknown option" in ln or "invalid value" in ln):
                return {"threads": threads, "depth": depth, "fen": fen, "hang": False,
                        "setup_refused": ln, "pid": p.pid,
                        "measured": {"bestmove_line_found": False,
                                     "node_count_found": False}}, p, []
        go = "go depth %d" % depth if depth != "inf" else "go infinite"
        t0 = time.monotonic()
        send(p, go)
        limit_s = 600.0 if depth == "inf" else limit
        got, ok = drain(q, p, until="bestmove", limit=limit_s)
        wall = time.monotonic() - t0
        best = ""
        last_depth = None
        last_nodes = None
        infos = 0
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
            if ln.startswith("info "):
                infos += 1
                parts = ln.split()
                if "depth" in parts:
                    try:
                        last_depth = int(parts[parts.index("depth") + 1])
                    except Exception:
                        pass
                if "nodes" in parts:
                    try:
                        last_nodes = int(parts[parts.index("nodes") + 1])
                    except Exception:
                        pass
        rec = {"threads": threads, "depth": depth, "fen": fen,
               "hang": not ok, "wall": round(wall, 3),
               "bestmove": best, "last_depth": last_depth,
               "last_nodes": last_nodes, "info_lines": infos,
               "measured": {"bestmove_line_found": bool(best),
                            "node_count_found": last_nodes is not None},
               "pid": p.pid, "stderr_lines": len(err)}
        return rec, p, got
    except Exception as e:
        return {"threads": threads, "depth": depth, "fen": fen, "hang": True,
                "error": repr(e), "pid": p.pid}, p, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("tag")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--depth", default="12")
    ap.add_argument("--limit", type=float, default=60.0)
    ap.add_argument("--fen", default=FEN)
    ap.add_argument("--keep", action="store_true", help="leave hung processes alive")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    depth = a.depth if a.depth == "inf" else int(a.depth)
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    hangs = 0
    walls = []
    leftovers = []
    with open(path, "w") as f:
        for i in range(a.runs):
            rec, p, _ = one(a.exe, a.threads, depth, a.limit, a.fen)
            rec["run"] = i
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if rec["hang"]:
                hangs += 1
                print("run %2d HANG (last depth %s, pid %s)" %
                      (i, rec.get("last_depth"), rec.get("pid")), flush=True)
                if a.keep:
                    leftovers.append(p.pid)
                else:
                    p.kill()
            else:
                walls.append(rec["wall"])
                print("run %2d ok %.2fs %s depth %s nodes %s" %
                      (i, rec["wall"], rec.get("bestmove"), rec.get("last_depth"),
                       rec.get("last_nodes")), flush=True)
            try:
                send(p, "quit")
                p.wait(timeout=5)
            except Exception:
                p.kill()
    walls.sort()
    print()
    print("tag=%s threads=%s depth=%s runs=%d hangs=%d" %
          (a.tag, a.threads, depth, a.runs, hangs))
    if walls:
        print("median time to bestmove (non-hanging) = %.3f s over %d runs" %
              (walls[len(walls) // 2], len(walls)))
        print("min %.3f  max %.3f" % (walls[0], walls[-1]))
    if leftovers:
        print("left alive for stack capture: %s" % leftovers)


if __name__ == "__main__":
    main()
