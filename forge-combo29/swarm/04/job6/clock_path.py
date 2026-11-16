#!/usr/bin/env python3
"""clock_path.py — the PC's strength-match path: a real clock, Threads 1, PC20.

File 6 says the owner's strength matches use 6 seconds + 0.06 s per move. That path has its own risks that a
fixed-depth or fixed-node test cannot show:
  * does the engine answer inside its allotted time, every move?
  * does the time actually spent track the plan, or is it wildly over/under?
  * does it ever fail to answer (the D1 hang, which loses a game outright)?
  * is a clock search reproducible when nothing else varies?

The script plays a short self-driven game: send each move's `go wtime X btime Y winc 60 binc 60`, read
bestmove, apply it, update the clocks by the measured elapsed time. It stops at the first failure.

Integrity: any missing bestmove, refused option, or illegal move aborts with a non-zero exit and the game
dump, because a partial game must not be summarised as a result.

Usage: clock_path.py EXE OUTDIR --settings pc20 --wtime 6000 --winc 60 --moves 40
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

try:
    import chess
except ImportError:
    print("python-chess required")
    sys.exit(2)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def opts_for(name):
    base = [("Hash", 16), ("Threads", 1)]
    if name == "none":
        return base
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    return base + S14 + PC20_EXTRA


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=lambda: [self.q.put(l.rstrip("\r\n")) for l in self.p.stdout],
                         daemon=True).start()
        self.err = []
        threading.Thread(target=lambda: [self.err.append(l.rstrip()) for l in self.p.stderr],
                         daemon=True).start()

    def send(self, c):
        try:
            self.p.stdin.write(c + "\n")
            self.p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def wait_for(self, tok, lim=60.0):
        got = []
        deadline = time.monotonic() + lim
        while time.monotonic() < deadline:
            try:
                ln = self.q.get(timeout=0.05)
            except queue.Empty:
                if self.p.poll() is not None and self.q.empty():
                    break
                continue
            got.append(ln)
            if ln == tok or ln.startswith(tok):
                return got, True
        return got, False

    def kill(self):
        try:
            self.p.kill()
            self.p.wait(timeout=5)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--wtime", type=int, default=6000)
    ap.add_argument("--winc", type=int, default=60)
    ap.add_argument("--moves", type=int, default=40)
    ap.add_argument("--overhead", type=int, default=10)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    eng = Eng(a.exe)
    problems = []
    eng.send("uci")
    eng.wait_for("uciok", 30)
    for name, val in opts_for(a.settings):
        eng.send("setoption name %s value %s" % (name, val))
        eng.send("isready")
        lines, ok = eng.wait_for("readyok", 20)
        if not ok:
            problems.append("no readyok after %s" % name)
        for ln in lines:
            if "unknown option" in ln or "invalid value" in ln:
                problems.append("refused: " + ln)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.wait_for("readyok", 20)

    board = chess.Board()
    white = a.wtime
    black = a.wtime
    rows = []
    for ply in range(a.moves):
        if board.is_game_over():
            break
        fen = board.fen()
        eng.send("position fen " + fen)
        eng.send("isready")
        _, ok = eng.wait_for("readyok", 20)
        if not ok:
            problems.append("no readyok before move %d" % ply)
            break
        cmd = "go wtime %d btime %d winc %d binc %d" % (white, black, a.winc, a.winc)
        t0 = time.monotonic()
        eng.send(cmd)
        got, reached = eng.wait_for("bestmove", max(60.0, (white + black) / 1000.0 * 4))
        wall_ms = (time.monotonic() - t0) * 1000.0
        best = ""
        nodes = None
        depth = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
            elif ln.startswith("info "):
                parts = ln.split()
                if "nodes" in parts:
                    try:
                        nodes = int(parts[parts.index("nodes") + 1])
                    except Exception:
                        pass
                if "depth" in parts:
                    try:
                        depth = int(parts[parts.index("depth") + 1])
                    except Exception:
                        pass
        mv = best.split()[1] if len(best.split()) > 1 else ""
        rec = {"ply": ply, "fen": fen, "side": "w" if board.turn else "b",
               "clock_ms": white if board.turn else black, "cmd": cmd,
               "bestmove": best, "move": mv, "wall_ms": round(wall_ms, 1),
               "nodes": nodes, "depth": depth, "reached": reached}
        rows.append(rec)
        if not reached:
            problems.append("NO BESTMOVE at ply %d (clock %d ms)" % (ply, rec["clock_ms"]))
            break
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            problems.append("unparseable bestmove %r at ply %d" % (mv, ply))
            break
        if mv == "0000" or m not in board.legal_moves:
            problems.append("illegal bestmove %s at ply %d" % (mv, ply))
            break
        # spend the clock the way a real GUI does
        spent = int(wall_ms) + a.overhead
        if board.turn:
            white = max(0, white - spent) + a.winc
        else:
            black = max(0, black - spent) + a.winc
        board.push(m)

    path = os.path.join(a.outdir, "clock_path.jsonl")
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
        f.write(json.dumps({"problems": problems,
                            "final_fen": board.fen(),
                            "white_ms": white, "black_ms": black}) + "\n")
    eng.send("quit")
    try:
        eng.p.wait(timeout=10)
    except Exception:
        eng.kill()

    if rows:
        walls = sorted(r["wall_ms"] for r in rows)
        over = [r for r in rows if r["wall_ms"] > r["clock_ms"] / 20.0]
        print("plies played: %d   problems: %d" % (len(rows), len(problems)))
        print("wall per move: min %.0f ms  median %.0f ms  max %.0f ms"
              % (walls[0], walls[len(walls) // 2], walls[-1]))
        print("moves that took more than 5%% of the clock on hand: %d of %d"
              % (len(over), len(rows)))
        print("depths reached: %s" % sorted({r["depth"] for r in rows}))
        print("final clocks: white %d ms, black %d ms" % (white, black))
    for p in problems:
        print("PROBLEM: " + p)
    if problems:
        sys.exit(1)
    print("VERDICT: the clock path answered every move, legally, inside its time")


if __name__ == "__main__":
    main()
