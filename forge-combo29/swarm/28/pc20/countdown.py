#!/usr/bin/env python3
"""countdown.py EXE LABEL OUTDIR — does a DECLINING clock change the tail, at 6 s + 0.06?

Seat 08 measured the same control ("median 295 ms pinned / 131 ms with a real countdown") and found a
worst case of 482 ms with nothing near the hard limit. I found 5 of 120 searches at 1.2-1.59 s. Two
candidate causes, and this script tests the one that is about the HARNESS rather than the positions:

  A) my harness sends `go wtime 6000` for EVERY move — the clock never goes down. A search therefore always
     sees a 6 s clock and always plans soft 317 / hard 1585 ms.
  B) a match sends a DECLINING clock: `wtime` falls by the time each move takes, plus the 60 ms increment.
     Late in a game the clock is small, the plan is small, and the hard limit is small — so a long search
     is cut much sooner.

If the tail disappears under a countdown, my 1585 ms outliers are an artefact of an unrealistic constant
clock, not a real risk class. If it persists, the positions are the explanation.

Both modes replay the same 60 positions in order, PC20, Threads 1, Hash 16.

Usage: countdown.py EXE OUTDIR [NPOS]
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
WINC, START = 60, 6000
OVERHEAD, SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT = 10, 22, 75, 60, 5


def plan(time_ms):
    if time_ms <= OVERHEAD:
        return 0, 0
    avail = time_ms - OVERHEAD
    soft = avail // SOFT_DIV + WINC * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


def run(exe, fens, countdown, outdir, label):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")

    rows = []
    # A countdown must be per SIDE. The 60 positions come in pairs of colours in places, so we simply
    # decrement the side that just moved by its own elapsed time and add the increment back.
    clock = {"w": START, "b": START}
    for i, fen in enumerate(fens):
        import chess
        board = chess.Board(fen)
        side = "w" if board.turn == chess.WHITE else "b"
        wtime, btime = (clock["w"], clock["b"]) if countdown else (START, START)
        soft, hard = plan(wtime if side == "w" else btime)
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {max(1, wtime)} btime {max(1, btime)} winc {WINC} binc {WINC}")
        out, ok = eng.read_until("bestmove", 40)
        t1 = time.monotonic()
        wall = (t1 - t0) * 1000.0
        if not ok:
            rows.append({"i": i, "fen": fen, "wall": float("inf"), "depth": 0, "best": "NORESP",
                         "soft": soft, "hard": hard, "wtime": wtime, "side": side})
            continue
        best, depth = "", 0
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth"):
                depth = max(depth, int(line.split()[2]))
        if countdown:
            clock[side] = max(1, max(0, (wtime if side == "w" else btime) - int(wall)) + WINC)
        rows.append({"i": i, "fen": fen, "wall": wall, "depth": depth, "best": best,
                     "soft": soft, "hard": hard, "wtime": wtime, "side": side})
    eng.close()
    with open(os.path.join(outdir, f"{label}.tsv"), "w") as fh:
        fh.write("i\tfen\tside\tclock_ms\tsoft\thard\twall_ms\tlast_depth\tbestmove\n")
        for r in rows:
            fh.write(f"{r['i']}\t{r['fen']}\t{r['side']}\t{r['wtime']}\t{r['soft']}\t{r['hard']}\t"
                     f"{r['wall']:.3f}\t{r['depth']}\t{r['best']}\n")
    return rows


def report(label, rows):
    walls = [r["wall"] for r in rows if r["wall"] != float("inf")]
    if not walls:
        print(f"| {label} | 0 | - | - | - | - | - |"); return
    s = sorted(walls)
    k = (len(s) - 1) * 0.99
    p99 = s[int(k)] + (s[min(int(k) + 1, len(s) - 1)] - s[int(k)]) * (k - int(k))
    med = statistics.median(walls)
    over_hard = sum(1 for r in rows if r["hard"] and r["wall"] > r["hard"])
    big = sum(1 for w in walls if w > 1000)
    print(f"| {label} | {len(walls)} | {med:.1f} | {p99:.1f} | {max(walls):.1f} | "
          f"{p99/med:.2f} | {over_hard} | {big} |")


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print(f"PC20, Threads 1, Hash 16, winc {WINC}, start {START} ms; SAME {len(fens)} positions in the same "
          f"order, once with a constant clock and once with a real countdown")
    print()
    print("| mode | n | median | p99 | max | p99/median | over its own hard | searches >1000 ms |")
    print("|---|---|---|---|---|---|---|---|")
    for label, countdown in (("constant 6000 ms", False), ("real countdown", True)):
        rows = run(exe, fens, countdown, outdir, label.replace(" ", "_"))
        report(label, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
