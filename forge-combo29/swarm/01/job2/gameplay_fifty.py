#!/usr/bin/env python3
"""swarm seat 01: does the fifty-move root shortcut (S-F5) fire in GAME PLAY, not just in `go depth`?

This is the question that decides whether S-F5 matters to Fable and Opus: my job-2 cases used `go depth 4`,
which always searches. A real game sends clocks (`go wtime ... btime ...`). If a clock-search on a
halfmove>=100 root returns in 0 nodes with a first-legal-move answer, S-F5 costs real games, not only
analysis.

Cases, all at halfmove 100 and 150 and 99 (control), S14 settings applied exactly as the brief lists them:
  a mate-in-one board        6k1/5ppp/8/8/8/8/5PPP/R5K1
  a winning-but-not-mated    8/5K2/7Q/4k3/8/8/8/8
with three clock modes: `go wtime 1000 btime 1000`, `go wtime 10000 btime 10000`, `go movetime 500`.

S14 options are set with `setoption` and each is followed by `isready` read to readyok, as the brief demands.

Usage: gameplay_fifty.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 300.0

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]


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


def run(exe, fen, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefixes, timeout=TIMEOUT):
        d = time.monotonic() + timeout
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            for pre in (prefixes if isinstance(prefixes, tuple) else (prefixes,)):
                if l.startswith(pre):
                    return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    # every setoption followed by isready read to readyok; stop on an unknown/invalid answer
    problems = []
    for name, value in S14:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok") is None:
            problems.append("no readyok after setoption %s" % name)
            break
        for l in buf:
            if l.startswith("unknown option"):
                problems.append("unknown option %s" % name)
            if l.startswith("info string invalid value"):
                problems.append("invalid value for %s" % name)
    send("ucinewgame")
    send("isready")
    if until("readyok") is None:
        problems.append("no readyok after ucinewgame")
    send("position fen " + fen)
    send("isready")
    if until("readyok") is None:
        problems.append("no readyok after position")
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    answered = False
    wall = None
    bm = None
    depth_lines = []
    if not refused and not problems:
        t0 = time.monotonic()
        send(go)
        bml = until("bestmove")
        wall = round((time.monotonic() - t0) * 1000, 1)
        answered = bml is not None
        bm = bml.split()[1] if bml else None
        depth_lines = [l for l in buf if l.startswith("info depth")]
        time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    score = nodes = ""
    if depth_lines:
        f = depth_lines[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"fen": fen, "go": go, "problems": problems, "refused": refused,
            "answered": answered, "bestmove": bm, "score": score, "nodes": nodes,
            "wall_ms": wall, "n_depth_lines": len(depth_lines)}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    boards = [("mate1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - %d 1"),
              ("win_no_mate1", "8/5K2/7Q/4k3/8/8/8/8 w - - %d 1")]
    hms = [99, 100, 150]
    gos = ["go wtime 1000 btime 1000", "go wtime 10000 btime 10000", "go movetime 500"]
    lines = ["does the fifty-move root shortcut fire in GAME PLAY (clock searches)? S14 settings applied",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("option lines sent (each followed by isready read to readyok): "
                 + ", ".join("%s=%s" % kv for kv in S14))
    lines.append("")
    header = "board\thalfmove\tgo\tbestmove\tscore\tnodes\twall_ms\tn_depth_lines\tproblems"
    lines.append(header)
    rows = []
    for label, tmpl in boards:
        for hm in hms:
            fen = tmpl % hm
            for go in gos:
                r = run(exe, fen, go)
                r["board"] = label
                r["halfmove"] = hm
                rows.append(r)
                lines.append("%s\t%d\t%s\t%s\t%s\t%s\t%s\t%d\t%s" % (
                    label, hm, go, r["bestmove"], r["score"], r["nodes"], r["wall_ms"],
                    r["n_depth_lines"], "; ".join(r["problems"]) or "(none)"))
                print("%-12s H=%-4d %-26s bm=%-6s score=%-8s nodes=%-8s %5sms depths=%d %s"
                      % (label, hm, go, r["bestmove"], r["score"], r["nodes"], r["wall_ms"],
                         r["n_depth_lines"], "; ".join(r["problems"]) or ""), flush=True)
    (out / "gameplay_fifty.json").write_text(json.dumps(rows, indent=1))
    (out / "gameplay_fifty.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
