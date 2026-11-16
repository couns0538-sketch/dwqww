#!/usr/bin/env python3
"""resolve_15f35.py EXE OUTDIR — seat 15's "would have forfeited at ~165 plies" vs my structural result.

THE CONFLICT, stated exactly:
  seat 15 (15-F35): 36 games at 6 s + 0.06, 0 forfeits, clock never <= 0, but "a game reaching ~165 plies
                    would have forfeited" because the median 105 ms search drains ~73 ms net per move and
                    6000/73 is about 82 moves of one side.
  seat 28 (S-F42):  the search is capped at `clock - MoveOverhead`, and a flag needs `> clock + increment`,
                    so the drain per move is at most `MoveOverhead + increment` = 70 ms in the OTHER
                    direction - the engine can never spend more than the clock allows, therefore it cannot
                    drain to zero.

Both cannot be right. The difference is WHAT drains the clock:
  - the SEARCH, which is capped at 60-80 % of what remains (my claim), or
  - the fact that a move which spends MORE than `increment` reduces the clock by the difference, which is
    true but BOUNDED: the reduction is at most `wall - 60`, and `wall <= clock - 10`, so the new clock is
    `clock - wall + 60 >= 10 + 60 = 70 ms`. The clock therefore can never go below ~70 ms, whatever it was.

So seat 15's arithmetic (6000/73 = 82 moves) assumes a CONSTANT 73 ms drain, but the drain SHRINKS with the
clock because the plan shrinks with it. That is the error to demonstrate: the drain is a function of the
clock, and near the bottom it goes to zero.

This script proves it two ways:
  1. ARITHMETIC: iterate the clock rule with the engine's own plan, from 6000 ms, using a worst-case
     assumption that every search spends its full HARD plan. Show the clock approaching a floor, not zero.
  2. EMPIRICAL: play one very long game (raised ply cap) from a position that avoids early repetition, at
     6 s + 0.06, and report the clock at the end and whether it dips below 70 ms.

Usage: resolve_15f35.py EXE OUTDIR [MAX_PLIES]
"""
import os
import sys
import time

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
START_MS, INC = 6000, 60
OVERHEAD, SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT = 10, 22, 75, 60, 5


def hard_plan(clock):
    if clock <= OVERHEAD:
        return 0
    avail = clock - OVERHEAD
    soft = avail // SOFT_DIV + INC * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    hard = max(1, min(hard, avail))
    return hard


def arithmetic():
    print("## 1. ARITHMETIC: iterate the clock rule with a WORST-CASE search (always spends its full hard plan)")
    print()
    print("`clock' = clock - hard(clock) + 60`, which is the most a move can cost.")
    print()
    print("| move | clock ms | hard plan ms | spend | clock after |")
    print("|---|---|---|---|---|")
    clock = float(START_MS)
    rows = []
    for m in range(1, 201):
        h = hard_plan(clock)
        after = clock - h + INC
        rows.append((m, clock, h, h, after))
        if m <= 10 or m % 25 == 0:
            print(f"| {m} | {clock:.0f} | {h} | {h} | {after:.0f} |")
        if abs(after - clock) < 0.5:
            print(f"| ... | **the clock stops falling at {after:.0f} ms after move {m}** | | | |")
            break
        clock = after
    floor = min(r[4] for r in rows)
    print()
    print(f"lowest clock reachable under a worst-case spend: **{floor:.0f} ms** "
          f"(never below MoveOverhead + increment = {OVERHEAD + INC} ms)")
    print()
    print("Seat 15's 6000/73 = 82 moves assumes a CONSTANT 73 ms drain. The drain is not constant: it is")
    print("`hard(clock) - 60`, which SHRINKS as the clock shrinks, reaching zero at the floor. That is why the")
    print("clock approaches a floor instead of crossing zero.")
    print()


def make(exe):
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
    return eng


def ask(eng, fen, wtime, btime):
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    t0 = time.monotonic()
    eng.send(f"go wtime {max(1,int(wtime))} btime {max(1,int(btime))} winc {INC} binc {INC}")
    out, ok = eng.read_until("bestmove", 40)
    t1 = time.monotonic()
    best = ""
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
    return best, (t1 - t0) * 1000.0, ok


def empirical(exe, max_plies):
    """One long game from a position that cannot repeat quickly: many pawns, so pushes keep it moving."""
    start = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8"
    eng = make(exe)
    board = chess.Board(start)
    clock = {chess.WHITE: float(START_MS), chess.BLACK: float(START_MS)}
    rows = []
    try:
        for ply in range(max_plies):
            side = board.turn
            if board.is_game_over(claim_draw=True) or not list(board.legal_moves):
                break
            before = clock[side]
            best, wall, ok = ask(eng, board.fen(), clock[chess.WHITE], clock[chess.BLACK])
            if not ok or not best:
                break
            try:
                mv = chess.Move.from_uci(best)
            except ValueError:
                break
            if mv not in board.legal_moves:
                break
            clock[side] = before - wall + INC
            rows.append((ply, side, before, wall, clock[side]))
            if clock[side] <= 0:
                break
            board.push(mv)
    finally:
        eng.close()
    return rows


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    max_plies = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    os.makedirs(outdir, exist_ok=True)
    arithmetic()
    print(f"## 2. EMPIRICAL: one long game at 6 s + 0.06, ply cap {max_plies}")
    print()
    rows = empirical(exe, max_plies)
    if not rows:
        print("no moves")
        return 1
    clocks = [r[4] for r in rows]
    print("| metric | value |")
    print("|---|---|")
    print(f"| plies played | {len(rows)} |")
    print(f"| lowest clock reached | **{min(clocks):.0f} ms** |")
    print(f"| clock at the end (last side) | {clocks[-1]:.0f} ms |")
    print(f"| plies with clock below 200 ms | {sum(1 for c in clocks if c < 200)} |")
    print(f"| plies with clock below 70 ms | {sum(1 for c in clocks if c < 70)} |")
    print(f"| forfeits (clock <= 0) | {sum(1 for c in clocks if c <= 0)} |")
    print()
    print("last 8 moves:")
    print()
    print("| ply | side | clock before | wall ms | clock after |")
    print("|---|---|---|---|---|")
    for r in rows[-8:]:
        print(f"| {r[0]} | {r[1]} | {r[2]:.0f} | {r[3]:.1f} | {r[4]:.0f} |")
    with open(os.path.join(outdir, "resolve.tsv"), "w") as fh:
        fh.write("ply\tside\tclock_before\twall_ms\tclock_after\n")
        for r in rows:
            fh.write(f"{r[0]}\t{r[1]}\t{r[2]:.0f}\t{r[3]:.1f}\t{r[4]:.0f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
