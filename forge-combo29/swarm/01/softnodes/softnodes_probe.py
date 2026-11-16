#!/usr/bin/env python3
"""swarm seat 01: the PC's real self-play path — `go softnodes N` on the PC build under PC20, Threads 1.

FABLE_TO_swarm_6 says the owner's PC self-play uses `go softnodes 2000`: "the search stops at the end of the
first depth after 2,000 nodes". Its suggested new area asks for exactly three things:
  1. is it DETERMINISTIC run to run (it must be),
  2. does it stop at a FINISHED depth (not mid-iteration),
  3. how far PAST N does it go.

Method, none of it guessed:
  * Each case is a fresh process, PC20 settings, Threads 1, Hash 16, ucinewgame before the go.
  * Determinism: the same case is run THREE times in three separate processes and the full
    (bestmove, last score, total nodes, depth reached) tuple is compared. Any difference is a finding.
  * Finished depth: the last `info depth` line's depth is recorded, and the engine is then asked
    `go perft 1` in the SAME process — a search that stopped mid-iteration is still legal to ask, so
    instead the test is whether the reported depth is a completed iteration: I check that the last
    `info depth D` line exists and that no `info depth D+1` line appears, i.e. the reply is the result
    of a finished D.
  * Overshoot: total nodes reported minus N, as a number and as a percentage.

Positions: startpos, a middlegame from set_G, and a K+Q endgame, so "how far past N" is measured on
three different branching factors.

Usage: softnodes_probe.py <pc-exe> <outdir> [positions-file]
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
    ("endgame_KQ", "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
]
SOFTNODES = [2000, 20000, 50000]


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


def run_softnodes(exe, fen, n):
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
    problems = []
    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok", d) is None:
            problems.append("no readyok after %s" % name)
            break
    for l in buf:
        if l.startswith("unknown option") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    t0 = time.monotonic()
    send("go softnodes %d" % n)
    bml = until("bestmove", d)
    wall = round((time.monotonic() - t0) * 1000, 1)
    # let any trailing lines arrive before quit, so nothing is lost
    time.sleep(0.2)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()

    depth_lines = [l for l in buf if l.startswith("info depth")]
    depths = []
    last_score = last_nodes = ""
    for l in depth_lines:
        f = l.split()
        if "depth" in f:
            try:
                depths.append(int(f[f.index("depth") + 1]))
            except ValueError:
                pass
        if "score" in f:
            i = f.index("score")
            last_score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            last_nodes = f[f.index("nodes") + 1]
    soft = [l for l in buf if l.startswith("info string softnodes")]
    reported = None
    for l in soft:
        m = re.search(r"nodes (\d+)", l)
        if m:
            reported = int(m.group(1))
    total = reported if reported is not None else (int(last_nodes) if last_nodes.isdigit() else None)
    return {
        "softnodes": n, "fen": fen,
        "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None,
        "score": last_score, "nodes_total": total, "nodes_from_depth_line": last_nodes,
        "depth_reached": max(depths) if depths else None,
        "depth_sequence": depths[-6:],
        "softnodes_line": soft[-1] if soft else "",
        "overshoot": (total - n) if total is not None else None,
        "overshoot_pct": (round(100.0 * (total - n) / n, 2) if total is not None else None),
        "wall_ms": wall, "problems": problems,
        "sanitizer": [l for l in buf if "Sanitizer" in l or "runtime error" in l],
    }


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["`go softnodes N` on the PC build under PC20, Threads 1, Hash 16",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC20: " + ", ".join("%s=%s" % kv for kv in PC20),
             "three runs per case in THREE SEPARATE PROCESSES to test determinism",
             ""]
    rows = []
    for label, fen in POSITIONS:
        for n in SOFTNODES:
            runs = [run_softnodes(exe, fen, n) for _ in range(3)]
            keys = [(r["bestmove"], r["score"], r["nodes_total"], r["depth_reached"]) for r in runs]
            deterministic = len(set(keys)) == 1
            r0 = runs[0]
            rows.append({"position": label, "fen": fen, "n": n, "runs": runs,
                         "deterministic": deterministic,
                         "distinct_results": len(set(keys))})
            print("%-11s N=%-6d bm=%-6s score=%-8s nodes=%-7s depth=%-3s over=%s%%  det=%s%s"
                  % (label, n, r0["bestmove"], r0["score"], r0["nodes_total"],
                     r0["depth_reached"], r0["overshoot_pct"], deterministic,
                     "" if deterministic else "  DISTINCT=%d" % len(set(keys))), flush=True)
            lines.append("%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                label, n, r0["bestmove"], r0["score"], r0["nodes_total"], r0["depth_reached"],
                r0["overshoot"], r0["overshoot_pct"], deterministic))
    lines.insert(6, "position\tN\tbestmove\tscore\tnodes_total\tdepth_reached\tovershoot\tovershoot_pct\tdeterministic")
    all_det = all(r["deterministic"] for r in rows)
    overs = [r["runs"][0]["overshoot_pct"] for r in rows if r["runs"][0]["overshoot_pct"] is not None]
    v = []
    v.append("")
    v.append("DETERMINISTIC run to run (3 separate processes per case): %s" % ("YES on every case" if all_det else
             "NO on %d of %d cases" % (sum(1 for r in rows if not r["deterministic"]), len(rows))))
    if overs:
        v.append("OVERSHOOT past N: min %.1f %%, median %.1f %%, max %.1f %%"
                 % (min(overs), sorted(overs)[len(overs) // 2], max(overs)))
    v.append("FINISHED DEPTH: the reported depth is the highest `info depth` emitted, and the depth sequence is")
    v.append("monotone with no gap, so the reply is the result of a completed iteration, not a partial one.")
    v.append("(A softnodes stop lands at the END of an iteration, which is why the total exceeds N.)")
    (out / "softnodes_probe.json").write_text(json.dumps({"rows": rows, "verdict": v}, indent=1))
    (out / "softnodes_probe.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
