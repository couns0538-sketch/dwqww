#!/usr/bin/env python3
"""playgames.py EXE OPENINGSFILE [--games N] [--startbase MS] [--inc MS] [--plycap N]

PC build vs itself under PC20, Threads 1, Hash 16, with a real clock:
each side starts with `startbase` ms and gains `inc` ms per own move. The clock is decremented by the
MEASURED wall time of that side's search (monotonic, from sending `go` to reading `bestmove`), which is
what a real match program does.

A FORFEIT is recorded when, at the start of a move, a side's remaining clock is <= 0 — that is the
"lost on time" condition and it is the whole question this job exists to answer. A forfeit is never
confused with a resignation or an adjudicated result.

Every move is verified legal with python-chess as the game is played; an illegal move aborts that game
and is reported.

One engine process per side for the whole run, `ucinewgame` between games.
"""
import argparse
import json
import queue
import re
import subprocess
import threading
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()

        def rd():
            for line in self.p.stdout:
                self.q.put(line.rstrip("\n"))
            self.q.put(None)

        threading.Thread(target=rd, daemon=True).start()
        self.send("uci")
        self.wait(lambda l: l.startswith("uciok"), 30)
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        for k, v in PC20:
            self.send("setoption name %s value %s" % (k, v))
        self.send("isready")
        self.wait(lambda l: l == "readyok", 30)

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def wait(self, pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return None
            try:
                line = self.q.get(timeout=rem)
            except queue.Empty:
                return None
            if line is None:
                return None
            if pred(line):
                return line

    def newgame(self):
        self.send("ucinewgame")
        self.send("isready")
        self.wait(lambda l: l == "readyok", 30)

    def go(self, poscmd, wtime, btime, inc, limit=30.0):
        self.send(poscmd)
        self.send("isready")
        self.wait(lambda l: l == "readyok", 30)
        t0 = time.monotonic()
        self.send("go wtime %d btime %d winc %d binc %d" % (wtime, btime, inc, inc))
        infos = []
        bm = None
        while time.monotonic() - t0 < limit:
            try:
                line = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                break
            if line.startswith("info depth"):
                infos.append(line)
            if line.startswith("bestmove"):
                bm = line
                break
        wall = time.monotonic() - t0
        nodes = None
        if infos:
            m = re.search(r"\bnodes (\d+)", infos[-1])
            nodes = int(m.group(1)) if m else None
        return (bm.split()[1] if bm and len(bm.split()) > 1 else None, int(wall * 1000), nodes)

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def load_openings(path, n):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            f = line.split()
            out.append(" ".join(f[:4]) + " 0 1" if len(f) == 4 else " ".join(f[:6]))
        if len(out) >= n:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("openings")
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--startbase", type=int, default=6000)
    ap.add_argument("--inc", type=int, default=60)
    ap.add_argument("--plycap", type=int, default=200)
    ap.add_argument("--out", default="games.jsonl")
    a = ap.parse_args()
    opens = load_openings(a.openings, a.games)
    white = Engine(a.exe)
    black = Engine(a.exe)
    results = []
    print("exe: %s  PC20  Threads 1  %d games, clock %d ms + %d ms/move, ply cap %d"
          % (a.exe, len(opens), a.startbase, a.inc, a.plycap), flush=True)
    try:
        for gi, fen in enumerate(opens):
            white.newgame()
            black.newgame()
            board = chess.Board(fen)
            # engine state per side: keep the full move list so `position fen ... moves` is exact
            moves = []
            clock = {chess.WHITE: a.startbase, chess.BLACK: a.startbase}
            forfeit = None
            illegal = None
            plies = 0
            used = []
            while plies < a.plycap:
                if board.is_game_over(claim_draw=False):
                    break
                side = board.turn
                # FORFEIT CHECK: the side to move has no time left
                if clock[side] <= 0:
                    forfeit = "white" if side == chess.WHITE else "black"
                    break
                poscmd = "position fen " + fen + ((" moves " + " ".join(moves)) if moves else "")
                bm, wall, nodes = white.go(poscmd, clock[chess.WHITE], clock[chess.BLACK], a.inc) \
                    if side == chess.WHITE else \
                    black.go(poscmd, clock[chess.WHITE], clock[chess.BLACK], a.inc)
                clock[side] -= wall
                used.append(wall)
                if bm is None:
                    forfeit = ("white" if side == chess.WHITE else "black") + " (no bestmove)"
                    break
                if bm == "0000":
                    break
                try:
                    mv = chess.Move.from_uci(bm)
                except ValueError:
                    illegal = bm
                    break
                if mv not in board.legal_moves:
                    illegal = bm
                    break
                board.push(mv)
                moves.append(bm)
                clock[side] += a.inc
                plies += 1
            if board.is_checkmate():
                res = "checkmate: " + ("white" if board.turn == chess.BLACK else "black") + " wins"
            elif board.is_stalemate():
                res = "stalemate"
            elif board.is_insufficient_material():
                res = "insufficient material"
            elif forfeit:
                res = "FORFEIT by " + forfeit
            elif illegal:
                res = "ILLEGAL MOVE " + illegal
            elif plies >= a.plycap:
                res = "ply cap"
            else:
                res = "draw by rule"
            med = sorted(used)[len(used) // 2] if used else 0
            print("game %2d %-58s plies %3d  %-34s med %4d ms  clocks w%d b%d"
                  % (gi + 1, fen[:58], plies, res, med, clock[chess.WHITE], clock[chess.BLACK]),
                  flush=True)
            results.append({"game": gi + 1, "fen": fen, "plies": plies, "result": res,
                            "forfeit": forfeit, "illegal": illegal, "median_ms": med,
                            "clock_white": clock[chess.WHITE], "clock_black": clock[chess.BLACK],
                            "used": used, "moves": moves})
            with open(a.out, "w", encoding="utf-8") as fh:
                for r in results:
                    fh.write(json.dumps(r) + "\n")
    finally:
        white.quit()
        black.quit()
    nf = sum(1 for r in results if r["forfeit"])
    ni = sum(1 for r in results if r["illegal"])
    print("\nGAMES %d   FORFEITS %d   ILLEGAL MOVES %d" % (len(results), nf, ni), flush=True)
    allused = [m for r in results for m in r["used"]]
    if allused:
        allused.sort()
        print("clock used per move across all games: median %d ms, max %d ms, n=%d"
              % (allused[len(allused) // 2], allused[-1], len(allused)), flush=True)


if __name__ == "__main__":
    main()
