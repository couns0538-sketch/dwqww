#!/usr/bin/env python3
"""swarm seat 01: settle my own 50 % on a LARGE sample (S-C42).

My softnodes pair test (S-C41) measured **50 % identical** on 12 hand-picked positions. Seat 19's `19-C49`, on 200
positions from a game set, measured **46.5-47.0 %** and mean spend **3,185 / 3,234** where I had **3,072**. Those agree
in direction and rough magnitude, but 12 positions is a small sample and I should not defend 50 % against their
2.5x-larger one without checking whether mine was noise.

So this runs the same pair test on a large sample drawn from `R_1911.fens` (11,192 positions, borrowed from seat 19's
branch - credited, not claimed as mine). Two things it answers:

  1. Does 50 % hold up, or move toward 46.5 %? A binomial interval on n=12 is wide (roughly 25-75 %), so 50 % and
     47 % were never in conflict - but that is an argument, and a bigger n is evidence.
  2. Is seat 19's mean spend (3,185-3,234) the better estimate? My 3,072 on 12 positions vs theirs on 200.

Design, per the traps I have already paid for:
  * a FIXED sample size and a fixed stride, so the set is reproducible from the file rather than chosen by me;
  * fresh process per search, read to `bestmove` before `quit` (Trap 11);
  * the identity check is on (bestmove, depth, nodes) - all three, not depth alone (S-F126 discipline);
  * report a binomial 95 % interval on the identical fraction, because a bare percentage at n=12 invites over-reading;
  * report the mean spend with its spread, and the overrun, since that is the second quantity that disagreed.

Usage: check_softnodes_large_sample.py <exe> <fens-file> <outdir> [n] [--pc20]
"""
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def search(exe, fen, pos_cmd, softnodes, pc20):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")
    info = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                info.append(line)
            if line.startswith(prefix):
                return line
        return None

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    if pc20:
        for n, v in PC20:
            send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(pos_cmd)
    send("isready")
    until("readyok")
    send("go softnodes %d" % softnodes)
    bm = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=180)
    except Exception:
        p.kill()
    if bm is None:
        return {"bestmove": None, "depth": None, "nodes": None, "no_info": not info}
    if not info:
        # the degenerate class seat 19 reported: a 4N-cap hit with no completed iteration and no info line
        return {"bestmove": bm.split()[1] if len(bm.split()) > 1 else None,
                "depth": None, "nodes": None, "no_info": True}
    last = info[-1]
    d = re.search(r"depth (\d+)", last)
    n = re.search(r"nodes (\d+)", last)
    return {"bestmove": bm.split()[1] if len(bm.split()) > 1 else None,
            "depth": int(d.group(1)) if d else None,
            "nodes": int(n.group(1)) if n else None, "no_info": False}


def ci95(k, n):
    """Wilson interval - honest for proportions near 0/1 and for small n, unlike the normal approximation."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main():
    exe, fenfile, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    pc20 = "--pc20" in sys.argv
    n = 200
    for a in sys.argv[4:]:
        if a.isdigit():
            n = int(a)
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    lines = [l.strip() for l in Path(fenfile).read_text().splitlines() if l.strip()]
    # deterministic stride over the file: reproducible without me picking positions
    stride = max(1, len(lines) // n)
    sample = lines[::stride][:n]

    rows = []
    print("=== %d positions (stride %d from %d lines), pc20=%s" % (len(sample), stride, len(lines), pc20), flush=True)
    for i, fen in enumerate(sample):
        pos_cmd = "position startpos" if fen.lower().startswith("startpos") else "position fen " + fen
        a = search(exe, fen, pos_cmd, 2000, pc20)
        b = search(exe, fen, pos_cmd, 3000, pc20)
        ident = (a["bestmove"] == b["bestmove"] and a["depth"] == b["depth"]
                 and a["nodes"] == b["nodes"] and a["no_info"] == b["no_info"])
        rows.append({"i": i, "fen": fen, "a": a, "b": b, "identical": ident})
        if (i + 1) % 25 == 0:
            k = sum(1 for r in rows if r["identical"])
            print("  %d/%d done, identical %d (%.1f %%)" % (i + 1, len(sample), k, 100.0 * k / (i + 1)), flush=True)

    k = sum(1 for r in rows if r["identical"])
    N = len(rows)
    lo, hi = ci95(k, N)
    spend2000 = [r["a"]["nodes"] for r in rows if r["a"]["nodes"]]
    spend3000 = [r["b"]["nodes"] for r in rows if r["b"]["nodes"]]
    deg = sum(1 for r in rows if r["a"]["no_info"] or r["b"]["no_info"])

    L = ["S-C42: my 50 percent identical on 12 positions, re-measured on a large sample",
         "exe: %s" % exe, "sha256: %s" % sha,
         "fens: %s (%d lines, stride %d, n=%d)" % (fenfile, len(lines), stride, N),
         "PC20=%s, Threads 1, Hash 16, fresh process per search, read to bestmove before quit." % pc20,
         "",
         "IDENTICAL (bestmove, depth, nodes all equal, no-info status equal):",
         "  **%d of %d = %.1f %%**   Wilson 95 %% CI: %.1f - %.1f %%" % (k, N, 100.0 * k / N, 100 * lo, 100 * hi),
         "",
         "MEAN SPEND at softnodes 2000: %.0f nodes (median %.0f, range %d-%d); overrun over 2000 = %+.0f (%+.0f %%)"
         % (statistics.mean(spend2000), statistics.median(spend2000), min(spend2000), max(spend2000),
            statistics.mean(spend2000) - 2000, 100 * (statistics.mean(spend2000) - 2000) / 2000) if spend2000 else "  (none)",
         "MEAN SPEND at softnodes 3000: %.0f nodes (median %.0f)" % (statistics.mean(spend3000), statistics.median(spend3000)) if spend3000 else "",
         "DEGENERATE (no info line at either budget): %d of %d" % (deg, N),
         ""]

    L.append("COMPARISON WITH THE TWO EARLIER MEASUREMENTS")
    L.append("  seat 01, 12 hand-picked positions : 50 %  identical, mean spend 3,072")
    L.append("  seat 19, 200 positions (R_2911)   : 46.5-47.0 % identical, mean spend 3,185 / 3,234")
    L.append("  this run, %d positions              : %.1f %% identical, mean spend %.0f"
             % (N, 100.0 * k / N, statistics.mean(spend2000) if spend2000 else 0))
    L.append("")
    if 0.465 <= k / N <= 0.47:
        L.append("VERDICT: the large sample lands ON seat 19's figure (46.5-47.0 %), so MY 50 % from 12 positions was")
        L.append("  a small-sample overestimate and theirs is the better number. My 50 % was never in conflict with it -")
        L.append("  the Wilson interval on n=12 covers both - but agreement is not the same as being right, and the")
        L.append("  larger sample should replace mine in the record.")
    elif lo <= 0.465 <= hi:
        L.append("VERDICT: consistent with seat 19's 46.5-47.0 % - the two intervals overlap, so the samples do not")
        L.append("  disagree. This run's point estimate is %.1f %%; theirs is stronger at n=%d vs my 12." % (100.0 * k / N, N))
    else:
        L.append("VERDICT: this run (%.1f %%) does NOT overlap seat 19's 46.5-47.0 %% interval - reported as a genuine"
                 % (100.0 * k / N))
        L.append("  discrepancy between samples, not smoothed over.")

    (out / "check_softnodes_large.json").write_text(json.dumps({"sha": sha, "pc20": pc20, "n": N,
                                                                "identical": k, "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_softnodes_large.txt").write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
