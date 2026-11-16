#!/usr/bin/env python3
"""swarm seat 01: the other two paths FABLE_TO_swarm_6 names as the PC's strength matches —
`go nodes` 20000/50000/250000 and the clock `6s + 0.06`.

Questions that decide whether these paths are trustworthy for measurement, all with fresh processes,
PC20, Threads 1, Hash 16:
  * `go nodes N`: is the total exactly N? (A hard budget should stop AT N, unlike softnodes.)
  * clock `wtime 6000 btime 6000 winc 60 binc 60`: how much of the 6 s is actually used, does it stay
    under the budget, and is the answer deterministic? A clock search cannot be node-deterministic, so
    for it I measure the WALL-TIME distribution and whether the MOVE is stable across runs, which is
    what a match needs.

Determinism for the clock: 5 runs per position; record move, wall time, nodes and the spread.

Usage: nodes_and_clock.py <pc-exe> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 600.0

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]

POSITIONS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("midgame", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G_pos1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
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

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    d = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", d)
    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    t0 = time.monotonic()
    send(go)
    bml = until("bestmove", d)
    wall = round((time.monotonic() - t0) * 1000, 1)
    time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    dls = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    depth = None
    if dls:
        f = dls[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
        if "depth" in f:
            depth = int(f[f.index("depth") + 1])
    # the clock answer often arrives as a final line with time/nodes
    for l in reversed(dls):
        if " nodes " in l:
            m = re.search(r"\bnodes (\d+)", l)
            if m:
                nodes = m.group(1)
                break
    return {"go": go, "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None,
            "score": score, "nodes": nodes, "depth": depth, "wall_ms": wall}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["`go nodes` and the 6s+0.06 clock on the PC build under PC20, Threads 1, Hash 16",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             ""]
    rows = []

    # A: go nodes -- a HARD budget, expected to stop AT N
    lines.append("A. go nodes N (hard budget):")
    lines.append("position\tN\tbestmove\tnodes_reported\texact\tscore\twall_ms")
    for label, fen in POSITIONS[:2]:
        for n in (20000, 50000, 250000):
            r = run(exe, fen, "go nodes %d" % n)
            exact = (r["nodes"] == str(n))
            rows.append({"kind": "nodes", "position": label, "n": n, **r, "exact": exact})
            print("nodes %-9s N=%-7d bm=%-6s reported=%-8s exact=%-5s %s"
                  % (label, n, r["bestmove"], r["nodes"], exact, r["score"]), flush=True)
            lines.append("%s\t%d\t%s\t%s\t%s\t%s\t%s"
                         % (label, n, r["bestmove"], r["nodes"], exact, r["score"], r["wall_ms"]))

    # B: the clock: is the MOVE stable and does it stay under budget?
    lines.append("")
    lines.append("B. clock `wtime 6000 btime 6000 winc 60 binc 60`, 5 runs per position:")
    lines.append("position\trun\tbestmove\twall_ms\tnodes\tscore\tdepth\twithin_budget")
    clocks = []
    for label, fen in POSITIONS[:2]:
        for k in range(5):
            r = run(exe, fen, "go wtime 6000 btime 6000 winc 60 binc 60")
            within = r["wall_ms"] <= 6000
            clocks.append({"position": label, "run": k + 1, **r, "within": within})
            print("clock %-9s run %d bm=%-6s wall=%-8s nodes=%-8s %s within=%s"
                  % (label, k + 1, r["bestmove"], r["wall_ms"], r["nodes"], r["score"], within),
                  flush=True)
            lines.append("%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s"
                         % (label, k + 1, r["bestmove"], r["wall_ms"], r["nodes"], r["score"],
                            r["depth"], within))
        moves = {c["bestmove"] for c in clocks if c["position"] == label}
        walls = [c["wall_ms"] for c in clocks if c["position"] == label]
        lines.append("  %s: %d distinct move(s) over 5 runs, wall min %.0f ms max %.0f ms"
                     % (label, len(moves), min(walls), max(walls)))

    v = []
    v.append("")
    node_rows = [r for r in rows if r["kind"] == "nodes"]
    exact_all = all(r["exact"] for r in node_rows)
    v.append("A. go nodes: reported total == N on %d of %d cases -> %s"
             % (sum(1 for r in node_rows if r["exact"]), len(node_rows),
                "a HARD budget that stops exactly at N, unlike softnodes" if exact_all
                else "NOT exact on every case (see the table)"))
    for label in {c["position"] for c in clocks}:
        sub = [c for c in clocks if c["position"] == label]
        moves = {c["bestmove"] for c in sub}
        walls = [c["wall_ms"] for c in sub]
        over = [c for c in sub if not c["within"]]
        v.append("B. clock %s: %d/%d runs within 6000 ms; wall %.0f..%.0f ms; %d distinct move(s) -> %s"
                 % (label, len(sub) - len(over), len(sub), min(walls), max(walls), len(moves),
                    "stable move" if len(moves) == 1 else "MOVE VARIES RUN TO RUN"))
    v.append("")
    v.append("READING: `go nodes` is the reproducible budget for matches (exact), while the clock path is")
    v.append("reproducible only in its MOVE, not its node count or wall time -- which is expected and is why")
    v.append("a match that wants reproducible results should use nodes or softnodes, as file 6 says the PC does.")
    (out / "nodes_and_clock.json").write_text(json.dumps({"go_nodes": node_rows,
                                                          "clock": clocks, "verdict": v}, indent=1))
    (out / "nodes_and_clock.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
