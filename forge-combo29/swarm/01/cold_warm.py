#!/usr/bin/env python3
"""swarm seat 01: cold vs warm, on the exact numbers my patch summary quotes.

Seat 10's rule: two identical unrestricted searches in ONE process differ (56,720 then 4,951 then 4,516),
a fresh process is cold every time, `ucinewgame` restores cold, and `Clear Hash` does NOT.

This script measures, for each exe:
  COLD  three separate processes, one search each -> must be equal
  WARM  one process, three searches with nothing between -> may differ
  UNEW  one process, three searches each preceded by `ucinewgame` + isready -> must be cold each time
  CHASH one process, three searches each preceded by `Clear Hash` -> seat 10 says NOT cold
Boards: the mate-in-one board at halfmove 99 and at 100, `go depth 6`, which is what PATCH_SUMMARY quotes
(126 nodes / mate 1, and 0 nodes / cp 0). Also the KQ v K halfmove-100 draw board (the 280-node figure).

Usage: cold_warm.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 300.0


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def parse(dl):
    if not dl:
        return {"score": "", "nodes": ""}
    f = dl[-1].split()
    score = nodes = ""
    if "score" in f:
        i = f.index("score")
        score = " ".join(f[i + 1:i + 3])
    if "nodes" in f:
        nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes}


def cold(exe, fen, go="go depth 6"):
    """One fresh process, one search."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send("position fen " + fen)
    send("isready")
    until("readyok")
    send(go)
    until("bestmove")
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    return parse([l for l in buf if l.startswith("info depth")])


def series(exe, fen, reset, go="go depth 6", n=3):
    """One process, n searches, with an optional reset between them. Returns the n results.

    reset=None means the TRUE warm case seat 10 measured: `position fen` is sent ONCE, then n
    consecutive `go` commands with literally nothing between them.
    """
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())

    def until(prefix, buf):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    out = []
    if reset is None:
        # true warm: position once, then n goes with nothing between
        send("position fen " + fen)
        send("isready")
        until("readyok", [])
        for _ in range(n):
            b = []
            send(go)
            until("bestmove", b)
            out.append(parse([l for l in b if l.startswith("info depth")]))
        time.sleep(0.1)
        send("quit")
        try:
            p.wait(timeout=40)
        except Exception:
            p.kill()
        return out
    for _ in range(n):
        if reset == "ucinewgame":
            send("ucinewgame")
            send("isready")
            until("readyok", [])
        elif reset == "clearhash":
            send("setoption name Clear Hash")
            send("isready")
            until("readyok", [])
        send("position fen " + fen)
        send("isready")
        b = []
        until("readyok", b)
        send(go)
        until("bestmove", b)
        out.append(parse([l for l in b if l.startswith("info depth")]))
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    return out


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        ("mate1_h99", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1"),
        ("mate1_h100", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"),
        ("KQvK_h100", "8/5K2/7Q/4k3/8/8/8/8 w - - 100 1"),
    ]
    lines = ["cold vs warm on the numbers PATCH_SUMMARY_fifty_move.md quotes",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "go line: 'go depth 6' everywhere; no setoption except the Clear Hash series",
             "option lines sent: 'setoption name Clear Hash' (no value) in the CHASH series only",
             ""]
    lines.append("board\tmode\tsearch1\tsearch2\tsearch3\tstable")
    rows = []
    for name, fen in boards:
        c = [cold(exe, fen) for _ in range(3)]
        w = series(exe, fen, None)
        u = series(exe, fen, "ucinewgame")
        ch = series(exe, fen, "clearhash")
        for mode, seq in (("COLD 3 processes", c), ("WARM 1 process", w),
                          ("UNEW ucinewgame", u), ("CHASH ClearHash", ch)):
            vals = ["%s/%s" % (r["score"], r["nodes"]) for r in seq]
            stable = len(set(vals)) == 1
            rows.append({"board": name, "mode": mode, "values": vals, "stable": stable})
            lines.append("%s\t%s\t%s\t%s" % (name, mode, "\t".join(vals),
                                             "YES" if stable else "NO  <-- differs"))
            print("%-11s %-18s %s  %s" % (name, mode, "  ".join(vals),
                                          "stable" if stable else "DIFFERS"), flush=True)
    (out / "cold_warm.json").write_text(json.dumps(rows, indent=1))
    (out / "cold_warm.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
