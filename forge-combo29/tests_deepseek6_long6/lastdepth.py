#!/usr/bin/env python3
"""lastdepth.py -- per position, the depth of the LAST info line before bestmove.

Usage: lastdepth.py --exe PATH --set FENS [--opts '..'] [--depth N]
                    [--searchmoves-from FILE] [--out FILE]
One row per position: "index | lastdepth | bestmove". Everything else matches
rows.py (ucinewgame + isready before each go, Threads 1 / Hash 16 / OwnBook false,
and the run STOPS on 'unknown option' or 'invalid value').
"""
import argparse
import os
import re
import subprocess
import sys

STOP_PAT = re.compile(r"unknown option|invalid value")
DEPTH_PAT = re.compile(r"^info depth (\d+)")


def load(path, limit):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
            if limit and len(out) >= limit:
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--opts", default="")
    ap.add_argument("--searchmoves-from", default="")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    fens = load(args.set, args.limit)
    per_row = {}
    if args.searchmoves_from:
        with open(args.searchmoves_from, "r", encoding="utf-8") as fh:
            for line in fh:
                p = [x.strip() for x in line.split("|")]
                if len(p) >= 3:
                    mv = p[2].strip()
                    per_row[int(p[0])] = "" if mv.startswith("(") else mv

    opts = ["setoption name Threads value 1", "setoption name Hash value 16",
            "setoption name OwnBook value false"]
    for chunk in args.opts.split(";"):
        chunk = chunk.strip()
        if chunk:
            n, _, v = chunk.partition("=")
            opts.append("setoption name %s value %s" % (n.strip(), v.strip()))

    proc = subprocess.Popen([os.path.abspath(args.exe)], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)

    def send(t):
        proc.stdin.write(t + "\n")
        proc.stdin.flush()

    def until(token):
        got, stop = [], None
        while True:
            line = proc.stdout.readline()
            if line == "":
                return got, "<EOF>"
            line = line.rstrip("\n")
            got.append(line)
            if STOP_PAT.search(line):
                return got, line
            if line.startswith(token):
                return got, None

    send("uci")
    _, stop = until("uciok")
    if stop:
        with open(args.out, "w") as fh:
            fh.write("# STOPPED during uci: %s\n" % stop)
        return 2
    for o in opts:
        send(o)
    send("isready")
    _, stop = until("readyok")
    if stop:
        with open(args.out, "w") as fh:
            fh.write("# STOPPED during setoption: %s\n" % stop)
        return 2

    rows = []
    for i, fen in enumerate(fens):
        send("ucinewgame")
        send("isready")
        _, stop = until("readyok")
        if stop:
            break
        send("position fen " + fen)
        mv = per_row.get(i, "") if per_row else ""
        go = "go depth %d" % args.depth
        if mv:
            go += " searchmoves " + mv
        send(go)
        body, stop = until("bestmove")
        if stop:
            break
        lastdepth, best = 0, ""
        for line in body:
            m = DEPTH_PAT.match(line)
            if m:
                lastdepth = int(m.group(1))
            if line.startswith("bestmove"):
                f = line.split()
                if len(f) > 1:
                    best = f[1]
        rows.append((i, lastdepth, best))
    send("quit")
    with open(args.out, "w") as fh:
        for i, d, b in rows:
            fh.write("%d | %d | %s\n" % (i, d, b))
    print("rows: %d -> %s" % (len(rows), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
