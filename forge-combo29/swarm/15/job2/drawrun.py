#!/usr/bin/env python3
"""drawrun.py SETSDIR OUTJSONL [--depth 10] [--exe PATH]

Runs every position of the six job 2 sets at the given depth with S14, Threads 1, Hash 16,
one fresh `ucinewgame` per position, and reads stdout until `bestmove` before the next
command (never closes stdin mid-search).

For the repetition set the position is given as `position startpos moves ...`, so the engine
sees the actual move history; the record keeps the move list.
Raw per-position transcripts go to SETSDIR/../raw/<set>_<i>.txt.
"""
import argparse
import json
import os
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.log = []
        self.send("uci")
        self.until(lambda l: l.startswith("uciok"))
        self.send("setoption name MultiPV value 1")
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        for k, v in S14:
            self.send("setoption name %s value %s" % (k, v))
        self.send("isready")
        self.until(lambda l: l == "readyok")

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def until(self, pred):
        got = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                return got, False
            line = line.rstrip("\n")
            got.append(line)
            if pred(line):
                return got, True

    def search(self, position_cmd, depth):
        out = []
        self.send("ucinewgame")
        self.send("isready")
        g, _ = self.until(lambda l: l == "readyok")
        out += g
        self.send(position_cmd)
        self.send("isready")
        g, ok = self.until(lambda l: l == "readyok")
        out += g
        bad = [l for l in g if any(b in l for b in BAD)]
        if bad:
            return {"accepted": False, "answer": bad, "infos": [], "bestmove": None,
                    "raw": out}
        self.send("go depth %d" % depth)
        g, ok = self.until(lambda l: l.startswith("bestmove"))
        out += g
        infos = [l for l in g if l.startswith("info depth")]  # an empty PV prints as " pv" at end of line
        bm = [l for l in g if l.startswith("bestmove")]
        return {"accepted": True, "answer": [], "infos": infos,
                "bestmove": bm[-1] if bm else None, "raw": out}

    def quit(self):
        self.send("quit")
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()


def load(setsdir):
    jobs = []  # (setname, kind, payload)
    for kind in ("kvk", "knk", "kbk", "knnk"):
        path = os.path.join(setsdir, "%s_20.fens" % kind)
        for line in open(path, encoding="utf-8"):
            if line.strip():
                jobs.append((kind, "fen", line.strip()))
    path = os.path.join(setsdir, "rep_20.ucimoves")
    for line in open(path, encoding="utf-8"):
        if line.strip():
            jobs.append(("rep", "moves", line.strip()))
    path = os.path.join(setsdir, "fifty_20.fens")
    for line in open(path, encoding="utf-8"):
        if line.strip():
            jobs.append(("fifty", "fen", line.strip()))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("setsdir")
    ap.add_argument("outjsonl")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--exe", default="/home/ubuntu/builds/rel/forge")
    a = ap.parse_args()

    rawdir = os.path.join(os.path.dirname(os.path.abspath(a.outjsonl)), "raw")
    os.makedirs(rawdir, exist_ok=True)
    meta = os.path.join(os.path.dirname(os.path.abspath(a.outjsonl)), "meta.txt")
    uci = subprocess.run([a.exe], input="uci\nquit\n", capture_output=True, text=True).stdout
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write("exe_started: %s\n" % os.path.abspath(a.exe))
        fh.write("sha256: %s\n" % subprocess.run(["sha256sum", os.path.abspath(a.exe)],
                                                 capture_output=True, text=True).stdout.split()[0])
        fh.write("id_name: %s\n" % uci.split("id name ")[1].splitlines()[0])
        fh.write("options_sent: MultiPV 1, Threads 1, Hash 16, %s\n" % " ".join(
            "%s=%s" % (k, v) for k, v in S14))
        fh.write("go: depth %d\n" % a.depth)

    eng = Engine(a.exe)
    n_ok = n_bad = 0
    with open(a.outjsonl, "w", encoding="utf-8") as jl:
        for setname, kind, payload in load(a.setsdir):
            if kind == "fen":
                cmd = "position fen " + payload
            else:
                cmd = "position startpos moves " + payload
            r = eng.search(cmd, a.depth)
            r["set"] = setname
            r["kind"] = kind
            r["payload"] = payload
            idx = n_ok + n_bad
            with open(os.path.join(rawdir, "%s_%03d.txt" % (setname, idx)), "w",
                      encoding="utf-8") as fh:
                fh.write("### " + cmd + "\n" + "\n".join(r["raw"]) + "\n")
            del r["raw"]
            jl.write(json.dumps(r) + "\n")
            jl.flush()
            if r["accepted"]:
                n_ok += 1
            else:
                n_bad += 1
                print("REFUSED %s %s -> %s" % (setname, payload[:40], r["answer"]), flush=True)
    eng.quit()
    print("accepted %d  refused %d" % (n_ok, n_bad))


if __name__ == "__main__":
    sys.exit(main())
