#!/usr/bin/env python3
"""clock_latency2.py EXE FENFILE MODE OUTJSONL LABEL

Same measurement as ../job1/clock_latency.py (time.monotonic from writing `go` to reading `bestmove`,
S14 + Threads 1 + Hash 16 + ucinewgame per search), with one addition: `setoption name OwnBook value false`
is sent for every search, so no answer can come from the opening book (my finding 08-F3: position 3 of the O
set was answered from the book in 0.04 ms with OwnBook at its default true).
"""
import json
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, token, timeout=180.0):
        t0 = time.monotonic()
        out = []
        while True:
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("no %r within %ss; last lines %r" % (token, timeout, out[-5:]))
            line = self.p.stdout.readline()
            if line == "":
                raise EOFError("engine closed; last lines %r" % (out[-5:],))
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


def parse_go(mode):
    toks = mode.split()
    d = {}
    i = 0
    while i < len(toks):
        k = toks[i]
        if k in ("movetime", "wtime", "btime", "winc", "binc", "depth", "nodes", "movestogo"):
            d[k] = int(toks[i + 1])
            i += 2
        elif k == "infinite":
            d["infinite"] = True
            i += 1
        else:
            raise SystemExit("unparsed go token %r" % k)
    if "movetime" in d:
        limit_ms = float(d["movetime"])
    else:
        base = min(d.get("wtime", 10 ** 9), d.get("btime", 10 ** 9))
        limit_ms = float(base) / 30.0
    return d, limit_ms


def main():
    exe, fenfile, mode, outpath = sys.argv[1:5]
    label = sys.argv[5] if len(sys.argv) > 5 else mode
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    d, limit_ms = parse_go(mode)

    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok")
    for name, val in S14:
        eng.command("setoption name %s value %s" % (name, val))
    eng.command("setoption name Threads value 1")
    eng.command("setoption name Hash value 16")
    eng.command("setoption name OwnBook value false")

    with open(outpath, "w") as out:
        for idx, fen in enumerate(fens):
            eng.command("ucinewgame")
            eng.send("position fen " + fen)
            eng.sync()
            t_go = time.monotonic()
            eng.send("go " + mode)
            lines = eng.read_until("bestmove")
            wall = (time.monotonic() - t_go) * 1000.0
            bm = [l for l in lines if l.startswith("bestmove")][0]
            rec = {"i": idx, "fen": fen, "go": mode, "label": label, "wall_ms": wall,
                   "limit_ms": limit_ms, "bestmove": bm, "nlines": len(lines),
                   "over_limit_50ms": wall > limit_ms + 50.0}
            out.write(json.dumps(rec) + "\n")
            out.flush()
    eng.close()


if __name__ == "__main__":
    main()
