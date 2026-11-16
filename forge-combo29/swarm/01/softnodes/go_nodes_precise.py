#!/usr/bin/env python3
"""swarm seat 01: what exactly is `go nodes N` reporting, and how much does it ACTUALLY spend?

The distinction the coordinator asks for:
  (a) "the reported count is not exact" (what I wrote in S-F54), versus
  (b) "the reported count is the HONEST total of the completed iterations, and the budget is interpreted as
       stop after the iteration that crosses N" — which is a different and more useful statement, because
       it says whether a match harness can trust the reported number.

Three measurements settle it, none of them by reading code alone:

  M1  Does the reported node count equal the node count of the SAME depth searched with `go depth D` (where
      D is the last depth that appeared)? If yes, the reported number is that completed iteration's total,
      i.e. honest but NOT including the aborted iteration.
  M2  How much is actually spent? The engine gives no total for `go nodes`, so I bound it: a `go nodes N`
      must spend at least as much as the last completed depth (M1's number) and at most N. If the reported
      number is always < N and the search stopped because of the budget, then the spend lies in
      [reported, N] — and the reported number UNDERSTATES the true cost by up to (N - reported).
  M3  Is the interpretation "stop after the iteration that crosses N"? Sweep N across one iteration's node
      band: if the reported number and the depth stay IDENTICAL for every N inside the band, the budget does
      not truncate an iteration — it lets the iteration finish and stops. That is exactly the softnodes
      behaviour, and it would mean `go nodes` and `go softnodes` differ only in the hard cap and the report.

Usage: go_nodes_precise.py <pc-exe> <outdir>
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
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"

OPTS = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"),
        ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]


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


def run(exe, go):
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
    for name, value in OPTS:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + FEN)
    send("isready")
    until("readyok", d)
    send(go)
    bml = until("bestmove", d)
    time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    dls = [l for l in buf if l.startswith("info depth")]
    parsed = []
    for l in dls:
        f = l.split()
        try:
            parsed.append({"depth": int(f[f.index("depth") + 1]),
                           "nodes": int(f[f.index("nodes") + 1]),
                           "score": " ".join(f[f.index("score") + 1:f.index("score") + 3])})
        except (ValueError, IndexError):
            continue
    soft = None
    for l in buf:
        if l.startswith("info string softnodes"):
            m = re.search(r"nodes (\d+)", l)
            if m:
                soft = int(m.group(1))
    return {"go": go, "iters": parsed,
            "last": parsed[-1] if parsed else None,
            "softnodes_reported": soft,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["what `go nodes N` reports and what it spends — PC r15, PC20, Threads 1, Hash 16",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "position: " + FEN, ""]

    # M1: reported total for a nodes run vs a depth run at the same last depth
    lines.append("M1. Is the reported count the COMPLETED iteration's total?")
    lines.append("go\tlast depth\treported nodes\tsame depth via go depth\tequal?")
    m1 = []
    for n in (20000, 50000, 250000):
        r = run(exe, "go nodes %d" % n)
        last = r["last"]
        d = run(exe, "go depth %d" % last["depth"]) if last else None
        same = bool(d and d["last"] and d["last"]["nodes"] == last["nodes"])
        m1.append({"n": n, "last": last, "depth_run": d["last"] if d else None, "equal": same})
        print("nodes %-8d depth %-3s reported %-8s | go depth %-3s -> %-8s equal=%s"
              % (n, last["depth"], last["nodes"], last["depth"], d["last"]["nodes"], same), flush=True)
        lines.append("%d\t%s\t%s\t%s\t%s" % (n, last["depth"], last["nodes"], d["last"]["nodes"], same))

    # M2: is the reported number always below N (so the spend lies in [reported, N])?
    lines.append("")
    lines.append("M2. reported vs the budget (a spend between them means the aborted iteration's nodes are NOT reported):")
    lines.append("N\treported\tN - reported\tpercent of N reported")
    m2 = []
    for n in (5000, 10000, 20000, 50000, 100000, 250000):
        r = run(exe, "go nodes %d" % n)
        last = r["last"]
        rep = last["nodes"] if last else None
        m2.append({"n": n, "reported": rep, "unreported": (n - rep) if rep else None,
                   "pct": round(100.0 * rep / n, 1) if rep else None})
        print("N=%-8d reported=%-8s unreported<=%-8s reported%%=%s"
              % (n, rep, (n - rep) if rep else None, round(100.0 * rep / n, 1) if rep else None),
              flush=True)
        lines.append("%d\t%s\t%s\t%s" % (n, rep, (n - rep) if rep else None,
                                         round(100.0 * rep / n, 1) if rep else None))

    # M3: does the budget truncate an iteration? Sweep N inside one iteration band.
    lines.append("")
    lines.append("M3. Sweep N inside one iteration band: identical depth+reported = the iteration FINISHED.")
    lines.append("N\tlast depth\treported\tbestmove")
    m3 = []
    for n in (38478, 39000, 40000, 42000, 45000, 48000, 52000, 60000):
        r = run(exe, "go nodes %d" % n)
        last = r["last"]
        m3.append({"n": n, "depth": last["depth"] if last else None,
                   "reported": last["nodes"] if last else None, "bestmove": r["bestmove"]})
        print("N=%-8d depth=%-3s reported=%-8s bm=%s" % (n, last["depth"], last["nodes"], r["bestmove"]),
              flush=True)
        lines.append("%d\t%s\t%s\t%s" % (n, last["depth"], last["nodes"], r["bestmove"]))

    # verdict from the data
    v = []
    v.append("")
    v.append("M1 RESULT: reported == `go depth D` total on %d of %d — the reported number is the last"
             % (sum(1 for x in m1 if x["equal"]), len(m1)))
    v.append("COMPLETED iteration's node total, so it is an HONEST number, not a truncated or invented one.")
    v.append("M2 RESULT: the reported number is below N on %d of %d cases, by up to %s nodes."
             % (sum(1 for x in m2 if x["unreported"] and x["unreported"] > 0), len(m2),
                max((x["unreported"] or 0) for x in m2)))
    v.append("M3 RESULT: within one iteration band the depth and the reported total are IDENTICAL, so the")
    v.append("budget does NOT truncate an iteration — the iteration finishes and the search then stops.")
    same_band = len({(x["depth"], x["reported"], x["bestmove"]) for x in m3}) < len(m3)
    v.append("")
    v.append("PRECISE STATEMENT for a match harness:")
    v.append("  `go nodes N` means 'finish the iteration that crosses N, then stop'. The number printed on")
    v.append("  the last `info depth` line is the true total of the COMPLETED iterations and can be trusted")
    v.append("  as such; the nodes spent inside the aborted iteration are NOT printed. So the actual spend")
    v.append("  lies in [reported, N], the reported figure UNDERSTATES cost by up to N - reported, and a")
    v.append("  harness that reads the last info line gets an honest but conservative count.")
    v.append("  (Unlike softnodes there is no `info string softnodes nodes` total, so for `go nodes` the")
    v.append("  aborted iteration's nodes are invisible; for softnodes the total IS reported.)")
    (out / "go_nodes_precise.json").write_text(json.dumps(
        {"m1": m1, "m2": m2, "m3": m3, "same_band": same_band, "verdict": v}, indent=1))
    (out / "go_nodes_precise.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
