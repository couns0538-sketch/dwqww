#!/usr/bin/env python3
"""tail_pc20.py EXE OUTDIR — re-run 08-F11 on a build under PC20, Threads 1 stated.

08-F11 (seat 08, area 8, base tree, S14 + Threads 1): "The clock tail scales linearly with the clock:
p99/median is constant at 3.1-4.8x across wtime 200/500/1000/3000/10000/30000 ms (p99 25.2 / 65.1 /
119.6 / 485.6 / 1422.7 / 3710.1 ms), and a 10x clock gives an 11.9x p99. The median is a slowly shrinking
fraction of the planned soft limit: 100 %, 80 %, 77 %, 75 %, 67 %, 61 %. No search at any clock size
exceeded its own clock."

THREADS 1 IS SENT EXPLICITLY in every cell (swarm rule: a score must come from Threads 1 unless the job is
about threading; a non-reproducible score changes the tree, which changes the search time). The engine's own
default is also 1, but this harness does not rely on that.

Settings: PC20 = S14's 14 setoptions, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
MateAlphaGuard true, OwnBook false, and Threads 1 / Hash 16.

Per search: position, isready, `go wtime W btime W winc 0 binc 0`, wall time go->bestmove on a monotonic
clock, the engine's own last-info `time` and depth, nodes, and whether any `info ... score` line was
followed by a DIFFERENT score for the same move across repeats (the score-reproducibility check seat 04
raised). Writes OUTDIR/w<W>.tsv plus a .meta naming every option sent.

Usage: tail_pc20.py EXE OUTDIR [NPOS]
"""
import hashlib
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
CLOCKS = (200, 500, 1000, 3000, 10000, 30000)
OVERHEAD = 10
SOFT_DIV = 22


def soft_plan(wtime):
    if wtime <= OVERHEAD:
        return 0
    return max(1, (wtime - OVERHEAD) // SOFT_DIV)


def cell(exe, fens, wtime, outdir, sha):
    eng = Engine(exe)
    eng.send("uci")
    if not eng.read_until("uciok", 20)[1]:
        raise SystemExit("no uciok")
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l or l.startswith("ERROR")]
        if bad or not ok:
            raise SystemExit(f"STOP on option {opt}: {bad[:2] or 'no readyok'}")
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc 0 binc 0")
        out, ok = eng.read_until("bestmove", max(120, wtime / 1000 * 3))
        t1 = time.monotonic()
        if not ok:
            rows.append({"fen": fen, "wall": float("inf"), "etime": "", "depth": 0, "nodes": 0,
                         "best": "NORESP", "score": ""})
            continue
        best, etime, depth, nodes, score = "", "", 0, 0, ""
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth"):
                f = line.split()
                depth = max(depth, int(f[f.index("depth") + 1]))
                if "time" in f:
                    etime = f[f.index("time") + 1]
                if "nodes" in f:
                    nodes = int(f[f.index("nodes") + 1])
                if "score" in f:
                    score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
        rows.append({"fen": fen, "wall": (t1 - t0) * 1000.0, "etime": etime, "depth": depth,
                     "nodes": nodes, "best": best, "score": score})
    eng.close()
    with open(os.path.join(outdir, f"w{wtime}.tsv"), "w") as fh:
        fh.write("fen\twall_ms\tengine_time_ms\tlast_depth\tnodes\tbestmove\tscore\n")
        for r in rows:
            fh.write(f"{r['fen']}\t{r['wall']:.3f}\t{r['etime']}\t{r['depth']}\t{r['nodes']}\t"
                     f"{r['best']}\t{r['score']}\n")
    with open(os.path.join(outdir, f"w{wtime}.meta"), "w") as fh:
        fh.write(f"exe_started {os.path.abspath(exe)}\nexe_sha256 {sha}\n")
        fh.write("go_line go wtime {0} btime {0} winc 0 binc 0\n".format(wtime))
        fh.write("THREADS 1 sent explicitly\nsettings PC20\n")
        for opt, val in sent:
            fh.write(f"option {opt} {val}\n")
        fh.write(f"positions {len(rows)}\nplan_soft_ms {soft_plan(wtime)}\n")
    return rows


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    print("| wtime | n | median | p99 | p99/median | median/soft | over wtime | over hard plan "
          "| max over hard | Threads |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for wtime in CLOCKS:
        rows = cell(exe, fens, wtime, outdir, sha)
        walls = [r["wall"] for r in rows if r["wall"] != float("inf")]
        if not walls:
            print(f"| {wtime} | 0 | NO RESPONSES | | | | | | | 1 |")
            continue
        soft = soft_plan(wtime)
        # clock searches: hard = min(available*60/100, soft*5), clamped; recomputed below
        avail = max(0, wtime - OVERHEAD)
        hard = min(avail * 60 // 100, soft * 5) if soft else 0
        hard = max(1, min(hard, avail)) if avail else 0
        med, p99 = statistics.median(walls), pct(walls, 99)
        over = sum(1 for w in walls if w > wtime)
        over_hard = [w - hard for w in walls if w > hard]
        print(f"| {wtime} | {len(walls)} | {med:.1f} | {p99:.1f} | {p99/med:.2f} | {med/soft:.2f} | "
              f"{over} | {len(over_hard)} | {max(over_hard) if over_hard else 0:.1f} | 1 |", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
