#!/usr/bin/env python3
"""clock_behaviour.py EXE OUTDIR

A GUI-style clock loop: for each time control, play a short self-game where every move is a
`go wtime .. btime .. winc .. binc [movestogo ..]`, the engine's bestmove is played on a
python-chess board, and the clock is decremented in real time. For every search it records:

  * wall time from sending `go` to reading `bestmove` (monotonic),
  * the engine's own reported `time` and `nodes`,
  * whether the move was legal,
  * whether the search exceeded the time the engine had left (a loss on time).

It also checks the two things a clock bug shows as in normal play: answering with an illegal
move under time pressure, and overrunning the remaining clock.
"""
import os
import queue
import re
import subprocess
import sys
import threading
import time

import chess


class Reader:
    def __init__(self, stream):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, timeout):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None


def play_game(exe, wtime_ms, winc_ms, movestogo, max_plies, outdir, tag):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)
    rows = []
    failures = []

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def drain():
        deadline = time.monotonic() + 60
        while True:
            line = r.get(max(0.01, deadline - time.monotonic()))
            if line is None:
                raise RuntimeError("no readyok")
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    # The book answers clock searches (uci.cpp:525-527 game_search), with NO info depth line.
    # A book move is legitimate, but it would leave this test measuring nothing, so the book
    # is turned off here and book behaviour is reported separately.
    send("setoption name OwnBook value false")
    send("isready")
    drain()

    board = chess.Board()
    white_ms = black_ms = wtime_ms
    for ply in range(max_plies):
        if board.is_game_over():
            break
        fen = board.fen()
        send("position fen " + fen)
        send("isready")
        drain()
        side = "w" if board.turn == chess.WHITE else "b"
        left_ms = white_ms if board.turn == chess.WHITE else black_ms
        go = (f"go wtime {white_ms} btime {black_ms} winc {winc_ms} binc {winc_ms}")
        if movestogo > 0:
            go += f" movestogo {movestogo}"
        t0 = time.monotonic()
        send(go)
        best = None
        eng_time = eng_nodes = None
        while True:
            line = r.get(max(0.01, 30.0))
            if line is None:
                failures.append(f"{tag} ply {ply}: no bestmove in 30 s (hang)")
                break
            if line.startswith("info depth") and " nodes " in line:
                m = re.search(r" nodes (\d+) ", line)
                if m:
                    eng_nodes = int(m.group(1))
                m = re.search(r" time (\d+) ", line)
                if m:
                    eng_time = int(m.group(1))
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        if best is None:
            break
        legal = [m.uci() for m in board.legal_moves]
        ok_move = (best in legal) if legal else (best == "0000")
        overrun = elapsed_ms > left_ms + 5   # 5 ms of measurement slack
        rows.append({"ply": ply, "side": side, "go": go, "left_ms": left_ms,
                     "wall_ms": round(elapsed_ms, 2), "engine_time_ms": eng_time,
                     "nodes": eng_nodes, "bestmove": best, "legal": ok_move,
                     "overrun": overrun, "nodes_missing": eng_nodes is None})
        if eng_nodes is None:
            failures.append(f"{tag} ply {ply}: no 'info depth ... nodes' line, so this search "
                            f"measured nothing (bestmove {best})")
            break
        if not ok_move:
            failures.append(f"{tag} ply {ply}: illegal bestmove {best} in {fen}")
            break
        if overrun:
            failures.append(f"{tag} ply {ply}: took {elapsed_ms:.1f} ms with {left_ms} ms left")
        spend = int(min(elapsed_ms, left_ms))
        if board.turn == chess.WHITE:
            white_ms = max(0, white_ms - spend) + winc_ms
        else:
            black_ms = max(0, black_ms - spend) + winc_ms
        board.push(chess.Move.from_uci(best))

    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, tag + ".txt"), "w") as fh:
        fh.write("go | left_ms | wall_ms | engine_time_ms | nodes | bestmove | legal | overrun\n")
        for row in rows:
            fh.write(f"{row['go']} | {row['left_ms']} | {row['wall_ms']} | "
                     f"{row['engine_time_ms']} | {row['nodes']} | {row['bestmove']} | "
                     f"{row['legal']} | {row['overrun']}\n")
    return rows, failures


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    controls = [
        ("sudden_1000", 1000, 10, 0, 24),
        ("sudden_10000", 10000, 100, 0, 24),
        ("mtg_1", 1000, 0, 1, 12),
        ("mtg_2", 1000, 0, 2, 12),
        ("mtg_40", 1000, 0, 40, 16),
        ("tiny_100", 100, 0, 0, 12),
        ("tiny_30", 30, 0, 0, 10),
        ("tiny_10", 10, 0, 0, 8),
        ("zero_0", 0, 0, 0, 6),
    ]
    all_failures = []
    for tag, wt, inc, mtg, plies in controls:
        rows, failures = play_game(exe, wt, inc, mtg, plies, outdir, tag)
        all_failures.extend(failures)
        overruns = sum(1 for r in rows if r["overrun"])
        missing = sum(1 for r in rows if r["nodes_missing"])
        worst = max((r["wall_ms"] for r in rows), default=0.0)
        print(f"{tag:14s} plies {len(rows):3d}  overruns {overruns}  rows without nodes {missing}  "
              f"worst wall {worst:8.1f} ms", flush=True)
    print()
    for f in all_failures[:20]:
        print("  FAIL " + f)
    if all_failures:
        print(f"RESULT: {len(all_failures)} failure(s)")
        sys.exit(1)
    print("RESULT: no illegal move under time pressure, no overrun of the remaining clock")


if __name__ == "__main__":
    main()
