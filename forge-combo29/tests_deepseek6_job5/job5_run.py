#!/usr/bin/env python3
"""job5_run.py -- the four counted runs of job 5 (E0..E3), O and G.

Usage: job5_run.py [--set O|G|both]
One engine process per run; `go depth 12` per position with ucinewgame+isready before
it; writes runs/<tag>_<set>.rows and runs/<tag>_<set>.cex (one counter line per go).
"""
import argparse
import os
import re
import subprocess
import sys

RUNS = [("E0", ""), ("E1", "CheckExtensionDepth=8"), ("E2", "CheckExtensionDepth=5"),
        ("E3", "CheckExtensionDepth=30")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="both")
    ap.add_argument("--exe", default="/agent/repos/work/build-j5/forge")
    ap.add_argument("--depth", type=int, default=12)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    os.makedirs("runs", exist_ok=True)
    s14 = open("s14.txt").read().strip()
    sets = ["O", "G"] if args.set == "both" else [args.set]
    out = open("table.txt", "a", encoding="utf-8")

    for setname in sets:
        fens = [l.strip() for l in open("first200.fens" if setname == "O" else "set_G.epd")
                if l.strip() and not l.startswith("#")]
        for tag, extra in RUNS:
            rf, cf = "runs/%s_%s.rows" % (tag, setname), "runs/%s_%s.cex" % (tag, setname)
            if os.path.exists(rf) and os.path.exists(cf):
                print("skip %s_%s" % (tag, setname)); continue
            p = subprocess.Popen([args.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)

            def send(t):
                p.stdin.write(t + "\n"); p.stdin.flush()

            def until(tok):
                got = []
                while True:
                    l = p.stdout.readline()
                    if l == "":
                        return got
                    l = l.rstrip("\n"); got.append(l)
                    if l.startswith(tok):
                        return got

            send("uci"); until("uciok")
            opts = ["setoption name Threads value 1", "setoption name Hash value 16",
                    "setoption name OwnBook value false"]
            for chunk in (s14 + (";" + extra if extra else "")).split(";"):
                chunk = chunk.strip()
                if chunk:
                    n, _, v = chunk.partition("=")
                    opts.append("setoption name %s value %s" % (n.strip(), v.strip()))
            for o in opts:
                send(o)
            send("isready"); until("readyok")
            rows, cex = [], []
            for i, fen in enumerate(fens):
                send("ucinewgame"); send("isready"); until("readyok")
                send("position fen " + fen)
                send("go depth %d" % args.depth)
                body = until("bestmove")
                nodes, best, c = 0, "", None
                for l in body:
                    if l.startswith("bestmove"):
                        f = l.split()
                        if len(f) > 1:
                            best = f[1]
                    elif l.startswith("info string cex"):
                        c = l
                    elif l.startswith("info "):
                        m = re.search(r"\bnodes (\d+)", l)
                        if m:
                            nodes = int(m.group(1))
                rows.append((i, nodes, best))
                cex.append(c if c else "info string cex MISSING")
            send("quit"); p.wait(timeout=900)
            with open(rf, "w") as fh:
                for i, n, b in rows:
                    fh.write("%d | %d | %s\n" % (i, n, b))
            with open(cf, "w") as fh:
                fh.write("\n".join(cex) + "\n")
            line = "%s | %s | %s | rows %d | sum %d" % (
                tag, setname, extra or "(none)", len(rows), sum(n for _, n, _ in rows))
            print(line, flush=True); out.write(line + "\n"); out.flush()
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
