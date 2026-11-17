#!/usr/bin/env python3
"""loneking11.py -- the 11 lone-king divergence boards, and the move each build plays.

The FENs are seat 08's `check_s03f13.txt` divergence table (the same 11 boards as
08-F37/F38). They are hard-coded here so this script does not depend on another
seat's branch being fetched, and each is re-parsed by python-chess before use: a
FEN that does not parse is a hard failure, not a silent skip.

Usage: loneking11.py EXE [--depth N] [--json OUT]
Prints one row per board: depth, bestmove, score, nodes, and the reduction
counters of the final iteration.
"""
import argparse
import json
import os
import re
import subprocess
import sys

BOARDS = [
    ("8/8/2B1k3/8/3PP3/P7/4K3/7R b - - 11 95", "e6d6", "e6e7", -9980),
    ("8/8/2k5/4P3/3P4/P7/4K3/7R w - - 1 106", "e2d3", "h1c1", -9428),
    ("8/2k5/4P3/8/3P4/PR6/3K4/8 b - - 0 109", "c7d8", "c7c6", 10981),
    ("8/4k3/8/6R1/8/P7/3K4/8 b - - 1 116", "e7d7", "e7d6", -14040),
    ("1R6/8/k7/8/8/P7/8/2K5 b - - 15 123", "a6a7", "a6a5", -7526),
    ("8/8/8/4R3/2k5/P7/8/2K5 w - - 22 127", "a3a4", "c1c2", 621),
    ("8/8/8/1R6/1K6/P7/3k4/8 b - - 57 144", "d2e3", "d2e1", -6547),
    ("8/8/P7/8/8/4K3/1k6/8 b - - 18 186", "b2b3", "b2c2", -3356),
    ("6K1/2b5/p1k5/8/8/8/8/b7 b - - 5 137", "a6a5", "a1d4", -9605),
    ("8/2k5/p7/8/8/7K/1b6/b7 w - - 26 148", "h3g4", "h3g2", -13946),
    ("2k5/8/p7/6b1/8/2b4K/8/8 b - - 47 158", "a6a5", "g5f6", -8191),
]

# counter-case boards are the ones where cap-OFF visits MORE nodes
COUNTER = {f for f, b, p, d in BOARDS if d > 0}

RE_DEPTH = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*? nodes (\d+) ")
RE_BEST = re.compile(r"^bestmove (\S+)")
RE_LMR = re.compile(r"^info string lmr depth (\d+) root (\S+) applied (\d+)")


def parse_lmr(lines):
    """The last depth's per-root and total blocks.

    Tokens are `key value` pairs for depth/root/applied/research/rej/cap_gate and
    `key=value` inside the bracketed guard breakdown and the magnitude lists, so the
    bracket contents are parsed separately rather than by splitting on '='.
    """
    total = None
    per_root = {}
    last_depth = -1
    for line in lines:
        if not line.startswith("info string lmr depth "):
            continue
        body = line[len("info string lmr "):]
        head, _, tail = body.partition(" applied ")
        htok = head.split()
        if len(htok) < 4:
            continue
        d = int(htok[1])
        root = htok[3]
        kv = {"applied": tail.split()[0] if tail.split() else "0"}
        m = re.search(r"\brmean ([-\d.]+)", body)
        if m:
            kv["rmean"] = m.group(1)
        for key in ("research", "rej", "cap_gate", "cap_clamp"):
            m = re.search(rf"\b{key} (\d+)", body)
            if m:
                kv[key] = m.group(1)
        m = re.search(r"\bcap_rmean ([-\d.]+)", body)
        if m:
            kv["cap_rmean"] = m.group(1)
        m = re.search(r"\[([^\]]*)\]", body)
        if m:
            toks = m.group(1).split()
            for j in range(0, len(toks) - 1, 2):
                kv[f"guard_{toks[j]}"] = toks[j + 1]
        m = re.search(r"\bmag((?: r-?\d+=\d+)+)", body)
        if m:
            kv["mag"] = dict(t.partition("=")[::2] for t in m.group(1).split())
        m = re.search(r"\bcap_mag((?: r-?\d+=\d+)+)", body)
        if m:
            kv["cap_mag"] = dict(t.partition("=")[::2] for t in m.group(1).split())
        last_depth = max(last_depth, d)
        if root == "all":
            total = kv
        else:
            per_root[root] = kv
    return last_depth, total, per_root


def run(exe, fen, depth, opts):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            lines.append(line)
            low = line.lower()
            if low.startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR on {fen}: {line}")
            if pred(line):
                return line

    send("uci")
    until(lambda l: l.startswith("uciok"))
    for k, v in opts:
        send(f"setoption name {k} value {v}")
        send("isready")
        until(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"position fen {fen}")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"go depth {depth}")
    best = until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=30)
    score = nodes = last_depth = None
    for line in lines:
        m = RE_DEPTH.match(line)
        if m:
            last_depth = int(m.group(1))
            kind = m.group(2)
            val = int(m.group(3))
            score = (kind, val)
            nodes = int(m.group(4))
    mv = RE_BEST.match(best).group(1) if best else None
    return {"fen": fen, "bestmove": mv, "score": score, "nodes": nodes,
            "depth": last_depth, "lines": lines}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    try:
        import chess
    except ImportError:
        chess = None

    rows = []
    print(f"exe {a.exe}  depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print(f"{'board':46s} {'cls':5s} {'move':6s} {'score':>10s} {'nodes':>7s} "
          f"{'applied':>7s} {'rmean':>5s} {'research':>8s} {'rej':>6s} "
          f"{'capgate':>7s} {'clamp':>6s} {'caprmean':>8s}")
    for fen, base_mv, pc_mv, delta in BOARDS:
        if chess is not None:
            chess.Board(fen)  # hard failure if the FEN does not parse
        r = run(a.exe, fen, a.depth, [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")])
        d, total, per_root = parse_lmr(r["lines"])
        cls = "CNTR" if fen in COUNTER else "pred"
        sc = f"{r['score'][0]}{r['score'][1]}" if r["score"] else "?"
        row = {
            "fen": fen, "cls": cls, "bestmove": r["bestmove"], "score": sc,
            "nodes": r["nodes"], "base_move": base_mv, "pc_move": pc_mv,
            "capoff_delta_from_08": delta,
            "lmr_depth": d, "lmr_total": total, "lmr_per_root": per_root,
        }
        rows.append(row)
        def g(k):
            return total.get(k, "-") if total else "-"
        print(f"{fen:46s} {cls:5s} {str(r['bestmove']):6s} {sc:>10s} {r['nodes']:>7d} "
              f"{g('applied'):>7s} {g('rmean'):>5s} {g('research'):>8s} {g('rej'):>6s} "
              f"{g('cap_gate'):>7s} {g('cap_clamp'):>6s} {g('cap_rmean', ):>8s}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
