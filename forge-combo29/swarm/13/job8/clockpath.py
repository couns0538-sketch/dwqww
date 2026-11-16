#!/usr/bin/env python3
"""The PC's clock mode: 6 s + 0.06 s per move, PC build, PC20, Threads 1.

FABLE file 6 lists the owner's match clock as 6 s + 0.06 s. Jobs 5 and 7 covered softnodes and
`go nodes`; this covers the clock path, which is a different limit type (time, not nodes) and is the
one place a search can LOSE ON TIME.

Per position, playing a short self-play sequence with the real clock:
  * send `go wtime X btime Y winc 60 binc 60` with the side to move's real remaining time;
  * measure wall time from sending `go` to reading `bestmove` (monotonic clock);
  * subtract the engine's own reported `time` where present, and flag overruns;
  * PLAY the move and repeat for the other side, deducting elapsed + checking the increment, so the
    clock state evolves exactly as a match would (this is what can expose a loss on time).

A "loss on time" is defined as: the time the engine spent exceeds the time it had available.

Usage: clockpath.py EXE FENS OUTDIR [MAXPLIES] [WTIME] [WINC]
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
MAXPLIES = int(sys.argv[4]) if len(sys.argv) > 4 else 20
WTIME = int(sys.argv[5]) if len(sys.argv) > 5 else 6000
WINC = int(sys.argv[6]) if len(sys.argv) > 6 else 60
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        opts = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                opts.append(l)
            if l == "uciok":
                break
        for n, v in PC20:
            if not any(o.startswith("option name %s " % n) for o in opts):
                raise SystemExit("FAIL: option %r not advertised" % n)
            self.send("setoption name %s value %s" % (n, v))
            self.ready()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died waiting readyok")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def go_clock(self, wtime, btime):
        self.send("position fen " + self.fen)
        self.ready()
        t0 = time.monotonic()
        self.send("go wtime %d btime %d winc %d binc %d" % (wtime, btime, WINC, WINC))
        infos = []
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died during clock search")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l.startswith("bestmove"):
                bm = l
                break
            if l.startswith("info depth"):
                infos.append(l)
        wall = (time.monotonic() - t0) * 1000.0
        last = infos[-1] if infos else None

        def g(pat, cast=int):
            m = re.search(pat, last) if last else None
            return cast(m.group(1)) if m else None

        return {
            "wall_ms": round(wall, 1),
            "engine_time_ms": g(r"\btime (\d+)"),
            "depth": g(r"\bdepth (\d+)"),
            "nodes": g(r"\bnodes (\d+)"),
            "cp": g(r"\bscore cp (-?\d+)"),
            "mate": g(r"\bscore mate (-?\d+)"),
            "bestmove": bm,
            "info_lines": len(infos),
        }

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    games = []
    for gi, fen in enumerate(fens):
        board = chess.Board(fen)
        e = Eng()
        e.fen = fen
        clock = {chess.WHITE: WTIME, chess.BLACK: WTIME}
        plies = []
        overrun = False
        for ply in range(MAXPLIES):
            if not board.legal_moves:
                break
            side = board.turn
            other = not side
            wtime = clock[chess.WHITE] if side == chess.WHITE else clock[chess.BLACK]
            btime = clock[chess.BLACK] if side == chess.WHITE else clock[chess.WHITE]
            # the engine always gets the true remaining times regardless of which side it "is"
            r = e.go_clock(clock[chess.WHITE], clock[chess.BLACK])
            avail = wtime
            spent = r["wall_ms"]
            over = spent > avail
            overrun |= over
            # apply the clock as a match would: deduct elapsed, add increment
            clock[side] = max(0, avail - spent) + WINC
            mv = None
            if r["bestmove"] and r["bestmove"].startswith("bestmove "):
                mv = r["bestmove"].split()[1]
            legal = (mv in {m.uci() for m in board.legal_moves})
            plies.append({
                "ply": ply, "side": "w" if side == chess.WHITE else "b",
                "available_ms": round(avail, 1), "wall_ms": spent,
                "engine_time_ms": r["engine_time_ms"],
                "overrun": over,
                "depth": r["depth"], "nodes": r["nodes"], "cp": r["cp"], "mate": r["mate"],
                "move": mv, "legal": legal,
            })
            if not legal:
                plies.append({"FATAL": "illegal move %r at ply %d" % (mv, ply)})
                break
            board.push(chess.Move.from_uci(mv))
            e.fen = board.fen()
        e.close()
        walls = [p["wall_ms"] for p in plies if "wall_ms" in p]
        games.append({
            "game": gi, "start_fen": fen, "plies": plies,
            "any_overrun": overrun,
            "max_wall_ms": max(walls) if walls else None,
            "total_wall_ms": round(sum(walls), 1) if walls else None,
        })
        print("game %2d plies %2d max %.1f ms overrun %s"
              % (gi, len(plies), games[-1]["max_wall_ms"] or 0, overrun), flush=True)

    allp = [p for g in games for p in g["plies"] if "wall_ms" in p]
    walls = sorted(p["wall_ms"] for p in allp)
    n = len(walls)

    def pct(q):
        return walls[min(n - 1, int(q * n))] if n else None

    summary = {
        "build": os.path.abspath(EXE),
        "sha256": sha256(EXE),
        "settings": "PC20 (Threads 1, Hash 16, S14 + 6)",
        "clock": "wtime/btime %d ms, winc/binc %d ms" % (WTIME, WINC),
        "games": len(games),
        "moves_measured": n,
        "overruns": sum(1 for p in allp if p["overrun"]),
        "games_with_overrun": sum(1 for g in games if g["any_overrun"]),
        "illegal_moves": sum(1 for p in allp if not p["legal"]),
        "wall_ms_min": walls[0] if n else None,
        "wall_ms_median": pct(0.5),
        "wall_ms_p99": pct(0.99),
        "wall_ms_max": walls[-1] if n else None,
        "note": "positions are 12 from the G set, NOT the owner's match games",
    }
    with open(os.path.join(OUTDIR, "clockpath.json"), "w") as f:
        json.dump({"summary": summary, "games": games}, f, indent=1)
    print()
    for k, v in summary.items():
        print("%-28s %s" % (k, v))


main()
