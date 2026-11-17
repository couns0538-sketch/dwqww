#!/usr/bin/env python3
"""swarm seat 01: independent replication of seat 19's `19-C53` — does PC20's node saving become WALL time?

Seat 19 committed a prediction before measuring: if seat 29's finding (PC20 searches 10.7-11.9 % FEWER NODES than S14
at matched depth) is right, and seat 19's own finding (PC20's per-node cost is within ~1.2 %) is right, then PC20
should take **10-11 % less WALL time**. Seat 29 measured no wall difference, but at n=40 with a CI of [-9 %, +16 %],
which cannot see a 10 % effect. Seat 19 predicts a paired wall ratio of **0.88-0.93** at n>=120.

This is a replication on MY build with MY harness, and I fix every choice before running:

  * **S14 vs PC20**, both on the PC r15 tree (S14 = PC20 minus its six non-default flags: CuckooRep, HistRework,
    TtPruneV2, CorrHistV2, MateAlphaGuard, OwnBook).
  * **`go depth 12`** fixed, so node counts differ and any node saving can show. `depth` rather than a budget, because
    a node budget would confound the comparison with the rung problem (`S-F123`) - worth avoiding given what I know.
  * **ABBA interleaving**, fresh process per search, both settings in the same session.
  * **The engine's own `time`** from the last PV line, so process startup is excluded (Trap 5 / Trap 10).
  * **n = 120 pairs minimum**, seat 19's stated threshold for 12 % power, on a deterministic stride through the same
    FEN set they used (`R_1911.fens` - they cite `R_2911`, which is not on their branch).

Two things I add that their design does not state, both from mistakes I have made:
  * **node counts are recorded per pair**, because if the two settings produce the SAME node count the "node saving"
    premise is absent on that position and the pair tests nothing;
  * **the median and the ratio-of-medians are both reported**, labelled, since they are different statistics
    (`S-F126`) and a paired-ratio claim needs the first.

Usage: check_wall_time_saving.py <exe> <fens> <outdir> [n]
"""
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

# PC20 is S14 plus these six, which are the only difference between the two regimes under test.
PC20_ONLY = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

PC20 = S14 + PC20_ONLY


def search(exe, fen, opts, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            if line.startswith(prefix):
                return line.rstrip("\n")
        return None

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for n, v in opts:
        send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position fen " + fen)
    send("isready")
    until("readyok")
    send("go depth %d" % depth)

    last = None
    bm = None
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            last = line
        if line.startswith("bestmove"):
            bm = line
            break
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    if last is None or bm is None:
        return None
    t = re.search(r"time (\d+)", last)
    nd = re.search(r"nodes (\d+)", last)
    dp = re.search(r"depth (\d+)", last)
    return {"time": int(t.group(1)) if t else None,
            "nodes": int(nd.group(1)) if nd else None,
            "depth": int(dp.group(1)) if dp else None,
            "bestmove": bm.split()[1] if len(bm.split()) > 1 else None}


def ci_of_median_ratio(ratios):
    """Bootstrap-free interval on the MEDIAN of paired ln-ratios: report the 2.5/97.5 percentiles of the ratios
    themselves, which is what a reader wants, plus the geometric mean of ln-ratios and its CI."""
    if len(ratios) < 5:
        return None
    lr = sorted(math.log(r) for r in ratios if r > 0)
    n = len(lr)
    mean = sum(lr) / n
    sd = statistics.stdev(lr) if n > 1 else 0.0
    se = sd / math.sqrt(n)
    return {"n": n, "geo_mean_ratio": math.exp(mean),
            "ci_lo": math.exp(mean - 1.96 * se), "ci_hi": math.exp(mean + 1.96 * se),
            "median_ratio": statistics.median(ratios),
            "q_lo": statistics.quantiles(ratios, n=40)[0] if n >= 5 else None,
            "q_hi": statistics.quantiles(ratios, n=40)[-1] if n >= 5 else None}


def main():
    exe, fenfile, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    depth = 12

    lines = [l.strip() for l in Path(fenfile).read_text().splitlines() if l.strip()]
    stride = max(1, len(lines) // n)
    sample = lines[::stride][:n]

    rows = []
    print("=== %d pairs, depth %d, ABBA" % (len(sample), depth), flush=True)
    for i, fen in enumerate(sample):
        # ABBA: S14, PC20, PC20, S14 - machine drift hits both equally
        a1 = search(exe, fen, S14, depth)
        b1 = search(exe, fen, PC20, depth)
        b2 = search(exe, fen, PC20, depth)
        a2 = search(exe, fen, S14, depth)
        if not all([a1, b1, b2, a2]):
            continue
        a_time = (a1["time"] + a2["time"]) / 2.0
        b_time = (b1["time"] + b2["time"]) / 2.0
        # depth must be reached by all four, else the pair compares different searches
        if not all(x["depth"] == depth for x in (a1, b1, b2, a2)):
            rows.append({"i": i, "skipped": "depth not reached", "fen": fen})
            continue
        if a_time <= 0:
            continue
        rows.append({"i": i, "fen": fen,
                     "s14_time": a_time, "pc20_time": b_time, "ratio": b_time / a_time,
                     "s14_nodes": a1["nodes"], "pc20_nodes": b1["nodes"],
                     "node_ratio": (b1["nodes"] / a1["nodes"]) if a1["nodes"] else None})
        if (i + 1) % 20 == 0:
            good = [r for r in rows if "ratio" in r]
            print("  %d done, %d usable, median ratio so far %.3f"
                  % (i + 1, len(good), statistics.median([r["ratio"] for r in good]) if good else 0), flush=True)

    good = [r for r in rows if "ratio" in r]
    skipped = [r for r in rows if "skipped" in r]
    L = ["S-C46: replication of seat 19's 19-C53 - does PC20's node saving become WALL time?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "fens: %s (%d lines, stride %d, n=%d requested)" % (fenfile, len(lines), stride, n),
         "S14 vs PC20 on the PC r15 tree, go depth %d, Threads 1, Hash 16, ABBA, fresh process per search," % depth,
         "engine-reported time from the last PV line (process startup excluded).", ""]

    if not good:
        L.append("NOTHING WAS MEASURED - no usable pairs, so no ratio is claimed.")
    else:
        stats = ci_of_median_ratio([r["ratio"] for r in good])
        node_ratios = [r["node_ratio"] for r in good if r["node_ratio"]]
        L.append("PAIRS: %d usable, %d skipped (depth not reached)" % (len(good), len(skipped)))
        L.append("")
        L.append("WALL TIME, PC20 / S14:")
        L.append("  **median paired ratio %.3f**   (95 %% CI on the geometric mean: %.3f - %.3f)"
                 % (stats["median_ratio"], stats["ci_lo"], stats["ci_hi"]))
        L.append("  geometric mean of paired ratios %.3f over n=%d" % (stats["geo_mean_ratio"], stats["n"]))
        L.append("  (median and geometric mean are different statistics, both labelled deliberately)")
        L.append("")
        if node_ratios:
            L.append("NODES, PC20 / S14:")
            L.append("  median node ratio **%.3f** (%.1f %% fewer nodes under PC20)"
                     % (statistics.median(node_ratios), 100 * (1 - statistics.median(node_ratios))))
            same = sum(1 for r in node_ratios if abs(r - 1.0) < 1e-9)
            L.append("  pairs with IDENTICAL node counts: %d of %d (those test nothing about a node saving)"
                     % (same, len(node_ratios)))
        L.append("")
        L.append("SCORED AGAINST SEAT 19's PREDICTION (0.88-0.93 wall ratio):")
        r = stats["median_ratio"]
        if 0.88 <= r <= 0.93:
            L.append("  **PREDICTION CONFIRMED** - %.3f lands inside their stated range." % r)
        elif r < 0.88:
            L.append("  OUTSIDE, on the FASTER side: %.3f is below their range (PC20 saves more time than predicted)." % r)
        else:
            L.append("  OUTSIDE, on the SLOWER side: %.3f is above their range - the node saving did NOT become wall"
                     % r)
            L.append("  time to the degree expected. That is the outcome that would support seat 29's null result.")
        L.append("  Their power note said n>=120 is adequate for 12 percent. This run has %d usable pairs." % len(good))

    (out / "check_wall_time_saving.json").write_text(json.dumps({"sha": sha, "depth": depth, "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_wall_time_saving.txt").write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
