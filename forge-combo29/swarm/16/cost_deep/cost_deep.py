#!/usr/bin/env python3
"""cost_deep.py EXE OUTDIR : re-judge S-F30's largest costs with DEEPER reference searches.

Reads the S-F30 table for positions with |cost| > 30 cp, then for each candidate move searches the resulting
position at depths 12, 14, 16, 18 and reports the mover's score at each depth, so the cost's sign and size can
be seen to be stable (or not) as the reference deepens. PC build under PC20, Threads 1, Hash 16, cold.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
SRC = "/agent/repos/dwqww/forge-combo29/swarm/16/selfplay_cost/raw/selfplay_cost.txt"
DEPTHS = [12, 14, 16, 18]
THRESH = 30

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def score_at(fen, depth):
    """Score of `fen` (from the side to move) at a fixed depth."""
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
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 400)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing(f"no bestmove at depth {depth}")
    kind = val = None
    for l in lines:
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+)", l)
        if m:
            kind, val = m.group(1), int(m.group(2))
    if kind is None:
        raise Missing(f"no score at depth {depth}")
    return kind, val


# collect the S-F30 cases with |cost| > THRESH
cases = []
with open(SRC) as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 8 and p[0].isdigit() and p[2] not in ("ERROR",):
            cost = int(p[4])
            if abs(cost) > THRESH:
                cases.append({"idx": int(p[0]), "fen": p[1], "low": p[2], "ref": p[3],
                              "cost12_signed": cost})
print(f"cases with |cost| > {THRESH}: {len(cases)}")

out = [f"exe {EXE}", f"PC20 + Threads 1 + Hash 16; reference depths {DEPTHS}",
       "note: S-F30's sign was INVERTED; the column `cost12_signed` below is S-F30's raw number, where a",
       "POSITIVE value means the low (2,000-node) move was BETTER. The `mover` scores below are the ground",
       "truth: the score of the position after the move, from the MOVER's point of view.", ""]
for c in cases:
    board = chess.Board(c["fen"])
    block = [f"### idx {c['idx']}  {c['fen']}",
             f"    low {c['low']}   ref {c['ref']}   S-F30 raw cost {c['cost12_signed']:+d}"]
    per = {}
    for label, mv in (("low", c["low"]), ("ref", c["ref"])):
        m = chess.Move.from_uci(mv)
        if m not in board.legal_moves:
            block.append(f"    {label} {mv}: ILLEGAL here")
            continue
        b2 = board.copy()
        b2.push(m)
        row = []
        for d in DEPTHS:
            try:
                k, v = score_at(b2.fen(), d)
                # b2 has the OPPONENT to move; negate to get the mover's view
                row.append((d, k, -v))
            except Missing as exc:
                row.append((d, "MISSING", None))
        per[label] = row
        block.append(f"    {label:3s} {mv}: " +
                     "  ".join(f"d{d}:{('mate ' + str(-v)) if k == 'mate' else v}"
                               for d, k, v in row if v is not None))
    if "low" in per and "ref" in per:
        deltas = []
        for (d1, k1, v1), (d2, k2, v2) in zip(per["low"], per["ref"]):
            if v1 is not None and v2 is not None and k1 == "cp" and k2 == "cp":
                # cost of LOW: positive = the low move is worse
                deltas.append((d1, v2 - v1))
        block.append("    cost of LOW (positive = low is worse): " +
                     "  ".join(f"d{d}:{x:+d}" for d, x in deltas))
        c["deltas"] = deltas
    out.append("\n".join(block))
    out.append("")
    print("\n".join(block), flush=True)

# summary: sign stability and whether the magnitude shrinks
stable = 0
comparable = 0
for c in cases:
    ds = c.get("deltas") or []
    if len(ds) >= 2:
        comparable += 1
        signs = {1 if x > 0 else (-1 if x < 0 else 0) for _, x in ds}
        if len(signs) == 1:
            stable += 1
out.append(f"### sign stability: {stable} of {comparable} cases keep the same sign at every depth")
print(out[-1])
text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "cost_deep.txt"), "w") as fh:
    fh.write(text)
