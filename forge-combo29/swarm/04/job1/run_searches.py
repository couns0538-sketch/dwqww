#!/usr/bin/env python3
"""run_searches.py — drive a Forge build through UCI, one fresh process per position.

Usage:
  run_searches.py --exe EXE --positions FILE --from N --count K --depth D --threads T
                  --hash H --outdir DIR --tag TAG [--timeout S]

Writes, for every search, a record in DIR/<tag>/records.jsonl and the raw
stdout/stderr of the engine in DIR/<tag>/raw/<index>_<n>.out .
Every option line actually sent is recorded. Reads every line up to readyok
after each setoption/position and stops on unknown option / invalid value /
invalid FEN / illegal move.
"""
import argparse
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe, timeout):
        self.exe = exe
        self.timeout = timeout
        self.lines = queue.Queue()
        self.err = []
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
            env={**os.environ, "TSAN_OPTIONS": "halt_on_error=0 second_deadlock_stack=1"})
        threading.Thread(target=self._pump_out, daemon=True).start()
        threading.Thread(target=self._pump_err, daemon=True).start()

    def _pump_out(self):
        for line in self.p.stdout:
            self.lines.put(line.rstrip("\r\n"))

    def _pump_err(self):
        for line in self.p.stderr:
            self.err.append(line.rstrip("\r\n"))

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def read_until(self, token):
        """Return the lines read up to and including `token`, or None on timeout/exit."""
        got = []
        deadline = time.monotonic() + self.timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            try:
                line = self.lines.get(timeout=min(left, 1.0))
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            got.append(line)
            if line.strip() == token or line.split(" ")[0] == token:
                return got

    def ready(self):
        self.send("isready")
        return self.read_until("readyok")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
            try:
                self.p.wait(timeout=5)
            except Exception:
                pass


def one_search(exe, fen, depth, threads, hash_mb, timeout, rawpath):
    eng = Engine(exe, timeout)
    optlines = []
    bad = None
    try:
        eng.send("uci")
        eng.read_until("uciok")
        opts = [("Hash", hash_mb), ("Threads", threads)] + S14
        for name, val in opts:
            cmd = "setoption name %s value %s" % (name, val)
            eng.send(cmd)
            optlines.append(cmd)
            lines = eng.ready()
            if lines is None:
                bad = "no readyok after %s" % cmd
                break
            for ln in lines:
                if any(b in ln for b in BAD):
                    bad = ln
        if bad is None:
            eng.send("ucinewgame")
            if eng.ready() is None:
                bad = "no readyok after ucinewgame"
        if bad is None:
            eng.send("position fen " + fen)
            lines = eng.ready()
            if lines is None:
                bad = "no readyok after position"
            else:
                for ln in lines:
                    if any(b in ln for b in BAD):
                        bad = ln
        t0 = time.monotonic()
        eng.send("go depth %d" % depth)
        got = eng.read_until("bestmove")
        wall = time.monotonic() - t0
        if got is None:
            return {"fen": fen, "hang": True, "exit": eng.p.poll(),
                    "stderr": "\n".join(eng.err), "opts": optlines, "bad": bad}
        best = ""
        nodes = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
            if ln.startswith("info") and " nodes " in ln:
                try:
                    nodes = int(ln.split(" nodes ")[1].split()[0])
                except Exception:
                    pass
        return {"fen": fen, "wall": wall, "bestmove": best, "nodes": nodes,
                "stderr": "\n".join(eng.err), "opts": optlines, "bad": bad,
                "exit": eng.p.poll()}
    finally:
        with open(rawpath, "w") as f:
            f.write("STDERR:\n" + "\n".join(eng.err) + "\n")
        eng.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--positions", required=True)
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", dest="hash_mb", type=int, default=16)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=float, default=180.0)
    a = ap.parse_args()

    fens = [l.strip() for l in open(a.positions) if l.strip() and not l.startswith("#")]
    fens = [f.split(";")[0].strip() for f in fens]
    sel = fens[a.start:a.start + a.count]
    d = os.path.join(a.outdir, a.tag)
    os.makedirs(os.path.join(d, "raw"), exist_ok=True)

    meta = {"exe": a.exe, "sha256": sha256(a.exe), "positions": a.positions,
            "start": a.start, "count": len(sel), "depth": a.depth,
            "threads": a.threads, "hash": a.hash_mb, "s14": S14}
    open(os.path.join(d, "meta.txt"), "w").write(json.dumps(meta, indent=1) + "\n")
    nm = subprocess.run("nm -C %s | grep -c __tsan_" % a.exe, shell=True,
                        capture_output=True, text=True).stdout.strip()
    open(os.path.join(d, "meta.txt"), "a").write("nm __tsan_ count: %s\n" % nm)
    idline = subprocess.run("%s <<< 'uci' 2>/dev/null | grep '^id name'" % a.exe,
                            shell=True, capture_output=True, text=True,
                            executable="/bin/bash").stdout.strip()
    open(os.path.join(d, "meta.txt"), "a").write("engine: %s\n" % idline)

    out = open(os.path.join(d, "records.jsonl"), "w")
    for i, fen in enumerate(sel):
        rawpath = os.path.join(d, "raw", "%04d.out" % i)
        rec = one_search(a.exe, fen, a.depth, a.threads, a.hash_mb, a.timeout, rawpath)
        rec["index"] = a.start + i
        out.write(json.dumps(rec) + "\n")
        out.flush()
        print("%4d %s %s" % (a.start + i, rec.get("bestmove", "HANG"),
                             "TSAN" if "__tsan" in rec.get("stderr", "") else ""),
              flush=True)
    out.close()


if __name__ == "__main__":
    main()
