#!/usr/bin/env python3
"""seat 17: the owner's match clock, 6 s + 0.06, on the PC build under PC20.

File 6 ranks this path highest: his strength matches use a 6-second clock with 0.06 s increment.
A time forfeit here loses a game, so the question is: does the engine ever exceed the time it has?

Method (Threads 1, Hash 16, PC20, read to bestmove, fresh process per game):
 - 20 short self-play games would be slow, so this plays ONE side's moves down a real game line:
   for each of N positions, send `go wtime <left> btime <left> winc 60 binc 60`, time the wall clock,
   subtract the wall time from the side's remaining clock and add the increment, and repeat.
 - A move that takes longer than the remaining time is a FORFEIT and is recorded.
 - Also records: wall time per move, the engine's own reported `time`, and the overshoot of the
   engine's soft plan (we cannot see the plan, so we compare wall against the time left).

usage: matchclock.py <exe> <outdir> [moves_per_game]
"""
import json
import os
import subprocess
import sys
import time

import chess

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA

START_FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"


def play(exe, moves, outdir, initial_ms=6000, inc_ms=60):
    """Drive one game from START_FEN for `moves` plies with the 6+0.06 clock."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    log = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        while True:
            reply = proc.stdout.readline()
            if reply == "":
                return None
            log.append(reply.rstrip("\n"))
            if pred(reply):
                return reply

    board = chess.Board(START_FEN)
    white_ms = black_ms = initial_ms
    rows = []
    send("uci")
    read_until(lambda l: l.strip() == "uciok")
    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        read_until(lambda l: l.strip() == "readyok")
    try:
        for ply in range(moves):
            if board.is_game_over():
                break
            send("position fen " + START_FEN + (" moves " + " ".join(m.uci() for m in board.move_stack)
                                               if board.move_stack else ""))
            send("isready")
            read_until(lambda l: l.strip() == "readyok")
            go = "go wtime %d btime %d winc %d binc %d" % (white_ms, black_ms, inc_ms, inc_ms)
            start = time.monotonic()
            send(go)
            best = read_until(lambda l: l.startswith("bestmove"))
            wall_ms = (time.monotonic() - start) * 1000.0
            if best is None:
                rows.append({"ply": ply, "forfeit": True, "reason": "no bestmove",
                             "wall_ms": round(wall_ms, 1)})
                break
            move_txt = best.split()[1]
            # the engine's own reported time, last info line
            engine_time = None
            for line in reversed(log):
                if line.startswith("info depth") and " time " in line:
                    try:
                        engine_time = int(line.split(" time ")[1].split()[0])
                    except (IndexError, ValueError):
                        pass
                    break
            side_white = board.turn == chess.WHITE
            left = white_ms if side_white else black_ms
            overrun = wall_ms > left
            rows.append({
                "ply": ply, "side": "w" if side_white else "b",
                "move": move_txt, "wall_ms": round(wall_ms, 1),
                "engine_time_ms": engine_time,
                "clock_before_ms": left,
                "overrun_clock": overrun,
            })
            if overrun:
                rows[-1]["forfeit"] = True
                break
            if side_white:
                white_ms = white_ms - int(wall_ms) + inc_ms
            else:
                black_ms = black_ms - int(wall_ms) + inc_ms
            if move_txt == "0000":
                rows[-1]["note"] = "engine returned 0000"
                break
            try:
                board.push_uci(move_txt)
            except ValueError:
                rows[-1]["note"] = "illegal move returned: " + move_txt
                break
    finally:
        try:
            send("quit")
            proc.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    open(os.path.join(outdir, "game.log"), "w").write("\n".join(log) + "\n")
    return rows, white_ms, black_ms


def main():
    exe, outdir = sys.argv[1:3]
    moves = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    os.makedirs(outdir, exist_ok=True)
    rows, w, b = play(exe, moves, outdir)
    walls = [r["wall_ms"] for r in rows if "wall_ms" in r and not r.get("forfeit")]
    forfeits = [r for r in rows if r.get("forfeit")]
    illegal = [r for r in rows if "illegal" in r.get("note", "")]
    walls_sorted = sorted(walls)
    summary = {
        "moves_played": len(rows),
        "forfeits": len(forfeits),
        "illegal_moves": len(illegal),
        "clock_left_white_ms": w,
        "clock_left_black_ms": b,
        "wall_ms_median": walls_sorted[len(walls_sorted) // 2] if walls_sorted else None,
        "wall_ms_max": max(walls) if walls else None,
        "wall_ms_over_200": sum(1 for x in walls if x > 200),
        "move_list": [r.get("move") for r in rows],
    }
    json.dump({"summary": summary, "rows": rows}, open(os.path.join(outdir, "matchclock.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    if forfeits:
        print("FORFEITS:", json.dumps(forfeits, indent=1))
    if illegal:
        print("ILLEGAL:", json.dumps(illegal, indent=1))


if __name__ == "__main__":
    main()
