#!/usr/bin/env python3
"""deepseek5 job12 harness: starts THE EXE NAMED on the command line; records path/sha256/id name
in a <rows>.meta beside every rows file; after every setoption reads to readyok and STOPS on
'unknown option' / 'invalid value'. Node sums over a position set at a fixed depth."""
import chess
import hashlib
import os
import subprocess
import sys
import time

class Eng:
    def __init__(self, exe, strict=True):
        self.strict = strict
        self.exe = exe
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = []
        import queue as _q, threading as _th
        self._q = _q.Queue()
        self._t = _th.Thread(target=self._reader, daemon=True)
        self._t.start()
        self.send("uci")
        self.idname = self.expect("id name", 30).strip()
        self.expect("uciok", 30)
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("setoption name OwnBook value false")
        self.send("isready")
        self.expect("readyok", 30)

    def _reader(self):
        for line in self.p.stdout:
            self._q.put(line)
        self._q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def expect(self, prefix, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            try:
                line = self._q.get(timeout=0.1)
            except _q.Empty:
                continue
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(prefix):
                return line
            if self.strict and ("unknown option" in line or "invalid value" in line):
                raise ValueError(f"SETOPTION REJECTED: {line.strip()}")
        raise TimeoutError(f"no {prefix} within {timeout}s")

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.expect("readyok", 30)   # raises ValueError on unknown/invalid

    def newgame(self):
        self.send("ucinewgame")
        self.send("isready")
        self.expect("readyok", 60)

def main():
    exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    opts = sys.argv[4:]
    tag = "+".join(opts).replace(" ", "+") if opts else "none"
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    e = Eng(exe)
    nostop = os.environ.get("DS5_NOSTOP") == "1"
    e.strict = not nostop
    for i in range(0, len(opts), 2):
        if nostop:
            e.send(f"setoption name {opts[i]} value {opts[i+1]}")
            e.send("isready")
            e.expect("readyok", 30)
        else:
            e.setoption(opts[i], opts[i + 1])   # raises ValueError on unknown/invalid — the Step-0 stop
    meta = (f"exe={exe}\nsha256={sha}\n{idname_line(e)}\n")
    rows = []
    total = 0
    for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
        fen = fen.strip()
        if not fen:
            continue
        e.newgame()
        e.send(f"position fen {fen}")
        e.send(f"go depth {depth}")
        best = None; nodes = None; score = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            try:
                l = e._q.get(timeout=1.0)
            except Exception:
                break
            if l is None:
                break
            if l.startswith("bestmove"):
                best = l.split()[1]
                break
            if l.startswith("info") and " score " in l and " nodes " in l:
                t = l.split()
                try:
                    i_s = t.index("score")
                    score = t[i_s + 1] + t[i_s + 2]
                    nodes = int(t[t.index("nodes") + 1])
                except Exception:
                    pass
        rows.append(f"{i}|{best}|{nodes}|{score}")
        total += nodes or 0
    e.send("quit")
    e.p.wait(timeout=30)
    outdir = "/tmp/glmflash/ds5j12"
    os.makedirs(outdir, exist_ok=True)
    base = f"{outdir}/{tag}_{os.path.basename(setfile)}_d{depth}"
    open(base + ".rows", "w").write("\n".join(rows) + "\n")
    open(base + ".meta", "w").write(meta)
    print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total} N={len(rows)} SHA={sha[:16]} ID={idname_line(e)[:50]}")

def idname_line(e):
    return e.idname if hasattr(e, "idname") else ""

if __name__ == "__main__":
    main()
