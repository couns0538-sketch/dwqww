#!/usr/bin/env python3
"""stress_softnodes.py EXE OUTDIR : is the softnodes overshoot bounded?

Runs `go softnodes 2000` and `go softnodes 200000` on 8 quiet G positions (quiet = few captures, from the same
G set the PC's games produce), 3 reps each, PC20 + Threads 1 + Hash 16, fresh process + ucinewgame.
Records overshoot = reported nodes / budget, determinism and finished-depth for every run.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
REPS = 3

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def search(fen, gov):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=300):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci"); uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    send("isready"); to("readyok", 20)
    for n, v in PC20.items():
        if n not in known:
            raise Missing(f"option {n} absent")
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 20)
    send("ucinewgame"); send("isready"); to("readyok", 20)
    send("position fen " + fen); send("isready"); to("readyok", 20)
    send(gov)
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = None
    depths = []
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.match(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+).*?(?: pv (.*))?$", l)
        if m:
            depths.append((int(m.group(1)), f"{m.group(2)} {m.group(3)}", int(m.group(4)),
                           (m.group(5) or "").split()))
    if not depths or best is None:
        raise Missing("missing depth line or bestmove")
    last = depths[-1]
    return {"best": best, "depth": last[0], "score": last[1], "nodes": last[2],
            "finished": best == (last[3][0] if last[3] else None)}


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job2/G_nocastle.fens")
        if l.strip()]
# pick the 8 quietest by python-chess's legal capture count (quiet = fewest captures available)
scored = []
for fen in fens:
    b = chess.Board(fen)
    caps = sum(1 for m in b.legal_moves if b.is_capture(m))
    scored.append((caps, fen))
scored.sort()
QUIET = [(f"quiet{i}", fen, caps) for i, (caps, fen) in enumerate(scored[:8])]

out = [f"exe {EXE}", "PC20 + Threads 1 + Hash 16; fresh process + ucinewgame per search",
       "positions chosen: the 8 G positions with the FEWEST legal captures", ""]
for label, fen, caps in QUIET:
    block = [f"### {label} (captures available: {caps}) {fen}"]
    for budget in (2000, 200000):
        try:
            rs = [search(fen, f"go softnodes {budget}") for _ in range(REPS)]
            keys = {(r["best"], r["depth"], r["score"], r["nodes"]) for r in rs}
            over = [r["nodes"] / budget for r in rs]
            fin = sum(1 for r in rs if r["finished"])
            block.append(f"  N={budget:6d} distinct {len(keys)} overshoot {min(over):.3f}x..{max(over):.3f}x "
                         f"depth {rs[0]['depth']} nodes {rs[0]['nodes']} finished {fin}/{len(rs)}")
        except Missing as exc:
            block.append(f"  N={budget:6d} NOT MEASURED: {exc}")
    out.append("\n".join(block))
    print(out[-1], flush=True)
    out.append("")

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "stress.txt"), "w") as fh:
    fh.write(text)
