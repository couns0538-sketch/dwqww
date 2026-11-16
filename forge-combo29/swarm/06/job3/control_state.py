#!/usr/bin/env python3
"""Control: is the depth-10 result a function of the position alone (fresh process each time),
or does it depend on what the same process searched before?

Three modes on the same FEN list:
  fresh   : one new engine process per search; search FEN i, then its mirror in a NEW process
  repeat  : ONE process; search FEN i twice in a row (must be identical: determinism control)
  seqself : ONE process; search FEN 0..n-1 in order, no mirrors (records order sensitivity)

usage: control_state.py MODE EXE FENFILE OUTFILE META DEPTH
"""
import hashlib
import json
import subprocess
import sys
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.name = None
        while True:
            line = self.readline()
            if line.startswith("id name"):
                self.name = line.strip()
            if line.strip() == "uciok":
                break
        self.sent = []
        for name, value in [("Threads", "1"), ("Hash", "16")] + S14:
            self.send("setoption name %s value %s" % (name, value))
            self.send("isready")
            self.wait_ready()
            self.sent.append("setoption name %s value %s" % (name, value))
        self.send("isready")
        self.wait_ready()

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def readline(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def wait_ready(self):
        lines = []
        while True:
            line = self.readline().strip()
            lines.append(line)
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError("engine rejected: " + line)
            if line == "readyok":
                return lines

    def search(self, fen, depth, timeout=180.0):
        self.send("ucinewgame")
        self.send("isready")
        self.wait_ready()
        self.send("position fen " + fen)
        self.send("isready")
        self.wait_ready()
        t0 = time.monotonic()
        self.send("go depth %d" % depth)
        last_pv, best = None, None
        while True:
            line = self.readline().strip()
            if " pv " in line and line.startswith("info"):
                last_pv = line
            if line.startswith("bestmove"):
                best = line
                break
            if time.monotonic() - t0 > timeout:
                self.send("stop")
                raise RuntimeError("timeout")
        return {"last_pv": last_pv, "bestmove": best, "seconds": round(time.monotonic() - t0, 3)}

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    mode, exe, fenfile, outfile, metafile, depth = sys.argv[1:7]
    depth = int(depth)
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    meta = []
    out = open(outfile, "w")

    if mode == "fresh":
        for i, fen in enumerate(fens):
            mfen = chess.Board(fen).mirror().fen()
            e1 = Engine(exe)
            a = e1.search(fen, depth)
            e1.quit()
            e2 = Engine(exe)
            b = e2.search(mfen, depth)
            e2.quit()
            out.write(json.dumps({"index": i, "fen": fen, "mfen": mfen, "self": a, "mirror": b}) + "\n")
            out.flush()
            meta.append("fresh processes: index %d, options: %s" % (i, "; ".join(e1.sent)))
    elif mode == "repeat":
        eng = Engine(exe)
        meta.append("option_lines_sent: " + "; ".join(eng.sent))
        for i, fen in enumerate(fens):
            a = eng.search(fen, depth)
            b = eng.search(fen, depth)
            out.write(json.dumps({"index": i, "fen": fen, "mfen": fen, "self": a, "mirror": b}) + "\n")
            out.flush()
        eng.quit()
    elif mode == "seqself":
        eng = Engine(exe)
        meta.append("option_lines_sent: " + "; ".join(eng.sent))
        for i, fen in enumerate(fens):
            a = eng.search(fen, depth)
            out.write(json.dumps({"index": i, "fen": fen, "mfen": fen, "self": a}) + "\n")
            out.flush()
        eng.quit()
    else:
        raise SystemExit("bad mode")

    out.close()
    meta.append("mode: " + mode)
    meta.append("exe_started: " + exe)
    meta.append("exe_sha256: " + sha256(exe))
    meta.append("fenfile: " + fenfile)
    meta.append("depth: %d" % depth)
    open(metafile, "w").write("\n".join(meta) + "\n")
    print("mode=%s rows=%d" % (mode, len(fens)))


if __name__ == "__main__":
    main()
