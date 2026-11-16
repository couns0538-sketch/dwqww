#!/usr/bin/env python3
"""ply_cost.py BASE PC OUTDIR [NPOS] — does the lost 10 s ply change the MOVE?

For each position, four searches:
  1. base  at `go wtime 10000`         (clock stop, base settings)
  2. PC20  at `go wtime 10000`         (clock stop, PC20 settings)
  3. base  at `go depth 20` fixed      (the reference move)
  4. PC20  at `go depth 20` fixed      (equal-depth control)
plus base at `go depth 19` and PC20 at `go depth 19` for the equal-depth-at-19 control.

Then, restricted to positions where the PC20 clock run reached a SHALLOWER depth than the base clock run,
it reports agreement rates:
  A1  PC20-clock == base-depth20     (the question)
  A2  base-clock == base-depth20     (the CONTROL: same question for the build that did not lose a ply)
  A3  PC20-clock == base-clock
and at equal fixed depth:
  A5  PC20-depth20 == base-depth20
  A5b PC20-depth19 == base-depth19

The control A2 is what makes A1 interpretable: if base's own clock answer is just as far from its
depth-20 answer, then one ply at this clock decides moves for neither build.

Every move is checked for legality with python-chess.

Usage: ply_cost.py BASE_EXE PC_EXE OUTDIR [NPOS]
"""
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


class Session:
    """One long-lived process per build; ucinewgame + isready before every search."""

    def __init__(self, exe, pc20):
        self.eng = Engine(exe)
        self.eng.send("uci")
        self.eng.read_until("uciok", 20)
        sent = [("Threads", 1), ("Hash", 16)] + list(S14.items())
        sent += PC20_EXTRA if pc20 else [("OwnBook", "false")]
        for opt, val in sent:
            self.eng.send(f"setoption name {opt} value {val}")
            self.eng.send("isready")
            lines, ok = self.eng.read_until("readyok", 20)
            bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
            if bad or not ok:
                raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")

    def go(self, fen, command, timeout=120):
        self.eng.send("ucinewgame")
        self.eng.send("isready")
        self.eng.read_until("readyok", 20)
        self.eng.send(f"position fen {fen}")
        self.eng.send("isready")
        self.eng.read_until("readyok", 20)
        t0 = time.monotonic()
        self.eng.send(command)
        out, ok = self.eng.read_until("bestmove", timeout)
        t1 = time.monotonic()
        best, depth = "", 0
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth"):
                f = line.split()
                depth = max(depth, int(f[f.index("depth") + 1]))
        return {"best": best, "depth": depth, "wall": (t1 - t0) * 1000.0, "ok": ok}

    def close(self):
        self.eng.close()


def legal(fen, move):
    try:
        return chess.Move.from_uci(move) in chess.Board(fen).legal_moves
    except (ValueError, AssertionError):
        return False


def main() -> int:
    base_exe, pc_exe, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    npos = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]

    b = Session(base_exe, pc20=False)
    p = Session(pc_exe, pc20=True)
    rows = []
    print(f"{len(fens)} positions; base and PC20 each in one process, Threads 1, ucinewgame per search")
    for i, fen in enumerate(fens, 1):
        bc = b.go(fen, "go wtime 10000 btime 10000 winc 0 binc 0")
        pc = p.go(fen, "go wtime 10000 btime 10000 winc 0 binc 0")
        b20 = b.go(fen, "go depth 20", timeout=180)
        p20 = p.go(fen, "go depth 20", timeout=180)
        b19 = b.go(fen, "go depth 19", timeout=180)
        p19 = p.go(fen, "go depth 19", timeout=180)
        rows.append({"fen": fen, "bc": bc, "pc": pc, "b20": b20, "p20": p20, "b19": b19, "p19": p19})
        print(f"  {i}/{len(fens)} base-clock d{bc['depth']}={bc['best']} pc-clock d{pc['depth']}={pc['best']}",
              flush=True)
    b.close()
    p.close()

    with open(os.path.join(outdir, "ply_cost.tsv"), "w") as fh:
        fh.write("fen\tbase_clock_move\tbase_clock_depth\tpc_clock_move\tpc_clock_depth\t"
                 "base_d20\tpc_d20\tbase_d19\tpc_d19\n")
        for r in rows:
            fh.write(f"{r['fen']}\t{r['bc']['best']}\t{r['bc']['depth']}\t{r['pc']['best']}\t"
                     f"{r['pc']['depth']}\t{r['b20']['best']}\t{r['p20']['best']}\t"
                     f"{r['b19']['best']}\t{r['p19']['best']}\n")

    # Positions where PC20's clock run ended shallower than base's.
    shallow = [r for r in rows if r["pc"]["depth"] < r["bc"]["depth"]]
    equal = [r for r in rows if r["pc"]["depth"] == r["bc"]["depth"]]

    def rate(subset, a, c):
        if not subset:
            return 0.0, 0, 0
        n = sum(1 for r in subset if r[a]["best"] == r[c]["best"])
        return 100.0 * n / len(subset), n, len(subset)

    print()
    print(f"positions where PC20's clock run ended shallower than base's: {len(shallow)} of {len(rows)}")
    print(f"positions where both ended at the same depth: {len(equal)}")
    print()
    print("| measurement | agreement | n |")
    print("|---|---|---|")
    for label, subset, a, c in [
        ("A1 PC20-clock vs base-depth20 (on the shallower positions)", shallow, "pc", "b20"),
        ("A2 CONTROL base-clock vs base-depth20 (same positions)", shallow, "bc", "b20"),
        ("A3 PC20-clock vs base-clock (same positions)", shallow, "pc", "bc"),
        ("A4 PC20-clock vs PC20-depth20 (same positions)", shallow, "pc", "p20"),
        ("A5 PC20-depth20 vs base-depth20 (ALL positions, equal fixed depth)", rows, "p20", "b20"),
        ("A6 PC20-depth19 vs base-depth19 (ALL positions, equal fixed depth)", rows, "p19", "b19"),
    ]:
        pct, n, tot = rate(subset, a, c)
        print(f"| {label} | {pct:.1f} % | {n}/{tot} |")

    illegal = 0
    for r in rows:
        for k in ("bc", "pc", "b20", "p20", "b19", "p19"):
            if r[k]["best"] and not legal(r["fen"], r[k]["best"]):
                illegal += 1
    print()
    print(f"illegal moves anywhere: {illegal} (of {6*len(rows)} searches)")
    print()
    print("Depth distribution of the clock runs:")
    print(f"  base clock depths: {sorted(set(r['bc']['depth'] for r in rows))}, "
          f"median {statistics.median([r['bc']['depth'] for r in rows]):.0f}")
    print(f"  PC20 clock depths: {sorted(set(r['pc']['depth'] for r in rows))}, "
          f"median {statistics.median([r['pc']['depth'] for r in rows]):.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
