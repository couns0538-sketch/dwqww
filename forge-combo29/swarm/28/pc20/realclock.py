#!/usr/bin/env python3
"""realclock.py BASE PC OUTDIR [NPOS] — the tail and stop fraction at the OWNER'S control: 6 s + 0.06/move.

FABLE_TO_swarm_6: "The owner's real clock is 6 seconds plus 0.06 per move, with the PC build under PC20 at
Threads 1 and Hash 16. Every clock measurement in the swarm so far was at a different control."

So this is the control that matters:
    go wtime 6000 btime 6000 winc 60 binc 60
PC build under PC20, Threads 1, Hash 16. Base build under S14 + Threads 1 + Hash 16 + OwnBook false, so
the two builds are compared at the same clock with each on its own settings.

Plan, from the engine's OWN advertised constants (verified equal on both builds in S-F27):
    available = 6000 - 10 = 5990
    soft = 5990/22 + 60*75/100 = 272 + 45 = 317 ms
    hard = min(5990*60/100, 317*5) = min(3594, 1585) = 1585 ms

Per search records: wall ms, the engine's own last-info time, the last completed depth, nodes, bestmove and
its legality. Reports median/p99/max, the stop fraction achieved/soft, last-iteration/soft, and counts over
soft, over hard and over the clock.

Usage: realclock.py BASE_EXE PC_EXE OUTDIR [NPOS]
"""
import hashlib
import os
import statistics
import sys
import time

import chess

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
WTIME, WINC = 6000, 60
OVERHEAD, SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT = 10, 22, 75, 60, 5


def plan():
    avail = WTIME - OVERHEAD
    soft = avail // SOFT_DIV + WINC * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    return max(1, min(soft, avail)), max(1, min(hard, avail))


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def run(exe, fens, pc20, label, outdir):
    eng = Engine(exe)
    eng.send("uci")
    if not eng.read_until("uciok", 20)[1]:
        raise SystemExit("no uciok")
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
        eng.send(f"go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}")
        out, ok = eng.read_until("bestmove", 40)
        t1 = time.monotonic()
        if not ok:
            rows.append({"fen": fen, "wall": float("inf"), "etime": None, "depth": 0,
                         "nodes": 0, "best": "NORESP", "legal": "n/a"})
            continue
        best, etime, depth, nodes = "", None, 0, 0
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth"):
                f = line.split()
                depth = max(depth, int(f[f.index("depth") + 1]))
                if "time" in f:
                    etime = float(f[f.index("time") + 1])
                if "nodes" in f:
                    nodes = int(f[f.index("nodes") + 1])
        try:
            legal = str(chess.Move.from_uci(best) in chess.Board(fen).legal_moves) if best else "n/a"
        except ValueError:
            legal = "unparsable"
        rows.append({"fen": fen, "wall": (t1 - t0) * 1000.0, "etime": etime, "depth": depth,
                     "nodes": nodes, "best": best, "legal": legal})
    eng.close()
    with open(os.path.join(outdir, f"realclock_{label}.tsv"), "w") as fh:
        fh.write("fen\twall_ms\tengine_time_ms\tlast_depth\tnodes\tbestmove\tlegal\n")
        for r in rows:
            fh.write(f"{r['fen']}\t{r['wall']:.3f}\t{r['etime']}\t{r['depth']}\t{r['nodes']}\t"
                     f"{r['best']}\t{r['legal']}\n")
    with open(os.path.join(outdir, f"realclock_{label}.meta"), "w") as fh:
        fh.write(f"exe_started {os.path.abspath(exe)}\n")
        fh.write(f"exe_sha256 {hashlib.sha256(open(exe, 'rb').read()).hexdigest()}\n")
        fh.write(f"go_line go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}\n")
        fh.write("settings " + ("PC20" if pc20 else "S14+OwnBook false") + "\nTHREADS 1 sent explicitly\n")
        for opt, val in sent:
            fh.write(f"option {opt} {val}\n")
        fh.write(f"positions {len(rows)}\n")
    return rows


def main() -> int:
    base_exe, pc_exe, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    npos = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    soft, hard = plan()
    print(f"OWNER'S CONTROL: go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}")
    print(f"plan from the engine's own constants: soft {soft} ms, hard {hard} ms, "
          f"{len(fens)} positions, Threads 1, Hash 16")
    print()
    print("| build | n | median | p99 | max | p99/median | stop fraction (median/soft) | "
          "last-iter/soft | median last depth | over soft | over hard | over clock | legal |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label, exe, pc20 in (("base", base_exe, False), ("PC20", pc_exe, True)):
        rows = run(exe, fens, pc20, label, outdir)
        walls = [r["wall"] for r in rows if r["wall"] != float("inf")]
        etimes = [r["etime"] for r in rows if r["etime"] is not None]
        depths = [r["depth"] for r in rows]
        legal = sum(1 for r in rows if r["legal"] == "True")
        mw = statistics.median(walls)
        print(f"| {label} | {len(rows)} | {mw:.1f} | {pct(walls, 99):.1f} | {max(walls):.1f} | "
              f"{pct(walls, 99)/mw:.2f} | {mw/soft:.2f} | "
              f"{(statistics.median(etimes)/soft if etimes else 0):.2f} | "
              f"{statistics.median(depths):.0f} | {sum(1 for w in walls if w > soft)} | "
              f"{sum(1 for w in walls if w > hard)} | {sum(1 for w in walls if w > WTIME)} | "
              f"{legal}/{len(rows)} |", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
