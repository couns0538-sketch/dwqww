#!/usr/bin/env python3
"""job3b_run.py -- the 14 counted runs of job 3b.

Usage: job3b_run.py [--set O|G|both]
For each run: one engine PROCESS (so the counters are that run's), `go depth 12` per
position with ucinewgame+isready before it, the rows file (index|nodes|bestmove) and a
counters file (one `info string cfp ...` line per go, in position order).
Appends one summary line per run to table.txt.
"""
import argparse
import os
import re
import subprocess
import sys

RUNS = [
    ("C0", ""),
    ("C1", "CaptureFutilityBase=230"),
    ("C2", "CaptureFutilityBase=230;CaptureFutilityDepth=5"),
    ("C3", "CaptureFutilityBase=230;CaptureFutilityDepth=7"),
    ("C4", "CaptureFutilityBase=230;CaptureFutilityMultiplier=100"),
    ("C5", "CaptureFutilityBase=230;CaptureFutilityMultiplier=100;CaptureFutilityDepth=5"),
    ("C6", "CaptureFutilityBase=230;CaptureFutilityMultiplier=100;CaptureFutilityDepth=9"),
]


def load(path, limit=0):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
            if limit and len(out) >= limit:
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="both")
    ap.add_argument("--exe", default="/agent/repos/work/build-j3b/forge")
    ap.add_argument("--depth", type=int, default=12)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    os.makedirs("runs", exist_ok=True)
    s14 = open("s14.txt").read().strip()
    sets = ["O", "G"] if args.set == "both" else [args.set]
    out = open("table.txt", "a", encoding="utf-8")

    for setname in sets:
        fens = load("first200.fens" if setname == "O" else "set_G.epd")
        for tag, extra in RUNS:
            rf = "runs/%s_%s.rows" % (tag, setname)
            cf = "runs/%s_%s.counters" % (tag, setname)
            if os.path.exists(rf) and os.path.exists(cf):
                print("skip %s_%s" % (tag, setname)); continue
            exe = args.exe
            p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)

            def send(t):
                p.stdin.write(t + "\n"); p.stdin.flush()

            def until(tok):
                got = []
                while True:
                    l = p.stdout.readline()
                    if l == "":
                        return got
                    l = l.rstrip("\n")
                    got.append(l)
                    if l.startswith(tok):
                        return got

            send("uci"); until("uciok")
            opts = ["setoption name Threads value 1",
                    "setoption name Hash value 16",
                    "setoption name OwnBook value false"]
            for chunk in (s14 + (";" + extra if extra else "")).split(";"):
                chunk = chunk.strip()
                if chunk:
                    n, _, v = chunk.partition("=")
                    opts.append("setoption name %s value %s" % (n.strip(), v.strip()))
            for o in opts:
                send(o)
            send("isready"); until("readyok")

            rows, counters = [], []
            stopped = None
            for i, fen in enumerate(fens):
                send("ucinewgame"); send("isready"); until("readyok")
                send("position fen " + fen)
                send("go depth %d" % args.depth)
                body = until("bestmove")
                bad = [b for b in body if re.search(r"unknown option|invalid value", b)]
                if bad:
                    stopped = bad[0]; break
                nodes, best, c = 0, "", None
                for l in body:
                    if l.startswith("bestmove"):
                        f = l.split()
                        if len(f) > 1:
                            best = f[1]
                    if l.startswith("info string cfp "):
                        c = l
                    elif l.startswith("info "):
                        m = re.search(r"\bnodes (\d+)", l)
                        if m:
                            nodes = int(m.group(1))
                rows.append((i, nodes, best))
                counters.append(c if c is not None else "info string cfp MISSING")
            send("quit")
            p.wait(timeout=600)
            with open(rf, "w") as fh:
                for i, n, b in rows:
                    fh.write("%d | %d | %s\n" % (i, n, b))
                if stopped:
                    fh.write("# STOPPED: %s\n" % stopped)
            with open(cf, "w") as fh:
                fh.write("\n".join(counters) + "\n")
            total = sum(n for _, n, _ in rows)
            line = "%s | %s | %s | rows %d | sum %d%s" % (
                tag, setname, extra or "(none)", len(rows), total,
                " | STOPPED " + stopped if stopped else "")
            print(line, flush=True)
            out.write(line + "\n"); out.flush()
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
