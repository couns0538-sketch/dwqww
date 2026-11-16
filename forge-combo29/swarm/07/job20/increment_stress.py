#!/usr/bin/env python3
"""increment_stress.py EXE OUTDIR

Targets the clock-plan behaviour I noticed in job19: with an increment comparable to or larger
than the clock, `plan_clock_budget` adds `increment * 3 / 4` on top of `available / (mtg + 1)`, so
with movestogo 40 and a 1000 ms clock + 1000 ms increment the SOFT target is 774 ms and HARD is
792 ms of a 990 ms usable clock.

The question this answers is the only one that matters for play: does that ever LOSE ON TIME?

Method: a self-game with a real decrementing clock and a real increment, over the increment-heavy
controls. Every move records wall time, remaining clock, and whether the engine exceeded what it
had. A loss on time is a failure; a high share of the clock is reported as informational.
"""
import os
import queue
import subprocess
import sys
import time

import chess


class Reader:
    def __init__(self, s):
        self.q = queue.Queue()
        import threading
        threading.Thread(target=self._pump, args=(s,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, t):
        try:
            return self.q.get(timeout=t)
        except queue.Empty:
            return None


def game(exe, clock, inc, mtg, plies, tag, outdir):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)
    rows, fails = [], []

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def drain():
        while True:
            line = r.get(60)
            if line is None:
                raise RuntimeError("no readyok")
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + opt)
    send("isready")
    drain()

    b = chess.Board()
    w = bl = clock
    for ply in range(plies):
        if b.is_game_over():
            break
        send("position fen " + b.fen())
        send("isready")
        drain()
        left = w if b.turn == chess.WHITE else bl
        go = f"go wtime {w} btime {bl} winc {inc} binc {inc}"
        if mtg:
            go += f" movestogo {mtg}"
        t0 = time.monotonic()
        send(go)
        best = None
        while True:
            line = r.get(60)
            if line is None:
                fails.append(f"{tag} ply {ply}: no bestmove (hang)")
                break
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        wall = (time.monotonic() - t0) * 1000.0
        if best is None:
            break
        legal = [m.uci() for m in b.legal_moves]
        if legal and best not in legal:
            fails.append(f"{tag} ply {ply}: illegal {best}")
            break
        share = wall / left if left > 0 else 1.0
        lost = wall > left
        rows.append((ply, left, round(wall, 1), round(share, 3), lost))
        if lost:
            fails.append(f"{tag} ply {ply}: LOST ON TIME, wall {wall:.1f} ms with {left} ms left")
        spend = int(min(wall, left))
        if b.turn == chess.WHITE:
            w = max(0, w - spend) + inc
        else:
            bl = max(0, bl - spend) + inc
        b.push(chess.Move.from_uci(best))
    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    with open(os.path.join(outdir, tag + ".txt"), "w") as fh:
        fh.write("ply left_ms wall_ms share lost\n")
        for row in rows:
            fh.write(f"{row[0]} {row[1]} {row[2]} {row[3]} {row[4]}\n")
    return rows, fails


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    controls = [
        ("inc_eq_clock_mtg40", 1000, 1000, 40, 40),
        ("inc_eq_clock_sudden", 1000, 1000, 0, 30),
        ("inc_gt_clock", 500, 1000, 0, 30),
        ("inc_half_clock_mtg40", 1000, 500, 40, 40),
        ("inc_tiny_clock", 50, 100, 0, 20),
    ]
    allf, allrows = [], []
    for tag, clock, inc, mtg, plies in controls:
        rows, fails = game(exe, clock, inc, mtg, plies, tag, outdir)
        allf.extend(fails)
        allrows.extend(rows)
        if rows:
            worst = max(r[3] for r in rows)
            avg = sum(r[3] for r in rows) / len(rows)
            print(f"{tag:22s} plies {len(rows):3d}  max share of clock {worst:6.3f}  "
                  f"average {avg:6.3f}  losses {sum(1 for r in rows if r[4])}", flush=True)
        else:
            print(f"{tag:22s} NO MOVES PLAYED", flush=True)
    print()
    for f in allf[:20]:
        print("  FAIL " + f)
    if allf:
        print(f"RESULT: {len(allf)} failure(s)")
        sys.exit(1)
    if not allrows:
        print("RESULT: no moves were played, nothing measured")
        sys.exit(2)
    print("RESULT: no loss on time in any increment-heavy control; shares reported above")


if __name__ == "__main__":
    main()
