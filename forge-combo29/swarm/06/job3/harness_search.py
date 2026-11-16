#!/usr/bin/env python3
"""area 6 job 3 harness: depth-10 search of each FEN and of its COLOUR mirror.

S14 is applied with setoption (every one followed by isready, all lines read); Threads 1, Hash 16.
Before every `go` a `ucinewgame` + `isready`. For each search the LAST `info ... pv` line and the
`bestmove` line are kept, plus the count of all pv lines. Results are written as JSON lines so nothing
is lost to parsing.

usage: harness_search.py EXE FENFILE OUTFILE META DEPTH [S14|nos14]
"""
import hashlib
import json
import subprocess
import sys
import time

import chess

ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]


class Engine:
    def __init__(self, exe, options):
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
        for name, value in options:
            self.send("setoption name %s value %s" % (name, value))
            self.send("isready")
            self.wait_ready()
            self.sent.append("setoption name %s value %s" % (name, value))
        self.send("isready")
        self.wait_ready()

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
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
                raise RuntimeError("engine rejected input: " + line)
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
        last_pv = None
        pv_count = 0
        bestmove = None
        while True:
            line = self.readline().strip()
            if " pv " in line and line.startswith("info"):
                last_pv = line
                pv_count += 1
            if line.startswith("bestmove"):
                bestmove = line
                break
            if time.monotonic() - t0 > timeout:
                self.send("stop")
                raise RuntimeError("timeout after %.0fs" % timeout)
        return {"last_pv": last_pv, "pv_count": pv_count, "bestmove": bestmove,
                "seconds": round(time.monotonic() - t0, 3)}

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    exe, fenfile, outfile, metafile, depth, mode = sys.argv[1:7]
    depth = int(depth)
    options = [("Threads", "1"), ("Hash", "16")]
    if mode == "S14":
        options += S14
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    eng = Engine(exe, options)
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe), "id_name: " + str(eng.name),
            "option_lines_sent: " + "; ".join(eng.sent),
            "per_search_lines: 'ucinewgame','isready','position fen <FEN>','isready','go depth %d'" % depth,
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "depth: %d" % depth, "mode: " + mode, "positions in file: %d" % len(fens)]
    failures = []
    out = open(outfile, "w")
    t_all = time.monotonic()
    for i, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except Exception as exc:
            failures.append({"index": i, "fen": fen, "why": "python-chess rejects: %s" % exc})
            continue
        mfen = board.mirror().fen()
        try:
            a = eng.search(fen, depth)
            b = eng.search(mfen, depth)
        except RuntimeError as exc:
            failures.append({"index": i, "fen": fen, "why": "engine: %s" % exc})
            eng = Engine(exe, options)
            continue
        rec = {"index": i, "fen": fen, "mfen": mfen, "self": a, "mirror": b}
        out.write(json.dumps(rec) + "\n")
        out.flush()
    out.close()
    eng.quit()
    meta.append("wall_seconds: %.1f" % (time.monotonic() - t_all))
    meta.append("failures: %d" % len(failures))
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
        for f in failures:
            fh.write("FAIL %s\n" % json.dumps(f))
    print("rows=%d failures=%d wall=%.1fs" % (len(fens) - len(failures), len(failures),
                                              time.monotonic() - t_all))


if __name__ == "__main__":
    main()
