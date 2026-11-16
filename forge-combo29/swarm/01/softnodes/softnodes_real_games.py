#!/usr/bin/env python3
"""swarm seat 01: does the softnodes STAIRCASE have STABLE band boundaries across REAL GAME positions?

The startpos staircase (S-F51) showed bands whose boundaries depend on each iteration's node count. The
owner's self-play uses real game positions, so the practical question is whether a FIXED N can be recommended
or whether each position needs its own staircase read.

Method: five positions from set_G (the PC's real-game set, in file order), ten budgets each, PC20, Threads 1,
Hash 16, fresh process per run. For each position I record, per budget, the (depth, bestmove, score) and the
total nodes; then a band is a maximal run of ascending budgets with the same (depth, bestmove, score).

The answer is the SPREAD of band boundaries across the five positions:
  * if a given (depth) first appears at budgets that differ by a factor of ~2 between positions, a fixed N is
    not safe and the advice is "read the staircase per position";
  * if the boundaries cluster within a narrow factor, a single fixed N can be recommended.

Usage: softnodes_real_games.py <pc-exe> <g-epd> <outdir> [n-positions]
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

TIMEOUT = 900.0
BUDGETS = [1000, 2000, 3000, 4000, 6000, 8000, 12000, 16000, 20000, 30000]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]


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


def run(exe, fen, n):
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
    send("go softnodes %d" % n)
    bml = until("bestmove", d)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    dls = [l for l in buf if l.startswith("info depth")]
    score = ""
    for l in dls:
        if " score " in l:
            f = l.split()
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
    total = None
    for l in buf:
        if l.startswith("info string softnodes"):
            m = re.search(r"nodes (\d+)", l)
            if m:
                total = int(m.group(1))
    depth = None
    if dls:
        f = dls[-1].split()
        if "depth" in f:
            try:
                depth = int(f[f.index("depth") + 1])
            except ValueError:
                pass
    return {"n": n, "depth": depth, "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None,
            "score": score, "total": total}


def main():
    exe = sys.argv[1]
    gpath = sys.argv[2]
    out = Path(sys.argv[3])
    howmany = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    out.mkdir(parents=True, exist_ok=True)
    positions = []
    for line in open(gpath):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            positions.append(" ".join(parts[:4]) + " 0 1")
        if len(positions) >= howmany:
            break

    lines = ["softnodes staircase on REAL GAME positions (set_G), per-position band boundaries",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC20, Threads 1, Hash 16; budgets: %s" % BUDGETS,
             "positions: first %d of %s" % (howmany, gpath),
             ""]
    per_position = []
    for idx, fen in enumerate(positions):
        rows = []
        for n in BUDGETS:
            r = run(exe, fen, n)
            rows.append(r)
            print("pos%d N=%-6d depth=%-3s bm=%-6s %-9s total=%s"
                  % (idx + 1, n, r["depth"], r["bestmove"], r["score"], r["total"]), flush=True)
        # bands: maximal runs of ascending N with identical (depth,bestmove,score)
        bands = []
        for r in rows:
            key = (r["depth"], r["bestmove"], r["score"])
            if bands and bands[-1]["key"] == key:
                bands[-1]["ns"].append(r["n"])
            else:
                bands.append({"key": key, "ns": [r["n"]]})
        per_position.append({"index": idx + 1, "fen": fen, "rows": rows,
                             "bands": [{"key": list(b["key"]), "ns": b["ns"]} for b in bands]})
        lines.append("pos%d %s" % (idx + 1, fen))
        for b in bands:
            lines.append("   N %-22s depth %-3s %s  %s" % (b["ns"], b["key"][0], b["key"][1], b["key"][2]))

    # the cross-position question: for each DEPTH, at what budget does each position first reach it?
    depths = sorted({r["depth"] for p in per_position for r in p["rows"] if r["depth"] is not None})
    lines.append("")
    lines.append("FIRST BUDGET AT WHICH EACH DEPTH APPEARS, per position (the band boundary):")
    lines.append("depth\t" + "\t".join("pos%d" % (i + 1) for i in range(len(per_position))) + "\tspread_factor")
    boundary_table = []
    for d in depths:
        firsts = []
        for p in per_position:
            hit = next((r["n"] for r in p["rows"] if r["depth"] is not None and r["depth"] >= d), None)
            firsts.append(hit)
        got = [f for f in firsts if f]
        spread = (max(got) / min(got)) if len(got) > 1 else None
        boundary_table.append({"depth": d, "firsts": firsts, "spread": spread})
        lines.append("%d\t%s\t%s" % (d, "\t".join(str(f) if f else "-" for f in firsts),
                                     ("%.2f" % spread) if spread else "-"))

    spreads = [b["spread"] for b in boundary_table if b["spread"]]
    v = []
    v.append("")
    if spreads:
        v.append("BOUNDARY SPREAD across the %d positions (max/min of the first budget reaching a depth):"
                 % len(per_position))
        v.append("   min %.2f, median %.2f, max %.2f  (1.00 = perfectly stable across positions)"
                 % (min(spreads), sorted(spreads)[len(spreads) // 2], max(spreads)))
        if max(spreads) <= 1.5:
            v.append("ADVICE: STABLE ENOUGH FOR A FIXED VALUE. The boundaries move by at most %.2fx across"
                     % max(spreads))
            v.append("these real positions, so one N can be named for self-play; the table above gives it.")
        else:
            v.append("ADVICE: READ THE STAIRCASE PER POSITION. The boundaries move by up to %.2fx across real"
                     % max(spreads))
            v.append("positions, so a single fixed N is not safe; the per-position bands above are the tool.")
    # also: within one position, how much does the total vary for the same depth?
    v.append("")
    v.append("WITHIN a position the total is constant inside a band (that is what makes the staircase), and")
    v.append("the ratio total/N therefore depends only on where N falls inside the band - so a budget should")
    v.append("be placed at or just above a band's FIRST budget, not at its last.")
    (out / "softnodes_real_games.json").write_text(json.dumps(
        {"budgets": BUDGETS, "positions": per_position, "boundary_table": boundary_table,
         "verdict": v}, indent=1))
    (out / "softnodes_real_games.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
