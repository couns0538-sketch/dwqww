#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 05's S-F49 — the depth reached by each of the owner's real controls.

Seat 05's claim, verbatim:
  "On the same boards the owner's real controls rank: softnodes 2000 (d7-8) < nodes 20000 (d10-11) <
   nodes 50000 (d12-14) < nodes 250000 (d15-17) < clock 6s+0.06 (d18) < movetime 6000 (d24-28). PC r15 +
   PC20, Threads 1, Hash 16, OwnBook false, three boards (startpos, G0, deep middlegame). The clock path is
   NOT the weakest control ... A caveat I found by re-testing: the clock row CAN vary under CPU contention —
   running it in the same batch as the node rows gave d18/784,328 then d17/542,082 twice, but 10 SOLO runs
   give depth 18 / 784,328 nodes / move a1c1 in 10 of 10."

What this checks, on the same build and settings:
  1. the ORDER of the ladder on my own boards — is it monotone in budget?
  2. their contention caveat: the clock row run SOLO, 5 times, and then run interleaved with a second
     engine process on the same machine — does the depth drop?

The clock row is the interesting one: if it only ranks as claimed when the machine is idle, then for the
owner's matches (one process per game, but several games in parallel is plausible) the ranking may not hold.

Usage: check_s05f49.py <pc-exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 900.0

OPTS = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"),
        ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

BOARDS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G0", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("deep_mid", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
]
LADDER = [("softnodes 2000", "go softnodes 2000"), ("nodes 20000", "go nodes 20000"),
          ("nodes 50000", "go nodes 50000"), ("nodes 250000", "go nodes 250000"),
          ("clock 6000", "go wtime 6000 btime 6000 winc 60 binc 60"),
          ("movetime 6000", "go movetime 6000")]


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
    for name, value in OPTS:
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
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=200)
    except Exception:
        p.kill()
    dls = [l for l in buf if l.startswith("info depth")]
    depth = None
    score = ""
    for l in dls:
        f = l.split()
        if "depth" in f:
            try:
                depth = int(f[f.index("depth") + 1])
            except ValueError:
                pass
        if " score " in l:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
    return {"go": go, "depth": depth, "score": score, "wall_ms": wall,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["CHECK of seat 05's S-F49: the depth ladder of the owner's real controls",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC20, Threads 1, Hash 16, OwnBook false; fresh process per row", ""]
    lines.append("board\tcontrol\tdepth\tscore\twall_ms\tbestmove")
    rows = []
    for label, fen in BOARDS:
        depths = []
        for name, go in LADDER:
            r = run(exe, fen, go)
            rows.append({"board": label, "control": name, **r})
            depths.append((name, r["depth"]))
            print("%-10s %-16s depth=%-3s %-9s %8sms %s"
                  % (label, name, r["depth"], r["score"], r["wall_ms"], r["bestmove"]), flush=True)
            lines.append("%s\t%s\t%s\t%s\t%s\t%s" % (label, name, r["depth"], r["score"],
                                                     r["wall_ms"], r["bestmove"]))
        mono = all(depths[i][1] is not None and depths[i + 1][1] is not None and
                   depths[i][1] <= depths[i + 1][1] for i in range(len(depths) - 1))
        rows.append({"board": label, "monotone": mono})
        print("%-10s ladder monotone: %s" % (label, mono), flush=True)

    # their contention caveat: the clock row SOLO, then with a concurrent engine process
    lines.append("")
    lines.append("contention test on the clock row (startpos), SOLO then with a second engine process running:")
    lines.append("mode\trun\tdepth\twall_ms\tbestmove")
    solo = [run(exe, BOARDS[0][1], "go wtime 6000 btime 6000 winc 60 binc 60") for _ in range(5)]
    for i, r in enumerate(solo):
        lines.append("solo\t%d\t%s\t%s\t%s" % (i + 1, r["depth"], r["wall_ms"], r["bestmove"]))
        print("solo   run %d depth=%-3s wall=%-7s bm=%s" % (i + 1, r["depth"], r["wall_ms"], r["bestmove"]),
              flush=True)
    # a concurrent load: a second engine doing a long search at the same time
    load = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, cwd="/tmp")
    try:
        load.stdin.write(b"uci\nsetoption name Threads value 1\nisready\n"
                         b"position startpos\ngo depth 30\n")
        load.stdin.flush()
        time.sleep(0.5)
        busy = [run(exe, BOARDS[0][1], "go wtime 6000 btime 6000 winc 60 binc 60") for _ in range(3)]
    finally:
        try:
            load.kill()
        except Exception:
            pass
    for i, r in enumerate(busy):
        lines.append("loaded\t%d\t%s\t%s\t%s" % (i + 1, r["depth"], r["wall_ms"], r["bestmove"]))
        print("loaded run %d depth=%-3s wall=%-7s bm=%s" % (i + 1, r["depth"], r["wall_ms"], r["bestmove"]),
              flush=True)

    v = []
    v.append("")
    mono_all = all(r.get("monotone") for r in rows if "monotone" in r)
    v.append("LADDER: monotone in budget on %s of %d boards."
             % (sum(1 for r in rows if r.get("monotone")), len(BOARDS)))
    if mono_all:
        v.append("  So the ORDER seat 05 reports reproduces: each control is at least as deep as the one before.")
    v.append("CONTENTION: the clock row gave depth %s solo (5 runs: %s) and depth %s under load (3 runs: %s)."
             % (solo[0]["depth"], [r["depth"] for r in solo], busy[0]["depth"], [r["depth"] for r in busy]))
    if len({r["depth"] for r in solo}) == 1 and len({r["depth"] for r in busy}) == 1 and \
            solo[0]["depth"] != busy[0]["depth"]:
        v.append("  Seat 05's caveat is CONFIRMED: the clock row is stable solo and DROPS under contention,")
        v.append("  so a clock-depth measurement taken alongside other searches is not comparable with a solo one.")
    elif len({r["depth"] for r in solo}) == 1 and len({r["depth"] for r in busy}) == 1:
        v.append("  The clock row was stable both solo and under load on this machine, so the contention effect")
        v.append("  seat 05 saw did not reproduce here (their load may have been heavier than one extra process).")
    else:
        v.append("  The clock row varied even solo on this machine, so the ranking's clock cell is not usable")
        v.append("  as a fixed number here.")
    (out / "check_s05f49.json").write_text(json.dumps({"ladder": rows, "solo": solo, "loaded": busy,
                                                       "verdict": v}, indent=1))
    (out / "check_s05f49.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
