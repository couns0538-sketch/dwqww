#!/usr/bin/env python3
"""game_p90.py EXE LABEL OUTDIR [GAMES] [MOVETIME_TRACE]

Per-move search-time distribution at the owner's real control: 6 s + 0.06 per move, PC20, Threads 1,
Hash 16, on REAL GAME positions (positions that arise in actual engine-vs-engine games, not a FEN set).

Why a game and not a FEN set: the owner's question is whether the clock runs out, and that depends on what
the clock actually reads. So this plays real games with a REAL COUNTDOWN:
  - each side starts at 6000 ms;
  - after each move, that side's clock decreases by the wall time the search took and increases by 60 ms;
  - the engine is sent the ACTUAL remaining clock, so the plan shrinks as the game goes on (this is what a
    GUI does; my earlier constant-clock runs were the unrealistic case — S-F30/S-F32 showed the difference).
  - a side whose clock reaches 0 before its move is flagged and LOSES on time (standard flag).

Referee is python-chess: legal moves only, draws by the same rules file 6 names (third occurrence and the
100th half-move without capture/pawn move end the game, 50-move and repetition scored as draws), and the
game ends at 250 plies or a terminal position.

Recorded per move: side, clock before, search wall ms, clock after, depth, nodes, and the move. Then the
report gives the distribution of SEARCH TIMES (the number the owner asked for) and the clock trajectory.

Usage: game_p90.py EXE LABEL OUTDIR [GAMES]
"""
import os
import statistics
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
START_MS, INC_MS, MAX_PLIES = 6000, 60, 250


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
    """One move at the given clocks. Returns (move, wall_ms, depth, nodes, flagged)."""
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    wt = max(1, int(wtime))
    bt = max(1, int(btime))
    t0 = time.monotonic()
    eng.send(f"go wtime {wt} btime {bt} winc {INC_MS} binc {INC_MS}")
    out, ok = eng.read_until("bestmove", 30)
    t1 = time.monotonic()
    best, depth, nodes = "", 0, 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
    return best, (t1 - t0) * 1000.0, depth, nodes, (not ok)


def play(exe, game_no):
    eng = make(exe)
    board = chess.Board()
    clock = {chess.WHITE: float(START_MS), chess.BLACK: float(START_MS)}
    moves = []
    result = "unfinished"
    flag = None
    try:
        for ply in range(MAX_PLIES):
            side = board.turn
            if board.is_game_over(claim_draw=True) or not list(board.legal_moves):
                if board.is_checkmate():
                    result = "checkmate"
                else:
                    result = "draw"
                break
            before = clock[side]
            best, wall, depth, nodes, noresp = ask(eng, board.fen(), clock[chess.WHITE],
                                                   clock[chess.BLACK])
            if noresp or not best:
                result = "no-response"
                break
            try:
                mv = chess.Move.from_uci(best)
            except ValueError:
                result = "illegal-unparsable"
                break
            if mv not in board.legal_moves:
                result = "illegal-move"
                break
            # The clock: time spent, plus the increment. A GUI flags at zero.
            clock[side] = before - wall + INC_MS
            flagged = clock[side] <= 0
            moves.append({"ply": ply, "side": "w" if side == chess.WHITE else "b",
                          "clock_before": before, "wall": wall, "clock_after": clock[side],
                          "depth": depth, "nodes": nodes, "move": best, "flag": flagged,
                          "fen": board.fen()})
            if flagged:
                result = "flag"
                flag = "w" if side == chess.WHITE else "b"
                break
            board.push(mv)
    finally:
        eng.close()
    return {"game": game_no, "moves": moves, "result": result, "flag": flag,
            "plies": len(moves), "final": board.fen()}


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    exe, label, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    games = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    os.makedirs(outdir, exist_ok=True)
    all_moves = []
    game_rows = []
    print(f"{label}: {games} games at {START_MS} ms + {INC_MS}/move, real countdown, PC20, Threads 1")
    for g in range(games):
        r = play(exe, g + 1)
        game_rows.append(r)
        all_moves.extend(r["moves"])
        clocks = [m["clock_after"] for m in r["moves"]]
        print(f"  game {g+1}: {r['plies']} plies, result {r['result']}"
              f"{' flag=' + r['flag'] if r['flag'] else ''}, "
              f"min clock {min(clocks) if clocks else 0:.0f} ms, "
              f"final clocks w/b", flush=True)

    with open(os.path.join(outdir, f"gamep90_{label}.tsv"), "w") as fh:
        fh.write("game\tply\tside\tclock_before\twall_ms\tclock_after\tdepth\tnodes\tmove\tflagged\n")
        for r in game_rows:
            for m in r["moves"]:
                fh.write(f"{r['game']}\t{m['ply']}\t{m['side']}\t{m['clock_before']:.0f}\t"
                         f"{m['wall']:.1f}\t{m['clock_after']:.0f}\t{m['depth']}\t{m['nodes']}\t"
                         f"{m['move']}\t{m['flag']}\n")
    with open(os.path.join(outdir, f"gamep90_{label}.games.txt"), "w") as fh:
        for r in game_rows:
            fh.write(f"game {r['game']}: plies {r['plies']} result {r['result']} "
                     f"flag {r['flag']} final {r['final']}\n")

    if not all_moves:
        print("no moves recorded")
        return 1
    walls = [m["wall"] for m in all_moves]
    print()
    print("## Per-move SEARCH TIME distribution (the number asked for)")
    print()
    print("| metric | value |")
    print("|---|---|")
    print(f"| moves | {len(walls)} |")
    print(f"| median | {statistics.median(walls):.0f} ms |")
    print(f"| 75th | {pct(walls,75):.0f} ms |")
    print(f"| **90th** | **{pct(walls,90):.0f} ms** |")
    print(f"| 95th | {pct(walls,95):.0f} ms |")
    print(f"| 99th | {pct(walls,99):.0f} ms |")
    print(f"| max | {max(walls):.0f} ms |")
    print(f"| moves where search > {INC_MS} ms increment | "
          f"{sum(1 for w in walls if w > INC_MS)}/{len(walls)} "
          f"({100.0*sum(1 for w in walls if w > INC_MS)/len(walls):.0f} %) |")
    print()
    print("## Clock trajectory")
    print()
    print("| game | plies | result | min clock reached | final white | final black |")
    print("|---|---|---|---|---|---|")
    for r in game_rows:
        clocks = [m["clock_after"] for m in r["moves"]]
        w = clocks[-1] if r["moves"] and r["moves"][-1]["side"] == "w" else (
            r["moves"][-2]["clock_after"] if len(r["moves"]) > 1 else START_MS)
        b = clocks[-1] if r["moves"] and r["moves"][-1]["side"] == "b" else (
            r["moves"][-2]["clock_after"] if len(r["moves"]) > 1 else START_MS)
        print(f"| {r['game']} | {r['plies']} | {r['result']}"
              f"{' (' + r['flag'] + ' flagged)' if r['flag'] else ''} | "
              f"{min(clocks) if clocks else START_MS:.0f} ms | {w:.0f} | {b:.0f} |")
    print()
    print(f"games flagged: {sum(1 for r in game_rows if r['flag'])} of {len(game_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
