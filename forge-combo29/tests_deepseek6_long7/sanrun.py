#!/usr/bin/env python3
"""sanrun.py -- run a position set under a sanitizer build and count sanitizer lines.

Usage: sanrun.py --exe PATH --set FENS --out ROWS [--raw RAWLOG] [--depth N]
                 [--opts 'Name=Value;...'] [--limit N]

Each position gets its own engine process (a crash on one position does not hide the
rest, and every process's exit is where ASan prints a leak report). The protocol is
the same as rows.py: uci, the options, isready, position fen, go depth N, WAIT for
bestmove, then quit and read everything the process still writes (including the
sanitizer's exit-time output) until it exits.

ROWS: one line per position "index | nodes | bestmove | sanlines | exitcode", with a
first header line "# totals: positions P sanlines S". RAWLOG keeps every raw line.
"""
import argparse
import os
import re
import subprocess
import sys

SAN_PAT = re.compile(r"AddressSanitizer|LeakSanitizer|SUMMARY:|runtime error|UndefinedBehaviorSanitizer")


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
    ap.add_argument("--raw", default="")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--opts", default="")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    exe = os.path.abspath(args.exe)
    fens = load(args.set, args.limit)
    opt_lines = []
    for chunk in args.opts.split(";"):
        chunk = chunk.strip()
        if chunk:
            n, _, v = chunk.partition("=")
            opt_lines.append("setoption name %s value %s" % (n.strip(), v.strip()))
    opt_lines += ["setoption name Threads value 1",
                  "setoption name Hash value 16",
                  "setoption name OwnBook value false"]

    raw = open(args.raw, "w", encoding="utf-8") if args.raw else None
    if raw:
        raw.write("# exe %s\n# set %s (%d positions) depth %d\n# options %s\n"
                  % (exe, args.set, len(fens), args.depth, args.opts or "(none)"))

    rows = []
    total_san = 0
    for i, fen in enumerate(fens):
        proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        collected = []

        def send(t):
            try:
                proc.stdin.write(t + "\n")
                proc.stdin.flush()
            except (BrokenPipeError, ValueError):
                pass

        def read_until(token):
            while True:
                line = proc.stdout.readline()
                if line == "":
                    return False
                collected.append(line.rstrip("\n"))
                if line.startswith(token):
                    return True

        send("uci")
        read_until("uciok")
        for o in opt_lines:
            send(o)
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("go depth %d" % args.depth)
        read_until("bestmove")
        send("quit")
        rest = proc.stdout.read()
        if rest:
            collected.extend(rest.splitlines())
        rc = proc.wait(timeout=600)

        san = [ln for ln in collected if SAN_PAT.search(ln)]
        total_san += len(san)
        nodes, best = 0, ""
        for line in collected:
            if line.startswith("bestmove"):
                f = line.split()
                if len(f) > 1:
                    best = f[1]
            if line.startswith("info "):
                m = re.search(r"\bnodes (\d+)", line)
                if m:
                    nodes = int(m.group(1))
        rows.append((i, nodes, best, len(san), rc))
        if raw:
            raw.write("=== position %d ===\n" % i)
            raw.write("\n".join(collected) + "\n")
            raw.write("=== exit %d, sanlines %d ===\n" % (rc, len(san)))

    if raw:
        raw.close()
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# totals: positions %d sanlines %d\n" % (len(rows), total_san))
        for i, nodes, best, san, rc in rows:
            fh.write("%d | %d | %s | %d | %d\n" % (i, nodes, best, san, rc))
    print("positions %d, sanitizer lines %d -> %s" % (len(rows), total_san, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
