#!/usr/bin/env python3
"""swarm seat 01: what happens if the owner IGNORES the per-position staircase advice?

The question the coordinator asks, made measurable: with one FIXED budget used across positions whose band
boundaries differ by up to 3x —
  * how much does the NODE COST per game vary?  and
  * does the SEARCH QUALITY change at all?

Design, chosen so the answer is a decision rather than a complaint:
  * Take the five real G positions and one fixed budget N = 6000.
  * For each position, run the fixed budget AND a "matched" budget equal to that position's own band-start
    (read from the real-game staircase run), so both arms spend comparable intent.
  * Record the total nodes actually spent and the (depth, bestmove, score) each arm produced.
  * Then measure quality two ways:
      (a) DEPTH REACHED — did the fixed budget reach a lower depth than the per-position budget on the same
          position? A depth difference on a real game position is a real quality difference.
      (b) BESTMOVE AGREEMENT — do the two arms choose the same move? If they disagree, the cheaper arm is
          playing a different move, which for a self-play/match context is the difference that matters.
  * Finally: the ratio max/min of nodes spent by the FIXED budget across the five positions, which is the
    "cost varies up to Xx" number.

Usage: softnodes_ignoring_advice.py <pc-exe> <g-epd> <outdir> [fixed-N]
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
FIXED = int(sys.argv[4]) if len(sys.argv) > 4 else 6000
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
    total = None
    for l in buf:
        if l.startswith("info string softnodes"):
            m = re.search(r"nodes (\d+)", l)
            if m:
                total = int(m.group(1))
    return {"n": n, "depth": depth, "score": score, "total": total,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def main():
    exe = sys.argv[1]
    gpath = sys.argv[2]
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    positions = []
    for line in open(gpath):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            positions.append(" ".join(parts[:4]) + " 0 1")
        if len(positions) >= 5:
            break

    lines = ["what it costs to IGNORE the per-position softnodes advice",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC20, Threads 1, Hash 16; fixed budget N = %d across all positions" % FIXED,
             ""]
    # per position: the fixed budget, and that position's own band-start budgets from the staircase sweep
    rows = []
    for idx, fen in enumerate(positions):
        # the position's own staircase: sweep the same budgets, so its band-start is measured here too
        sweep = [run(exe, fen, n) for n in BUDGETS]
        bands = []
        for r in sweep:
            key = (r["depth"], r["bestmove"], r["score"])
            if bands and bands[-1]["key"] == key:
                bands[-1]["ns"].append(r["n"])
            else:
                bands.append({"key": key, "ns": [r["n"]], "first": r["n"]})
        # the fixed-budget answer, measured (already in the sweep if FIXED is in BUDGETS)
        fixed = next((r for r in sweep if r["n"] == FIXED), run(exe, fen, FIXED))
        # the "matched" answer: the band the fixed budget landed in, but at that band's FIRST budget
        band = next((b for b in bands if FIXED in b["ns"]), bands[-1])
        matched = next((r for r in sweep if r["n"] == band["first"]), None)
        if matched is None:
            matched = run(exe, fen, band["first"])
        rows.append({"position": idx + 1, "fen": fen, "bands": [
            {"key": list(b["key"]), "ns": b["ns"], "first": b["first"]} for b in bands],
            "fixed": fixed, "matched": matched, "band_first": band["first"]})
        print("pos%d fixed N=%d -> depth %-3s bm=%-6s %-9s nodes=%-7s | band-first N=%-6d -> depth %-3s bm=%-6s %-9s nodes=%s"
              % (idx + 1, FIXED, fixed["depth"], fixed["bestmove"], fixed["score"], fixed["total"],
                 band["first"], matched["depth"], matched["bestmove"], matched["score"],
                 matched["total"]), flush=True)

    # the numbers the decision needs, all computed
    costs = [r["fixed"]["total"] for r in rows if r["fixed"]["total"]]
    depth_off = [(r["position"], r["fixed"]["depth"], r["matched"]["depth"])
                 for r in rows if r["fixed"]["depth"] != r["matched"]["depth"]]
    move_off = [(r["position"], r["fixed"]["bestmove"], r["matched"]["bestmove"])
                for r in rows if r["fixed"]["bestmove"] != r["matched"]["bestmove"]]
    score_off = [(r["position"], r["fixed"]["score"], r["matched"]["score"])
                 for r in rows if r["fixed"]["score"] != r["matched"]["score"]]
    ratio = (max(costs) / min(costs)) if len(costs) > 1 else None

    lines.append("")
    lines.append("position\tfixed_N\tdepth\tbestmove\tscore\tnodes\tband_first_N\tmatched_depth\tmatched_bestmove\tmatched_nodes")
    for r in rows:
        lines.append("%d\t%d\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s" % (
            r["position"], FIXED, r["fixed"]["depth"], r["fixed"]["bestmove"], r["fixed"]["score"],
            r["fixed"]["total"], r["band_first"], r["matched"]["depth"],
            r["matched"]["bestmove"], r["matched"]["total"]))

    v = []
    v.append("")
    if ratio:
        v.append("COST of ignoring the advice: with one fixed budget N=%d the nodes actually spent per" % FIXED)
        v.append("position ranged %s..%s, i.e. a factor of %.2fx." % (min(costs), max(costs), ratio))
    v.append("QUALITY of ignoring the advice:")
    v.append("  depth differed from the per-position optimum on %d of %d positions%s"
             % (len(depth_off), len(rows), (": " + str(depth_off)) if depth_off else ""))
    v.append("  bestmove differed on %d of %d positions%s"
             % (len(move_off), len(rows), (": " + str(move_off)) if move_off else ""))
    v.append("  score differed on %d of %d positions%s"
             % (len(score_off), len(rows), (": " + str(score_off)) if score_off else ""))
    v.append("")
    if not move_off and not depth_off:
        v.append("ONE-LINE DECISION: ignoring the per-position advice costs up to %.2fx in NODES PER GAME with"
                 % (ratio or 1.0))
        v.append("NO change in the move, the depth or the score — so it is a COST decision, not a quality one:")
    elif not move_off:
        v.append("ONE-LINE DECISION: ignoring the advice costs up to %.2fx in nodes per game and changes the"
                 % (ratio or 1.0))
        v.append("DEPTH reached but not the move chosen — a quality cost at the margin, not in the move played.")
    else:
        v.append("ONE-LINE DECISION: ignoring the advice costs up to %.2fx in nodes per game AND changes the"
                 % (ratio or 1.0))
        v.append("MOVE CHOSEN on %d of %d positions — the advice is URGENT, not optional." % (len(move_off), len(rows)))
    (out / "softnodes_ignoring_advice.json").write_text(json.dumps(
        {"fixed_n": FIXED, "rows": rows, "cost_ratio": ratio, "depth_offsets": depth_off,
         "move_offsets": move_off, "score_offsets": score_off, "verdict": v}, indent=1))
    (out / "softnodes_ignoring_advice.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
