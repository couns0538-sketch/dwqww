#!/usr/bin/env python3
"""seat 17: independent confirmation of the threaded move-instability claim (seat 24).

Claim under test: at depth 12, Hash 16, OwnBook false, the chosen MOVE is not reproducible above one
thread. Seat 24 reports unstable-position counts base 0/20 (T1), 8/20 (T2), 9/20 (T4); PC build under
PC20 0, 10, 8 of 20.

Method (mine, written from the claim, not from their script):
 - 20 positions: the first 20 of set G (their set, so the counts are directly comparable), each validated
   with python-chess first.
 - For each (position, Threads) in {1, 2, 4} x {20 positions}: SIX runs, each a FRESH process.
 - Threads and Hash are sent, each confirmed by `readyok` before the position; the search is read to
   `bestmove` before `quit` (never pipelined - 19-F12).
 - A position counts as UNSTABLE when its six runs return more than one distinct bestmove token.
 - Also records the node counts, so I can report whether the Threads-1 counts are identical to the digit
   (their claim) and how far the multi-thread counts spread.

usage: thread_instability.py <exe> <epd> <outdir> <label> [--pc20]
"""
import json
import os
import subprocess
import sys

import chess

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"),
]
RUNS = 6
DEPTH = 12


def one_run(exe, fen, threads, pc20, timeout=300):
    """One fresh process, one search. Returns (bestmove_token, last_depth12_nodes, complaint_lines)."""
    opts = list(PC20_EXTRA) if pc20 else []
    # OwnBook false in both regimes: the claim uses it, and it removes book answers entirely.
    opts = opts + [("OwnBook", "false"), ("Hash", "16"), ("Threads", str(threads))]
    if pc20:
        opts = list(S14) + opts

    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        while True:
            reply = proc.stdout.readline()
            if reply == "":
                return None
            out.append(reply.rstrip("\n"))
            if pred(reply):
                return reply

    try:
        send("uci")
        read_until(lambda l: l.strip() == "uciok")
        for name, value in opts:
            send("setoption name %s value %s" % (name, value))
            send("isready")
            read_until(lambda l: l.strip() == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda l: l.strip() == "readyok")
        send("go depth %d" % DEPTH)
        read_until(lambda l: l.startswith("bestmove"))
    finally:
        try:
            send("quit")
            proc.wait(timeout=30)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()

    token = None
    nodes = None
    for line in out:
        if line.startswith("bestmove"):
            parts = line.split()
            token = parts[1] if len(parts) > 1 else None
    for line in out:
        if line.startswith("info depth %d " % DEPTH) and " nodes " in line:
            try:
                nodes = int(line.split(" nodes ")[1].split()[0])
            except (IndexError, ValueError):
                nodes = None
    complaints = [l for l in out if "unknown option" in l or "invalid value" in l]
    return token, nodes, complaints


def main():
    exe, epd, outdir, label = sys.argv[1:5]
    pc20 = "--pc20" in sys.argv
    os.makedirs(outdir, exist_ok=True)

    raw = [line.split(";")[0].strip() for line in open(epd) if line.strip()][:20]
    fens = []
    rejected = []
    for i, f in enumerate(raw):
        try:
            b = chess.Board(f)
            if b.is_valid() and b.legal_moves.count() > 0:
                fens.append(f)
            else:
                rejected.append({"i": i, "fen": f, "why": "invalid or terminal"})
        except ValueError as exc:
            rejected.append({"i": i, "fen": f, "why": str(exc)})
    json.dump(rejected, open(os.path.join(outdir, "rejected.json"), "w"), indent=1)
    print("positions usable:", len(fens), "rejected:", len(rejected), flush=True)

    rows = []
    summary = {}
    for threads in (1, 2, 4):
        unstable = []
        for index, fen in enumerate(fens):
            moves = []
            nodes = []
            complaints = []
            for run in range(RUNS):
                token, n, comp = one_run(exe, fen, threads, pc20)
                moves.append(token)
                nodes.append(n)
                complaints += comp
            distinct = sorted({m for m in moves if m})
            nodes_distinct = sorted({n for n in nodes if n is not None})
            row = {"threads": threads, "index": index, "fen": fen,
                   "moves": moves, "distinct_moves": distinct,
                   "unstable": len(distinct) > 1,
                   "node_counts": nodes,
                   "distinct_node_counts": nodes_distinct,
                   "complaints": complaints[:2]}
            rows.append(row)
            if row["unstable"]:
                unstable.append({"index": index, "fen": fen, "moves": moves,
                                 "nodes": nodes, "distinct": distinct})
            json.dump(rows, open(os.path.join(outdir, "thread_instability_%s.json" % label), "w"), indent=1)
        summary["threads_%d" % threads] = {
            "positions": len(fens),
            "unstable": len(unstable),
            "examples": unstable[:3],
        }
        print(json.dumps({"label": label, "threads": threads, "unstable": len(unstable),
                          "of": len(fens)}), flush=True)

    # their claim: Threads 1 node counts identical to the digit
    t1 = [r for r in rows if r["threads"] == 1]
    t1_identical = sum(1 for r in t1 if len(r["distinct_node_counts"]) == 1)
    summary["threads1_positions_with_identical_node_counts"] = t1_identical
    summary["label"] = label
    summary["pc20"] = pc20
    summary["runs_per_cell"] = RUNS
    summary["depth"] = DEPTH
    summary["positions"] = len(fens)
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(outdir, "summary_%s.json" % label), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
