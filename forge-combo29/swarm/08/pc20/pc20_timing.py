#!/usr/bin/env python3
"""pc20_timing.py EXE FENFILE MODE OUTJSONL LABEL

Wall-clock timing harness for the PC build under PC20 = S14 + the six extra settings.
Same measurement discipline as job1b/clock_latency2.py (time.monotonic from writing `go` to reading `bestmove`,
ucinewgame before every search, never sends anything mid-search), and it ALSO records the last completed depth and
the cost of the last iteration, because 08-F10/F11 need those.

Aborts loudly on any `unknown option` / `invalid value` / `invalid FEN` / `illegal move`.
"""
import json
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.read_until("uciok")
        for name, val in S14 + PC20_EXTRA:
            self.command("setoption name %s value %s" % (name, val))
        self.command("setoption name Threads value 1")
        self.command("setoption name Hash value 16")

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, token, timeout=180.0):
        t0 = time.monotonic()
        out = []
        while True:
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("no %r in %ss; last %r" % (token, timeout, out[-5:]))
            line = self.p.stdout.readline()
            if line == "":
                raise EOFError("engine closed; last %r" % (out[-5:],))
            line = line.rstrip("\n")
            for b in BAD:
                if b in line:
                    raise RuntimeError("engine refused: %r" % line)
            out.append(line)
            if line.startswith(token):
                return out

    def sync(self):
        self.send("isready")
        return self.read_until("readyok")

    def command(self, line):
        self.send(line)
        return self.sync()

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def main():
    exe, fenfile, mode, outpath = sys.argv[1:5]
    label = sys.argv[5] if len(sys.argv) > 5 else mode
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    eng = Engine(exe)
    with open(outpath, "w") as out:
        for idx, fen in enumerate(fens):
            eng.command("ucinewgame")
            eng.send("position fen " + fen)
            eng.sync()
            t_go = time.monotonic()
            eng.send("go " + mode)
            lines = eng.read_until("bestmove")
            wall = (time.monotonic() - t_go) * 1000.0
            marks = []
            for l in lines:
                if l.startswith("info depth"):
                    marks.append(l)
            bm = [l for l in lines if l.startswith("bestmove")][0]
            last_depth = None
            if marks:
                try:
                    last_depth = int(marks[-1].split()[2])
                except (IndexError, ValueError):
                    pass
            rec = {"i": idx, "fen": fen, "go": mode, "label": label, "wall_ms": wall,
                   "bestmove": bm, "nlines": len(lines), "last_depth": last_depth,
                   "n_info": len(marks)}
            out.write(json.dumps(rec) + "\n")
            out.flush()
    eng.close()


if __name__ == "__main__":
    main()
