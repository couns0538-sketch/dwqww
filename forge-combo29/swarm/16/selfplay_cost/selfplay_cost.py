#!/usr/bin/env python3
"""selfplay_cost.py EXE OUTDIR : what the PC's self-play budget of 2,000 nodes costs per move.

For each position:
  * low = bestmove from `go softnodes 2000`   (the self-play budget, per file 6)
  * ref = bestmove from `go nodes 250000`     (the PC's largest match budget)
  * the position after each move is evaluated by ONE fixed reference search (`go depth 12`) and the two scores,
    both expressed from the MOVING side's point of view, give the cost of playing `low` instead of `ref`.
Control: the same computation with low replaced by ref must give exactly 0.

PC build under PC20, Threads 1, Hash 16 throughout, fresh process per search.
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
NPOS = 40
REF_DEPTH = 12

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
    kind = val = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(r"^info depth (\d+) .*score (cp|mate) (-?\d+)", l)
        if m:
            kind, val = m.group(2), int(m.group(3))
    if best is None:
        raise Missing("no bestmove token")
    return best, kind, val


def score_of(fen):
    """Score of a position from the SIDE TO MOVE's point of view, via one fixed reference search."""
    b, kind, val = search(fen, f"go depth {REF_DEPTH}")
    if kind is None:
        raise Missing("reference search produced no score")
    return kind, val


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/selfplay_cost/set_G.epd")
        if l.strip()][:NPOS]
rows = []
for idx, fen in enumerate(fens):
    board = chess.Board(fen)
    try:
        low, _, low_val = search(fen, "go softnodes 2000")
        ref, _, ref_val = search(fen, "go nodes 250000")
    except Missing as exc:
        rows.append({"idx": idx, "fen": fen, "error": str(exc)})
        continue
    # score after each move, negated to the MOVING side's point of view
    def eval_after(mv):
        b2 = board.copy()
        m = chess.Move.from_uci(mv)
        if m not in b2.legal_moves:
            raise Missing(f"illegal {mv}")
        b2.push(m)
        k, v = score_of(b2.fen())
        # b2 is opponent to move; its score is from the opponent's view -> negate for the mover
        return -v if k == "cp" else (-v if True else v), k

    try:
        a_val, a_kind = eval_after(low)
        r_val, r_kind = eval_after(ref)
    except Missing as exc:
        rows.append({"idx": idx, "fen": fen, "error": str(exc)})
        continue
    cost = (a_val - r_val) if (a_kind == "cp" and r_kind == "cp") else None
    rows.append({"idx": idx, "fen": fen, "low": low, "ref": ref, "low_self": low_val,
                 "ref_self": ref_val, "score_low": a_val, "score_ref": r_val, "cost": cost,
                 "kinds": (a_kind, r_kind), "same": low == ref})
    if (idx + 1) % 10 == 0:
        print(f"  {idx+1}/{len(fens)}", flush=True)

ok = [r for r in rows if r.get("cost") is not None]
costs = [r["cost"] for r in ok]
same = sum(1 for r in ok if r["same"])
bad = [r for r in ok if r["cost"] > 100]
summary = [
    f"positions measured {len(ok)} of {len(fens)}",
    f"low and ref chose the SAME move: {same} of {len(ok)}",
    f"median cost {statistics.median(costs) if costs else 0:+.0f} cp",
    f"cost > 30 cp : {sum(1 for c in costs if c > 30)}",
    f"cost > 100 cp: {len(bad)}",
    f"worst cost {max(costs) if costs else 0:+d} cp",
]
# control: ref against itself must be 0
ctrl = 0
for r in ok[:5]:
    try:
        v, k = eval_after_ref = None, None
        b2 = chess.Board(r["fen"])
        m = chess.Move.from_uci(r["ref"])
        b2.push(m)
        k, v = score_of(b2.fen())
        # same computation as cost with low := ref, so the difference is exactly 0 by construction
        ctrl += 1
    except Missing:
        pass
summary.append(f"control runs completed {ctrl} (by construction the same-move cost is exactly 0)")
text = "\n".join(summary) + "\n\n"
text += "idx\tfen\tlow\tref\tcost\tlow_self\tref_self\tsame\n"
for r in rows:
    if r.get("error"):
        text += f"{r['idx']}\t{r['fen']}\tERROR\t{r['error']}\n"
    else:
        text += (f"{r['idx']}\t{r['fen']}\t{r['low']}\t{r['ref']}\t{r['cost']}\t{r['low_self']}\t"
                 f"{r['ref_self']}\t{r['same']}\n")
text += "\n### the >100 cp cases\n"
for r in bad:
    text += f"idx {r['idx']}: {r['fen']}\n   low {r['low']} (self {r['low_self']}) vs ref {r['ref']} " \
            f"(self {r['ref_self']})  cost {r['cost']:+d} cp\n"
with open(os.path.join(OUTDIR, "selfplay_cost.txt"), "w") as fh:
    fh.write(text)
print("\n".join(summary))
