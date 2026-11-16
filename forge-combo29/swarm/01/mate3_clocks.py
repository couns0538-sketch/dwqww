#!/usr/bin/env python3
"""swarm seat 01: mate-in-3 under the CLOCK path — same board for base, my patch and seat 12's patch,
plus the halfmove-0 control.

The question the coordinator asked: does the clock path lose mate-in-3 the SAME way it loses mate-in-1?
Mate-in-1 at halfmove 100 returned 0 nodes (root adjudicated before any search, so the stop logic never
ran). The gameplay run showed mate-in-3 at halfmove 99 returning `cp 0` with 1728 nodes and at halfmove 100
`cp 0` with 0 nodes — i.e. TWO different signatures. This script pins them down.

Board: 8/8/8/8/2K4Q/8/8/1k6 w - - H 1  (forced mate in 3 plies, verified by exhaustive search).
Controls: the same board at halfmove 0 (no claim possible), with both `go depth` and the clock commands.

Usage: mate3_clocks.py <base-exe> <mine-exe> <s12-exe> <outdir>
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
# The FIRST board (8/8/8/8/2K4Q/8/8/1k6) mates in 3 plies but every white move is quiet, so the counter
# reaches 100 after it and Black simply CLAIMS the draw. cp 0 is therefore CORRECT chess on that board and
# my earlier S-F19 reading of it was wrong. This board is the discriminating one: the mating line starts
# with the PAWN move h6h7, which RESETS the fifty-move counter, so no claim is available and the mate IS
# forceable. Verified with python-chess (forced mate in 3 plies, first move a pawn move).
BOARD = "8/3K4/7P/8/8/7k/8/6Q1 w - - %d 1"


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
    if until("readyok") is None:
        p.kill()
        return {"score": "", "nodes": "", "bestmove": None, "depths": 0, "error": "no readyok"}
    send(go)
    bml = until("bestmove")
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes,
            "bestmove": (bml.split()[1] if bml else None), "depths": len(dl)}


def main():
    base, mine, s12, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    exes = [("base(unpatched)", base), ("mine", mine), ("seat12", s12)]
    hms = [0, 99, 100]
    gos = ["go depth 12", "go wtime 1000 btime 1000", "go movetime 500", "go nodes 200000"]
    lines = ["mate-in-3 under the clock path: base vs my patch vs seat 12's patch, plus the halfmove-0 control",
             "board: " + BOARD + "  (forced mate in 3 plies whose FIRST move h6h7 is a PAWN move, so the",
             "fifty-move counter resets and no draw claim is available; verified by exhaustive search)",
             "NOTE the earlier board 8/8/8/8/2K4Q/8/8/1k6 is NOT discriminating: its mating moves are all",
             "quiet, the counter reaches 100 after White's move, and Black claims - cp 0 is correct there."]
    for label, exe in exes:
        lines.append("%-15s %s sha256 %s" % (label, exe,
                                            hashlib.sha256(Path(exe).read_bytes()).hexdigest()))
    lines.append("option lines sent: NONE (every case is a fresh process)")
    lines.append("")
    lines.append("halfmove\tgo\tbase score/nodes/bm\tmine score/nodes/bm\tseat12 score/nodes/bm\tsignature")
    rows = []
    for hm in hms:
        fen = BOARD % hm
        for go in gos:
            got = {}
            for label, exe in exes:
                got[label] = run(exe, fen, go)
            def fmt(d):
                return "%s / %s / %s" % (d["score"], d["nodes"], d["bestmove"])
            # signature: does the same answer appear on all three builds?
            vals = {label: (got[label]["score"], got[label]["nodes"]) for label, _ in exes}
            uniq = set(vals.values())
            if len(uniq) == 1:
                sig = "all three agree"
            else:
                sig = "DIFFERS between builds"
            if all(v[1] == "0" for v in vals.values()):
                sig += " [0 nodes = root adjudicated before any search]"
            elif all("cp 0" in v[0] for v in vals.values()) and all(v[1] not in ("0", "") for v in vals.values()):
                sig += " [searched, still cp 0: lost INSIDE the search]"
            rows.append({"halfmove": hm, "go": go, "results": got, "signature": sig})
            lines.append("%d\t%s\t%s\t%s\t%s\t%s" % (hm, go, fmt(got["base(unpatched)"]),
                                                    fmt(got["mine"]), fmt(got["seat12"]), sig))
            print("H=%-4d %-26s base %-18s mine %-18s s12 %-18s %s"
                  % (hm, go, fmt(got["base(unpatched)"]), fmt(got["mine"]),
                     fmt(got["seat12"]), sig), flush=True)
    (out / "mate3_clocks.json").write_text(json.dumps(rows, indent=1))
    (out / "mate3_clocks.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
