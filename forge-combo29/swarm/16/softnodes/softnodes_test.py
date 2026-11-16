#!/usr/bin/env python3
"""softnodes_test.py EXE OUTDIR : `go softnodes N` on the PC build under PC20, Threads 1.

For each budget N and each position: REPS fresh processes, `ucinewgame` before the search, PC20 settings.
Records every info line, the `info string softnodes nodes X` line if present, and the bestmove, so:
  * determinism  = one distinct (bestmove, last-depth, score, nodes) triple over the reps
  * finished depth = the bestmove equals the PV's first move on the last depth line
  * overshoot    = reported nodes / N
Also runs `go nodes` at the PC's match budgets for the same determinism check.
"""
import os
import re
import sys
import subprocess
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
REPS = 20
NODE_REPS = 5

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}

# positions from real games (set G) plus startpos, which is what the PC's self-play starts from
POSITIONS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G0", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G1", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G2", "6k1/p4r1p/1p2Q3/2p5/2P1N3/1P3P2/PK6/6q1 b - - 0 1"),
]
BUDGETS = [2000, 20000, 50000]


class Missing(Exception):
    pass


def search(fen, gov):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=240):
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

    send("uci")
    uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    send("isready"); to("readyok", 20)
    for name, val in PC20.items():
        if name not in known:
            raise Missing(f"option {name} absent")
        send(f"setoption name {name} value {val}")
        send("isready")
        got, _ = to("readyok", 20)
        for l in got:
            if "unknown option" in l.lower() or "invalid value" in l.lower():
                raise Missing(f"refused {l}")
    send("ucinewgame"); send("isready"); to("readyok", 20)
    send("position fen " + fen)
    send("isready"); to("readyok", 20)
    send(gov)
    lines, ok = to("bestmove", 240)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    depths = []
    best = None
    soft = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.match(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+).*?(?: pv (.*))?$", l)
        if m:
            depths.append((int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)),
                           (m.group(5) or "").split()))
        if l.startswith("info string softnodes"):
            mm = re.search(r"nodes (\d+)", l)
            if mm:
                soft = int(mm.group(1))
    if best is None:
        raise Missing("no bestmove line")
    if not depths:
        raise Missing("no info depth line")
    last = depths[-1]
    pv_first = last[4][0] if last[4] else None
    return {"best": best, "depth": last[0], "score": f"{last[1]} {last[2]}", "nodes": last[3],
            "soft": soft, "pv_first": pv_first,
            "finished": (best == pv_first), "ndepths": len(depths)}


out = [f"exe {EXE}", "PC20 + Threads 1 + Hash 16; fresh process + ucinewgame per search", ""]
for label, fen in POSITIONS:
    out.append(f"### {label}  {fen}")
    for budget in BUDGETS:
        triples = {}
        records = []
        try:
            for _ in range(REPS if budget == 2000 else 5):
                r = search(fen, f"go softnodes {budget}")
                records.append(r)
                key = (r["best"], r["depth"], r["score"], r["nodes"])
                triples[key] = triples.get(key, 0) + 1
            distinct = len(triples)
            over = [r["nodes"] / budget for r in records]
            fin = sum(1 for r in records if r["finished"])
            line = (f"  softnodes {budget:6d}: reps {len(records)} distinct results {distinct} | "
                    f"depth {records[0]['depth']} score {records[0]['score']} nodes {records[0]['nodes']} | "
                    f"overshoot min {min(over):.3f}x max {max(over):.3f}x | "
                    f"finished-depth {fin}/{len(records)}")
            if distinct > 1:
                line += "  <-- NOT DETERMINISTIC"
        except Missing as exc:
            line = f"  softnodes {budget:6d}: NOT MEASURED: {exc}"
        out.append(line)
        print(line, flush=True)
    # go nodes at the match budgets
    for budget in (20000, 50000, 250000):
        try:
            results = [search(fen, f"go nodes {budget}") for _ in range(NODE_REPS)]
            keys = {(r["best"], r["depth"], r["score"], r["nodes"]) for r in results}
            line = (f"  go nodes  {budget:6d}: reps {len(results)} distinct results {len(keys)} | "
                    f"depth {results[0]['depth']} score {results[0]['score']} nodes {results[0]['nodes']}")
            if len(keys) > 1:
                line += "  <-- NOT DETERMINISTIC"
        except Missing as exc:
            line = f"  go nodes  {budget:6d}: NOT MEASURED: {exc}"
        out.append(line)
        print(line, flush=True)
    out.append("")

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "softnodes.txt"), "w") as fh:
    fh.write(text)
