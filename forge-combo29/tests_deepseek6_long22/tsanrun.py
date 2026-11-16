#!/usr/bin/env python3
"""tsanrun.py -- rows + TSan report capture for multithreaded runs.
Each position gets its own engine process; every 'WARNING: ThreadSanitizer' line (and any
'-race' summary) is captured with its position index. The run does not stop on a report."""
import argparse
import hashlib
import queue
import subprocess
import sys
import threading
import time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--opts", default="")
    ap.add_argument("--meta", default=None)
    a = ap.parse_args()
    opts = [o for o in a.opts.split(";") if o.strip()]
    rows = []
    races = []
    for i, fen in enumerate(open(a.set, encoding="utf-8", errors="replace")):
        fen = fen.strip()
        if not fen:
            continue
        p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, bufsize=1)
        out_q = queue.Queue()
        err_lines = []
        def rd_out():
            try:
                for l in p.stdout:
                    out_q.put(l)
            except Exception:
                pass
            out_q.put(None)
        def rd_err():
            for l in p.stderr:
                err_lines.append(l)
        threading.Thread(target=rd_out, daemon=True).start()
        threading.Thread(target=rd_err, daemon=True).start()
        def send(s):
            try:
                p.stdin.write(s + "\n"); p.stdin.flush()
            except Exception:
                pass
        send("uci")
        t0 = time.monotonic()
        while True:
            try:
                l = out_q.get(timeout=1.0)
            except queue.Empty:
                if time.monotonic() - t0 > 60:
                    rows.append(f"{i} | NORESP | -")
                    p.kill(); break
                continue
            if l is None or l.strip() == "uciok":
                break
        for o in ["Threads=1", "Hash=16", "OwnBook=false"] + opts:
            send(f"setoption name {o.replace('=', ' value ')}")
        send("isready")
        while True:
            l = out_q.get(timeout=60)
            if l is None or l.strip() == "readyok":
                break
        send(f"position fen {fen}")
        send(f"go depth {a.depth}")
        best = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 600:
            try:
                l = out_q.get(timeout=1.0)
            except queue.Empty:
                continue
            if l is None:
                break
            l = l.strip()
            if l.startswith("bestmove"):
                best = l.split()[1]
                break
            if "unknown option" in l or "invalid value" in l:
                rows.append(f"{i} | REFUSED | {l}")
                p.kill()
                break
        send("quit")
        try:
            p.wait(timeout=30)
        except Exception:
            p.kill()
        nodes = None
        # best-effort: no node parsing needed for TSan runs; keep the exit code instead
        rows.append(f"{i} | {best if best else 'NONE'} | exit={p.returncode}")
        nrac = sum(1 for l in err_lines if "WARNING: ThreadSanitizer" in l or "data race" in l or "thread deadlock" in l)
        races.append(f"# pos {i}: tsan-lines {nrac}, exit {p.returncode}")
        for l in err_lines:
            if "ThreadSanitizer" in l or "data race" in l:
                races.append(l.rstrip())
    open(a.out, "w").write("\n".join(rows) + "\n")
    open(a.out + ".tsan", "w").write("\n".join(races) + "\n")
    if a.meta:
        sha = hashlib.sha256(open(a.exe, "rb").read()).hexdigest()
        open(a.meta, "w").write(f"exe={a.exe}\nsha256={sha}\n" +
            "".join(f"setoption name {o.replace('=', ' value ')}\n" for o in
                    ["Threads=1", "Hash=16", "OwnBook=false"] + opts) + f"depth={a.depth}\n")
    tot = sum(1 for r in races if "ThreadSanitizer" in r or "data race" in r)
    print(f"rows: {len(rows)} -> {a.out}; race lines: {tot}")

if __name__ == "__main__":
    main()
