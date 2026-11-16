#!/usr/bin/env python3
"""counterrun.py -- rows + the per-go 'info string cfp' line, for the job-3b counter build.

Usage: counterrun.py --exe PATH --set FENS --out ROWS --cfp CFPFILE --depth N
                     --opts 'Name=Value;...' --meta METAFILE
Protocol per position: ucinewgame, isready, go depth N, wait for bestmove.
The LAST 'info string cfp ' line before each bestmove is appended to CFPFILE.
Every answer line is read; the run STOPS on 'unknown option' or 'invalid value' (exit 2).
"""
import argparse
import hashlib
import re
import subprocess
import sys
import threading
import time

STOP_PAT = re.compile(r"unknown option|invalid value")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cfp", required=True)
    ap.add_argument("--prefix", default="cfp")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--opts", default="")
    ap.add_argument("--meta", default=None)
    a = ap.parse_args()

    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    out_lines = []
    lock = threading.Lock()
    def reader():
        for line in p.stdout:
            with lock:
                out_lines.append(line)
    threading.Thread(target=reader, daemon=True).start()
    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()
    def wait_for(tok, timeout=60):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                for l in out_lines:
                    if l.strip().startswith(tok):
                        return True
                for l in out_lines:
                    if STOP_PAT.search(l):
                        print(f"REFUSED: {l.strip()}")
                        raise SystemExit(2)
            time.sleep(0.02)
        return False

    send("uci")
    if not wait_for("uciok"):
        print("REFUSED: no uciok")
        raise SystemExit(2)
    idname = ""
    with lock:
        for l in out_lines:
            if l.startswith("id name "):
                idname = l.strip()
    opts = [o for o in a.opts.split(";") if o.strip()]
    for o in ["Threads=1", "Hash=16", "OwnBook=false"] + opts:
        send(f"setoption name {o.replace('=', ' value ')}")
    send("isready")
    if not wait_for("readyok"):
        print("REFUSED: no readyok")
        raise SystemExit(2)

    rows = []
    cfp_lines = []
    for i, fen in enumerate(open(a.set, encoding="utf-8", errors="replace"), 0):
        fen = fen.strip()
        if not fen:
            continue
        n0 = len(out_lines)
        send("ucinewgame")
        send("isready")
        wait_for("readyok")
        send(f"position fen {fen}")
        send(f"go depth {a.depth}")
        t0 = time.monotonic()
        best = None
        nodes = None
        cfp = None
        while time.monotonic() - t0 < 600:
            with lock:
                fresh = out_lines[n0:]
                del out_lines[n0:]
            if not fresh:
                if time.monotonic() - t0 > 600:
                    break
                time.sleep(0.02)
                continue
            for l in fresh:
                l = l.strip()
                if l.startswith(f"info string {a.prefix} "):
                    cfp = l[len("info string "):]
                elif l.startswith("info") and " nodes " in l:
                    t = l.split()
                    try:
                        nodes = int(t[t.index("nodes") + 1])
                    except Exception:
                        pass
                elif l.startswith("bestmove"):
                    best = l.split()[1]
                    break
            if best is not None:
                break
        rows.append(f"{i} | {nodes} | {best}")
        cfp_lines.append(cfp if cfp else "MISSING")
    send("quit")
    p.wait(timeout=30)
    open(a.out, "w").write("\n".join(rows) + "\n")
    open(a.cfp, "w").write("\n".join(cfp_lines) + "\n")
    if a.meta:
        sha = hashlib.sha256(open(a.exe, "rb").read()).hexdigest()
        open(a.meta, "w").write(
            f"exe={a.exe}\nsha256={sha}\n{idname}\n" +
            "".join(f"setoption name {o.replace('=', ' value ')}\n" for o in
                    ["Threads=1", "Hash=16", "OwnBook=false"] + opts) +
            f"depth={a.depth}\n")
    print(f"rows: {len(rows)} -> {a.out}; cfp lines: {len(cfp_lines)} -> {a.cfp}")

if __name__ == "__main__":
    main()
