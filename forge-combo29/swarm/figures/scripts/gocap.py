#!/usr/bin/env python3
"""gocap.py — run one `go` form with a HARD wall-clock cap and report what came back.

Exists because the obvious version is wrong twice over:

  * `subprocess` + blocking `readline()` ignores the cap. A form that never answers
    (here: `go nodes abc`) blocks the reader past any `timeout=` you wrap around the
    process, because the process is alive and just not talking.
  * so the cap is enforced by a READER THREAD pushing lines into a queue, and the
    caller waits on the queue. `go nodes abc` is then reported as "no bestmove within
    N s", which is the measurement, rather than as a hang.

A form that never answers is a RESULT. The cap is printed beside every row so the
row cannot be read as an unbounded observation.

Usage:
    python3 gocap.py <cap_seconds> [FEN] [go form...]

Measured on 6b98f217 (g++ 13.3.0, FORGE_PORTABLE, startpos, cap 6 s):
    go depth 5        depth 5, 1001 nodes          -- the well-formed reference
    go depth abc      depth 1,   26 nodes          -- read_int() -> 0, clamp(0,1,64) = 1
    go nodes abc      NO bestmove within 6 s       -- and identical to `go infinite`
    go mate abc       NO bestmove within 6 s       -- identical to `go infinite`
"""
import os
import queue
import subprocess
import threading
import time

EXE_DEFAULT = os.environ.get("FORGE_BIN", "./forge")


class Proc:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def drain(self, want, timeout):
        out = []
        end = time.time() + timeout
        while True:
            left = end - time.time()
            if left <= 0:
                return out, False
            try:
                ln = self.q.get(timeout=left)
            except queue.Empty:
                return out, False
            if ln is None:
                return out, False
            out.append(ln)
            if ln.startswith(want):
                return out, True

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def probe(go, cap, fen=None, exe=EXE_DEFAULT):
    e = Proc(exe)
    e.send("uci")
    e.drain("uciok", 10)
    e.send("setoption name Hash value 16")
    e.send("setoption name Threads value 1")
    e.send("setoption name OwnBook value false")
    e.send("ucinewgame")
    e.send("position fen " + fen if fen else "position startpos")
    e.send("isready")
    e.drain("readyok", 10)
    e.send(go)
    lines, hit = e.drain("bestmove", cap)
    info = [l for l in lines if l.startswith("info depth")]
    bm = [l for l in lines if l.startswith("bestmove")]
    depth = nodes = None
    if info:
        f = info[-1].split()
        depth = int(f[f.index("depth") + 1]) if "depth" in f else None
        nodes = int(f[f.index("nodes") + 1]) if "nodes" in f else None
    e.close()
    return {"go": go, "answered": hit, "info": len(info), "depth": depth,
            "nodes": nodes, "bm": bm[0].split()[1] if bm else None}


if __name__ == "__main__":
    import sys
    cap = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    fen = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    forms = sys.argv[3:] or [
        "go depth 5", "go depth abc", "go depth", "go depth 0",
        "go wtime abc", "go wtime 0", "go movetime abc", "go movetime 0",
        "go nodes abc", "go nodes", "go nodes 0", "go mate abc", "go infinite",
    ]
    print("cap %.0fs   position %s" % (cap, fen or "startpos"))
    for g in forms:
        r = probe(g, cap, fen)
        print("%-18s answered=%-6s info_lines=%-3d depth=%-4s nodes=%-10s bestmove=%s"
              % (r["go"], r["answered"], r["info"], r["depth"], r["nodes"], r["bm"]))
