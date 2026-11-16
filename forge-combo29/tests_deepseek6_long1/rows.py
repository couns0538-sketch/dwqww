#!/usr/bin/env python3
"""rows.py -- one row per position: index | nodes | bestmove.

Usage: rows.py --exe PATH --set FENSFILE --out ROWSFILE [--depth N]
               [--opts 'Name=Value;Name=Value'] [--searchmoves "e2e4 d2d4"]
               [--multipv N] [--limit N] [--meta METAFILE]

Protocol per position: ucinewgame, isready, go depth N, wait for bestmove.
Options are sent once, after uci/isready and before the first ucinewgame.
Every answer line is read; the run STOPS at once on 'unknown option' or
'invalid value' (that line is written to the rows file and the meta file).
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

STOP_PAT = re.compile(r"unknown option|invalid value")


def load_positions(path, limit):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            # epd: first 4 fields are the fen, the rest are operations
            if len(parts) > 6 and (parts[4].startswith("bm") or parts[4].startswith(";")):
                line = " ".join(parts[:4]) + " 0 1"
            out.append(line)
            if limit and len(out) >= limit:
                break
    return out


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = []

    def send(self, text):
        self.lines.append(text)
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def read_until(self, token):
        """Read lines until one starts with `token`. Returns (lines, stopline)."""
        got = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                return got, "<EOF>"
            line = line.rstrip("\n")
            got.append(line)
            if STOP_PAT.search(line):
                return got, line
            if line.startswith(token):
                return got, None

    def quit(self):
        try:
            self.proc.stdin.write("quit\n")
            self.proc.stdin.flush()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", default=None)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--opts", default="")
    ap.add_argument("--searchmoves", default="")
    ap.add_argument("--multipv", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    exe = os.path.abspath(args.exe)
    meta_path = args.meta or (args.out + ".meta")
    exe_sha = sha256_of(exe)

    positions = load_positions(args.set, args.limit)
    opt_lines = []
    for chunk in args.opts.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, _, value = chunk.partition("=")
        opt_lines.append("setoption name %s value %s" % (name.strip(), value.strip()))
    if args.multipv:
        opt_lines.append("setoption name MultiPV value %d" % args.multipv)
    # fixed test conditions, always sent
    opt_lines = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "setoption name OwnBook value false",
    ] + opt_lines

    eng = Engine(exe)
    eng.send("uci")
    uci_lines, stop = eng.read_until("uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    if stop:
        with open(args.out, "w") as fh:
            fh.write("# STOPPED during uci: %s\n" % stop)
        eng.quit()
        return 1

    for line in opt_lines:
        eng.send(line)
    eng.send("isready")
    _, stop = eng.read_until("readyok")
    if stop:
        with open(args.out, "w") as fh:
            fh.write("# STOPPED during setoption: %s\n" % stop)
        eng.quit()
        return 1

    rows = []
    stopped = None
    for i, fen in enumerate(positions):
        eng.send("ucinewgame")
        eng.send("isready")
        _, stop = eng.read_until("readyok")
        if stop:
            stopped = (i, stop)
            break
        eng.send("position fen " + fen)
        go = "go depth %d" % args.depth
        if args.searchmoves:
            go += " searchmoves " + args.searchmoves
        eng.send(go)
        body, stop = eng.read_until("bestmove")
        if stop:
            stopped = (i, stop)
            break
        nodes = 0
        bestmove = ""
        for line in body:
            if line.startswith("bestmove"):
                f = line.split()
                if len(f) > 1:
                    bestmove = f[1]
            elif line.startswith("info "):
                m = re.search(r"\bnodes (\d+)", line)
                if m:
                    nodes = int(m.group(1))
        rows.append((i, nodes, bestmove))

    eng.quit()

    with open(args.out, "w") as fh:
        for i, nodes, bestmove in rows:
            fh.write("%d | %d | %s\n" % (i, nodes, bestmove))
        if stopped:
            fh.write("# STOPPED at %d: %s\n" % stopped)

    with open(meta_path, "w") as fh:
        fh.write("exe_started: %s\n" % exe)
        fh.write("exe_sha256: %s\nexe_sha256_at_start: %s\n" % (sha256_of(exe), exe_sha))
        fh.write("id_name: %s\n" % id_name)
        fh.write("set: %s\n" % os.path.abspath(args.set))
        fh.write("set_sha256: %s\n" % sha256_of(args.set))
        fh.write("depth: %d\n" % args.depth)
        fh.write("searchmoves: %s\n" % (args.searchmoves or "(none)"))
        fh.write("rows_written: %d\n" % len(rows))
        if stopped:
            fh.write("stopped_at_row: %d\nstopped_line: %s\n" % stopped)
        fh.write("option_lines_sent:\n")
        for line in opt_lines:
            fh.write("  %s\n" % line)
    if stopped:
        print("STOPPED at row %d: %s" % stopped, file=sys.stderr)
        return 2
    print("rows: %d -> %s; meta -> %s" % (len(rows), args.out, meta_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
