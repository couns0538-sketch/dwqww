#!/usr/bin/env python3
"""Real-clock self-play harness for the time manager (job FB2-J4).

Plays engine-vs-engine games over UCI with a GUI-style clock: the time charged to a move is the wall time from
sending `go` to receiving `bestmove`. A flag loss is a move whose charged time exceeds the remaining clock. Each
side gets its own engine process; options are set per side (`--opt-white`, `--opt-black`, repeatable Name=value).

    fable_timeman_games.py <forge.exe> --tc 1+0.01 --games 100 --opt-white TimeManV2=true --opt-black TimeManV2=true
       [--overhead 10] [--max-plies 300] [--seed 1] [--out summary.json] [--random-plies 6]

Reports: games, moves, flag losses, max overshoot over the hard deadline (the engine's own deadline is not
observable, so the report gives max(charged - remaining_before) and the minimum remaining clock), mean charged
time per move as a fraction of the remaining time, and the result distribution.
"""
import argparse
import json
import random
import subprocess
import sys
import time

import chess


class Engine:
    def __init__(self, exe, opts, overhead):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.send("uci")
        self.wait("uciok")
        self.send(f"setoption name Move Overhead value {overhead}")
        self.send("setoption name OwnBook value false")
        for o in opts:
            name, value = o.split("=", 1)
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.wait("readyok")

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def wait(self, token):
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("engine died")
            if line.startswith(token):
                return line.strip()

    def go(self, fen_moves, wtime, btime, winc, binc):
        self.send("position startpos moves " + fen_moves if fen_moves else "position startpos")
        self.send("isready")
        self.wait("readyok")
        t0 = time.perf_counter()
        self.send(f"go wtime {int(wtime)} btime {int(btime)} winc {int(winc)} binc {int(binc)}")
        line = self.wait("bestmove")
        used = (time.perf_counter() - t0) * 1000.0
        return line.split()[1], used

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exe")
    ap.add_argument("--tc", default="1+0.01")
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--opt-white", action="append", default=[])
    ap.add_argument("--opt-black", action="append", default=[])
    ap.add_argument("--overhead", type=int, default=10)
    ap.add_argument("--max-plies", type=int, default=300)
    ap.add_argument("--random-plies", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out")
    args = ap.parse_args()
    base_s, inc_s = args.tc.split("+")
    base_ms, inc_ms = float(base_s) * 1000.0, float(inc_s) * 1000.0
    rng = random.Random(args.seed)
    white = Engine(args.exe, args.opt_white, args.overhead)
    black = Engine(args.exe, args.opt_black, args.overhead)
    stats = {"tc": args.tc, "games": 0, "moves": 0, "flags": 0, "flag_details": [], "max_over_remaining_ms": -1e9, "min_clock_ms": 1e9,
             "sum_fraction": 0.0, "max_fraction": 0.0, "results": {"1-0": 0, "0-1": 0, "1/2-1/2": 0}, "white_opts": args.opt_white, "black_opts": args.opt_black,
             "max_used_ms": 0.0, "moves_over_half_clock": 0}
    t_start = time.time()
    for g in range(args.games):
        board = chess.Board()
        for _ in range(args.random_plies):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if board.is_game_over():
            continue
        clocks = {chess.WHITE: base_ms, chess.BLACK: base_ms}
        moves_played = []
        for m in board.move_stack:
            moves_played.append(m.uci())
        flagged = None
        plies = 0
        while not board.is_game_over(claim_draw=True) and plies < args.max_plies:
            side = board.turn
            eng = white if side else black
            remaining = clocks[side]
            mv, used = eng.go(" ".join(moves_played), clocks[chess.WHITE], clocks[chess.BLACK], inc_ms, inc_ms)
            stats["moves"] += 1
            stats["max_used_ms"] = max(stats["max_used_ms"], used)
            frac = used / max(remaining, 1.0)
            stats["sum_fraction"] += frac
            stats["max_fraction"] = max(stats["max_fraction"], frac)
            stats["max_over_remaining_ms"] = max(stats["max_over_remaining_ms"], used - remaining)
            if used > remaining * 0.5:
                stats["moves_over_half_clock"] += 1
            if used > remaining:
                flagged = side
                stats["flags"] += 1
                if len(stats["flag_details"]) < 20:
                    stats["flag_details"].append({"game": g, "ply": plies, "remaining_ms": remaining, "used_ms": used, "side": "white" if side else "black"})
                break
            clocks[side] = remaining - used + inc_ms
            stats["min_clock_ms"] = min(stats["min_clock_ms"], clocks[side])
            move = chess.Move.from_uci(mv)
            if move not in board.legal_moves:
                raise SystemExit(f"illegal move {mv} in {board.fen()}")
            board.push(move)
            moves_played.append(mv)
            plies += 1
        if flagged is not None:
            result = "0-1" if flagged == chess.WHITE else "1-0"
        else:
            result = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "1/2-1/2"
        stats["results"][result] = stats["results"].get(result, 0) + 1
        stats["games"] += 1
        if (g + 1) % 10 == 0:
            print(f"game {g + 1}: moves {stats['moves']} flags {stats['flags']} min clock {stats['min_clock_ms']:.0f} ms max used {stats['max_used_ms']:.0f} ms "
                  f"elapsed {time.time() - t_start:.0f}s", flush=True)
    white.quit()
    black.quit()
    stats["mean_fraction"] = stats["sum_fraction"] / max(stats["moves"], 1)
    stats["seconds"] = round(time.time() - t_start, 1)
    print(json.dumps({k: v for k, v in stats.items() if k != "flag_details"}, sort_keys=True))
    print("PASS" if stats["flags"] == 0 else "FAIL")
    if args.out:
        with open(args.out, "w", newline="\n") as f:
            json.dump(stats, f, indent=1, sort_keys=True)
    sys.exit(0 if stats["flags"] == 0 else 1)


if __name__ == "__main__":
    main()
