#!/usr/bin/env python3
"""pvrun.py EXE FENFILE OUTDIR [--depth 12] [--maxpos N]

One engine process, one position at a time: ucinewgame, isready, then the S14
options, then `position fen`, isready, `go depth D`, read every line up to
bestmove. Raw transcript per position under OUTDIR/raw/<idx>.txt, one JSON
record per position appended to OUTDIR/pv.jsonl.

Nothing is edited after the run: the analysis is a separate script.
"""
import argparse
import json
import os
import subprocess
import sys
import time

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", True),
    ("CuckooRep", True), ("HistRework", 2), ("TtPruneV2", True),
    ("CorrHistV2", True), ("MateAlphaGuard", True), ("OwnBook", False),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def read_fens(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            # EPD (4 fields, ops allowed) -> plain FEN by adding the two counters
            if len(fields) == 4:
                out.append(" ".join(fields) + " 0 1")
            elif len(fields) >= 6:
                out.append(" ".join(fields[:6]))
            else:
                out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fenfile")
    ap.add_argument("outdir")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--maxpos", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(os.path.join(args.outdir, "raw"), exist_ok=True)
    fens = read_fens(args.fenfile)
    if args.maxpos:
        fens = fens[: args.maxpos]

    with open(os.path.join(args.outdir, "meta.txt"), "w", encoding="utf-8") as m:
        m.write("exe_started: %s\n" % os.path.abspath(args.exe))
        m.write("id_name: %s\n" % subprocess.run(
            [args.exe], input="uci\nquit\n", capture_output=True, text=True).stdout
            .split("id name ")[1].splitlines()[0])
        m.write("options_sent:\n")
        m.write("  MultiPV 1\n  Threads 1\n  Hash 16\n")
        for k, v in S14:
            m.write("  %s %s\n" % (k, "true" if v is True else v))
        m.write("go: depth %d\n" % args.depth)

    proc = subprocess.Popen([args.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(cmd):
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def until_ready(raw):
        while True:
            line = proc.stdout.readline()
            if not line:
                return False
            raw.append(line.rstrip("\n"))
            if line.strip() == "readyok":
                return True

    send("uci")
    raw0 = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        raw0.append(line.rstrip("\n"))
        if line.startswith("uciok"):
            break
    send("setoption name MultiPV value 1")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for k, v in S14:
        send("setoption name %s value %s" % (k, "true" if v is True else v))
    send("isready")
    startup = []
    until_ready(startup)

    jl = open(os.path.join(args.outdir, "pv.jsonl"), "w", encoding="utf-8")
    t_all0 = time.monotonic()
    for idx, fen in enumerate(fens):
        raw = ["### ucinewgame"]
        send("ucinewgame")
        send("isready")
        until_ready(raw)
        raw.append("### position fen " + fen)
        send("position fen " + fen)
        send("isready")
        ok_fen = until_ready(raw)
        bad = [l for l in raw if any(b in l for b in BAD)]
        rec = {"idx": idx, "fen": fen, "accepted": ok_fen and not bad, "answer": bad,
               "infos": [], "bestmove": None, "seconds": None}
        if rec["accepted"]:
            t0 = time.monotonic()
            send("go depth %d" % args.depth)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.rstrip("\n")
                raw.append(line)
                if line.startswith("info ") and " pv " in line:
                    rec["infos"].append(line)
                elif line.startswith("bestmove"):
                    rec["bestmove"] = line
                    break
            rec["seconds"] = time.monotonic() - t0
        with open(os.path.join(args.outdir, "raw", "%04d.txt" % idx), "w", encoding="utf-8") as fh:
            fh.write("\n".join(raw) + "\n")
        jl.write(json.dumps(rec) + "\n")
        jl.flush()
        if idx % 25 == 0:
            print("pos %d/%d %.1fs" % (idx, len(fens), time.monotonic() - t_all0), flush=True)
        if proc.poll() is not None:
            print("ENGINE EXIT at pos %d code %s" % (idx, proc.returncode), flush=True)
            break
    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    jl.close()
    print("total_seconds %.1f positions %d" % (time.monotonic() - t_all0, len(fens)))


if __name__ == "__main__":
    main()
