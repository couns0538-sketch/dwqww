#!/usr/bin/env python3
"""chkrun.py -- rows + capture every 'info string CHECK*' line per go (kimi5's job-6 flag build).
Usage: chkrun.py --exe PATH --set FENS --out ROWS --chk CHKFILE --depth N --opts '...' [--meta M]"""
import argparse
import hashlib
import subprocess
import sys
import threading
import time
import queue

STOP_PAT = None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chk", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--opts", default="")
    ap.add_argument("--meta", default=None)
    a = ap.parse_args()
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()
    def reader():
        try:
            for line in p.stdout:
                q.put(line)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=reader, daemon=True).start()
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    def rl(tmo=2.0):
        try:
            return q.get(timeout=tmo)
        except queue.Empty:
            return ""
    send("uci")
    idname = ""
    t0 = time.monotonic()
    while True:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 30:
                print("REFUSED: no uciok"); raise SystemExit(2)
            continue
        l = l.strip()
        if l.startswith("id name "):
            idname = l
        if l.startswith("uciok"):
            break
        if "unknown option" in l or "invalid value" in l:
            print(f"REFUSED: {l}"); raise SystemExit(2)
    opts = [o for o in a.opts.split(";") if o.strip()]
    for o in ["Threads=1", "Hash=16", "OwnBook=false"] + opts:
        send(f"setoption name {o.replace('=', ' value ')}")
    send("isready")
    while True:
        l = rl()
        if not l or l.strip().startswith("readyok"):
            break
    rows = []
    chk_out = []
    for i, fen in enumerate(open(a.set, encoding="utf-8", errors="replace")):
        fen = fen.strip()
        if not fen:
            continue
        send("ucinewgame"); send("isready")
        while True:
            l = rl()
            if not l or l.strip().startswith("readyok"):
                break
        send(f"position fen {fen}")
        send(f"go depth {a.depth}")
        best = None; nodes = None
        my_chk = []
        t0 = time.monotonic()
        while time.monotonic() - t0 < 900:
            l = rl()
            if not l:
                if time.monotonic() - t0 > 900:
                    break
                continue
            l = l.strip()
            if l.startswith("info string CHECK") or l.startswith("info string CHECKX") or l.startswith("info string CHECKFIRST"):
                my_chk.append(l)
            elif l.startswith("info") and " nodes " in l:
                t = l.split()
                try:
                    nodes = int(t[t.index("nodes") + 1])
                except Exception:
                    pass
            elif l.startswith("bestmove"):
                best = l.split()[1]
                break
            if "unknown option" in l or "invalid value" in l:
                print(f"REFUSED: {l}"); raise SystemExit(2)
        rows.append(f"{i} | {nodes} | {best}")
        chk_out.append(f"# pos {i}")
        chk_out.extend(my_chk)
    send("quit")
    p.wait(timeout=30)
    open(a.out, "w").write("\n".join(rows) + "\n")
    open(a.chk, "w").write("\n".join(chk_out) + "\n")
    if a.meta:
        sha = hashlib.sha256(open(a.exe, "rb").read()).hexdigest()
        open(a.meta, "w").write(f"exe={a.exe}\nsha256={sha}\n{idname}\n" +
            "".join(f"setoption name {o.replace('=', ' value ')}\n" for o in
                    ["Threads=1", "Hash=16", "OwnBook=false"] + opts) + f"depth={a.depth}\n")
    print(f"rows: {len(rows)} -> {a.out}; chk lines: {len(chk_out)} -> {a.chk}")

if __name__ == "__main__":
    main()
