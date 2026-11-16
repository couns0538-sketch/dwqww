#!/usr/bin/env python3
"""tail_cause.py — why is the PC build's clock tail better: deeper, or stopping earlier?

Same clock grid on BOTH builds, each on its own settings, Threads 1 sent explicitly to both:
  base  : S14 + Threads 1 + Hash 16 + OwnBook false
  PC r15: PC20 = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
          MateAlphaGuard true, OwnBook false, Threads 1 + Hash 16

Per cell and per build this records, per search: wall ms, the engine's own `time`, the LAST COMPLETED
DEPTH, nodes. Then it prints a per-cell comparison with:
  median achieved time, median last depth, median nodes, nodes/second (from the last info line),
  achieved / soft plan, and depth per achieved millisecond.
That pair — achieved time AND depth for the same cell — is what separates "searches deeper" from
"stops earlier".

Usage: tail_cause.py BASE_EXE PC_EXE OUTDIR [NPOS]
"""
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
CLOCKS = (1000, 3000, 10000)
OVERHEAD, SOFT_DIV = 10, 22


def soft_plan(w):
    return max(1, (w - OVERHEAD) // SOFT_DIV) if w > OVERHEAD else 0


def cell(exe, fens, wtime, pc20):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items())
    sent += PC20_EXTRA if pc20 else [("OwnBook", "false")]
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
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
            continue
        etime, depth, nodes = None, 0, 0
        for line in out:
            if line.startswith("info depth"):
                f = line.split()
                depth = max(depth, int(f[f.index("depth") + 1]))
                if "time" in f:
                    etime = float(f[f.index("time") + 1])
                if "nodes" in f:
                    nodes = int(f[f.index("nodes") + 1])
        rows.append({"wall": (t1 - t0) * 1000.0, "etime": etime, "depth": depth, "nodes": nodes})
    eng.close()
    return rows


def med(v, default=0.0):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else default


def main() -> int:
    base, pc, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    npos = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]

    print("| wtime | build | n | median wall | median engine time | median LAST DEPTH | median nodes | "
          "nps | wall/soft | depth per 100 ms |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    allrows = {}
    for wtime in CLOCKS:
        for label, exe, pc20 in (("base", base, False), ("PC20", pc, True)):
            rows = cell(exe, fens, wtime, pc20)
            allrows[(wtime, label)] = rows
            soft = soft_plan(wtime)
            mw = med([r["wall"] for r in rows])
            me = med([r["etime"] for r in rows])
            md = med([r["depth"] for r in rows])
            mn = med([r["nodes"] for r in rows])
            nps = (mn / (me / 1000.0)) if me else 0
            print(f"| {wtime} | {label} | {len(rows)} | {mw:.1f} | {me:.0f} | {md:.0f} | {mn:.0f} | "
                  f"{nps:.0f} | {mw/soft:.2f} | {md/(mw/100.0) if mw else 0:.1f} |", flush=True)
            with open(os.path.join(outdir, f"w{wtime}_{label}.tsv"), "w") as fh:
                fh.write("wall_ms\tengine_time_ms\tlast_depth\tnodes\n")
                for r in rows:
                    fh.write(f"{r['wall']:.3f}\t{r['etime']}\t{r['depth']}\t{r['nodes']}\n")

    print()
    print("## The separating comparison")
    print()
    print("| wtime | PC wall / base wall | PC depth - base depth | PC nps / base nps | reading |")
    print("|---|---|---|---|---|")
    verdicts = []
    for wtime in CLOCKS:
        b, p = allrows[(wtime, "base")], allrows[(wtime, "PC20")]
        bw, pw = med([r["wall"] for r in b]), med([r["wall"] for r in p])
        bd, pd = med([r["depth"] for r in b]), med([r["depth"] for r in p])
        be, pe = med([r["etime"] for r in b]), med([r["etime"] for r in p])
        bn = med([r["nodes"] for r in b])
        pn = med([r["nodes"] for r in p])
        bnps = bn / (be / 1000.0) if be else 0
        pnps = pn / (pe / 1000.0) if pe else 0
        if pd > bd and pw <= bw:
            reading = "DEEPER in LESS time - a strength"
        elif pd > bd:
            reading = "deeper for more time"
        elif abs(pd - bd) < 0.5 and pw < bw * 0.9:
            reading = "same depth, less time - STOPS EARLIER"
        else:
            reading = "no clear separation"
        verdicts.append((wtime, reading))
        print(f"| {wtime} | {pw/bw:.2f} | {pd-bd:+.0f} | {pnps/bnps if bnps else 0:.2f} | {reading} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
