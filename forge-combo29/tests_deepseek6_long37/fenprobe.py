#!/usr/bin/env python3
"""fenprobe.py -- per FEN of a set file: send `position fen X`, then `isready`, read EVERY
answer line up to readyok; STOP on 'invalid FEN' or 'illegal move' (record the exact line);
if accepted: `go perft 2` -> its count, then `d` (its board display). One process per FEN."""
import json
import subprocess
import sys
import threading
import queue

exe, setfile, statusfile = sys.argv[1], sys.argv[2], sys.argv[3]
fens = [l.strip() for l in open(setfile, encoding="utf-8", errors="replace") if l.strip()]
status = json.load(open(statusfile))
print("header: name | fen | python-chess valid | engine refused? (line) | perft 2 | == 400 (start) |")
for i, fen in enumerate(fens):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()
    def rd():
        try:
            for l in p.stdout:
                q.put(l)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=rd, daemon=True).start()
    def send(s):
        try:
            p.stdin.write(s + "\n"); p.stdin.flush()
        except Exception:
            pass
    def rl(tmo=5.0):
        try:
            return q.get(timeout=tmo)
        except queue.Empty:
            return ""
    send("uci")
    while True:
        l = rl()
        if not l or l.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    while True:
        l = rl()
        if not l or l.strip() == "readyok":
            break
    send(f"position fen {fen}")
    send("isready")
    refused = None
    while True:
        l = rl(10)
        if not l:
            break
        l = l.strip()
        if l.startswith("readyok"):
            break
        if "invalid FEN" in l or "illegal move" in l or "invalid" in l.lower():
            refused = l
            # drain until readyok or silence
            while True:
                l2 = rl(2)
                if not l2 or l2.strip().startswith("readyok"):
                    break
            break
    if refused:
        send("go perft 2")
        cnt = None
        t0 = __import__("time").monotonic()
        while __import__("time").monotonic() - t0 < 30:
            l = rl()
            if not l:
                if __import__("time").monotonic() - t0 > 30:
                    break
                continue
            t = l.split()
            if t and t[0] == "nodes" and len(t) > 1 and t[1].isdigit():
                cnt = int(t[1])
            if l.strip().startswith("bestmove"):
                break
        name = list(status.keys())[i] if i < len(status) else f"fen{i}"
        pv, valid, st, code = status[name] if i < len(status) else ("?", "?", "?", -1)
        print(f"| {name} | {fen} | {valid} | refused: {refused} | {cnt} | {'YES' if cnt == 400 else 'NO'} |")
        send("quit"); p.wait(timeout=10)
        continue
    send("go perft 2")
    cnt = None
    import time
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 60:
                break
            continue
        t = l.split()
        if t and t[0] == "nodes" and len(t) > 1 and t[1].isdigit():
            cnt = int(t[1])
        if l.strip().startswith("bestmove"):
            break
    name = list(status.keys())[i] if i < len(status) else f"fen{i}"
    pv, valid, st, code = status[name] if i < len(status) else ("?", "?", "?", -1)
    print(f"| {name} | {fen} | {valid} | accepted | {cnt} | {'YES' if cnt == 400 else 'NO'} |")
    send("quit"); p.wait(timeout=10)
