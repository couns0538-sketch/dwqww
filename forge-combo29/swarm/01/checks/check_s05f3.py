#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 05's S-F3 (the fifty-move draw is applied about 9 plies early).

Seat 05's claim, verbatim from its FINDINGS.md:
  "The fifty-move draw is applied about 9 plies early: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at `go depth 10`
   scores `cp 472` for H=0..75, `cp 314` at H=90, then exactly `cp 0` from H=91"

I wrote this harness myself from that sentence; I did not read or copy seat 05's threshold_probe.py.
Method: for each halfmove value, a fresh process, `position fen`, `isready` read to readyok, `go depth 10`,
read to bestmove, and the LAST `info depth` line is recorded. A control is included: the same sweep on a
K+Q board (the second board seat 05 names) and on a position where the engine should NOT show a cliff.

Usage: check_s05f3.py <exe> <outdir>
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


def one(exe, fen, go="go depth 10"):
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
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    bm = None
    depth_lines = []
    if not refused:
        send(go)
        bml = until("bestmove")
        if bml:
            bm = bml.split()[1]
        depth_lines = [l for l in buf if l.startswith("info depth")]
        time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    score = ""
    nodes = ""
    if depth_lines:
        f = depth_lines[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"fen": fen, "refused": bool(refused), "bestmove": bm, "score": score,
            "nodes": nodes, "n_depth_lines": len(depth_lines),
            "sanitizer": [l for l in buf if "Sanitizer" in l or "runtime error" in l]}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        # seat 05's first board, verbatim
        ("KR_vs_k", "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"),
        # seat 05's second board, verbatim
        ("KQ_vs_k", "8/5K2/7Q/4k3/8/8/8/8 w - - %d 1"),
        # control that must NOT show the same cliff at 91: a drawn-looking position where the
        # engine has nothing to lose (K v K is an immediate draw)
        ("K_vs_K", "8/8/4k3/8/8/3K4/8/8 w - - %d 1"),
    ]
    halfmoves = [0, 50, 75, 80, 85, 88, 89, 90, 91, 92, 95, 98, 99, 100]
    results = []
    lines = ["CHECK of seat 05 S-F3: fifty-move draw applied early?",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l))
    lines.append("option lines sent: NONE")
    lines.append("go line: 'go depth 10' for every case")
    lines.append("")
    header = "board\thalfmove\tscore\tnodes\tbestmove\tn_depth_lines"
    lines.append(header)
    for name, tmpl in boards:
        for hm in halfmoves:
            fen = tmpl % hm
            r = one(exe, fen)
            r["board"] = name
            r["halfmove"] = hm
            results.append(r)
            lines.append("%s\t%d\t%s\t%s\t%s\t%d" % (name, hm, r["score"], r["nodes"],
                                                     r["bestmove"], r["n_depth_lines"]))
            print("%-10s H=%-4d score=%-10s nodes=%-10s bm=%s"
                  % (name, hm, r["score"], r["nodes"], r["bestmove"]), flush=True)

    # verdict computed from the data: first halfmove at which the score becomes exactly 0
    verdict = []
    for name, _ in boards:
        rows = [r for r in results if r["board"] == name]
        zero_at = next((r["halfmove"] for r in rows if r["score"] in ("cp 0",)), None)
        nonzero_below = [r["halfmove"] for r in rows if r["halfmove"] < (zero_at or 999)
                         and r["score"] not in ("cp 0",)]
        verdict.append("%s: first exactly-zero score at halfmove %s; non-zero at %s"
                       % (name, zero_at, nonzero_below[:8]))
        if name == "KR_vs_k":
            seat05_said_91 = (zero_at == 91)
            verdict.append("   seat 05 said 91 -> %s" % ("CONFIRMED on that number" if seat05_said_91
                                                         else "NOT reproduced (got %s)" % zero_at))

    (out / "check_s05f3.json").write_text(json.dumps(results, indent=1))
    text = "\n".join(lines + [""] + verdict) + "\n"
    (out / "check_s05f3.txt").write_text(text)
    print("")
    print("\n".join(verdict))


if __name__ == "__main__":
    main()
