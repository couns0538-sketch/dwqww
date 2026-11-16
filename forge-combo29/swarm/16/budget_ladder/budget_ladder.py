#!/usr/bin/env python3
"""budget_ladder.py EXE OUTDIR : what does raising the self-play node budget BUY?

For budgets 2000 / 8000 / 20000 / 50000 against the reference budget 250000, on real-game positions:
  cost(B) = score_after(move_ref) - score_after(move_B)   from the mover's view (positive = B is worse),
judged by ONE fixed deeper reference search (go depth 16). PC build under PC20, Threads 1, Hash 16, cold.
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
BUDGETS = [2000, 8000, 20000, 50000]
REF = 250000
REF_DEPTH = 16

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def run(fen, gov, depth_for_score=None):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=400):
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
    lines, ok = to("bestmove", 400)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing(f"no bestmove for {gov}")
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


def score_at(fen):
    """One fixed reference judgement of a position, from ITS side to move."""
    _, kind, val = run(fen, f"go depth {REF_DEPTH}")
    if kind is None:
        raise Missing("reference score missing")
    return kind, val


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/budget_ladder/set_G.epd")
        if l.strip()][:NPOS]
rows = []
for idx, fen in enumerate(fens):
    board = chess.Board(fen)
    try:
        mv_ref, _, _ = run(fen, f"go nodes {REF}")
        b2 = board.copy(); b2.push(chess.Move.from_uci(mv_ref))
        rk, rv = score_at(b2.fen())
        if rk != "cp":
            continue
        ref_score = -rv                      # mover's view
        rec = {"idx": idx, "fen": fen, "ref": mv_ref, "ref_score": ref_score}
        for B in BUDGETS:
            mv, _, _ = run(fen, f"go nodes {B}")
            bb = board.copy(); bb.push(chess.Move.from_uci(mv))
            bk, bv = score_at(bb.fen())
            rec[f"mv{B}"] = mv
            rec[f"cost{B}"] = (-bv - ref_score) if bk == "cp" else None
        rows.append(rec)
    except Missing as exc:
        rows.append({"idx": idx, "fen": fen, "error": str(exc)})
    if (idx + 1) % 5 == 0:
        print(f"  {idx+1}/{len(fens)}", flush=True)

ok = [r for r in rows if "error" not in r]
out = [f"exe {EXE}", f"positions scored {len(ok)} of {len(fens)}", f"reference budget {REF}, reference depth {REF_DEPTH}",
       "cost positive = that budget's move is WORSE than the reference move", "",
       "budget | same move as ref | median cost | >30 cp worse | >100 cp worse | total damage (sum of positive costs)"]
print(out[-1])
for B in BUDGETS:
    costs = [r[f"cost{B}"] for r in ok if r.get(f"cost{B}") is not None]
    same = sum(1 for r in ok if r.get(f"mv{B}") == r["ref"])
    if not costs:
        out.append(f"{B}: no usable rows")
        continue
    line = (f"{B:6d} | {same:3d} of {len(costs):3d} | {statistics.median(costs):+5.0f} cp | "
            f"{sum(1 for c in costs if c > 30):3d} | {sum(1 for c in costs if c > 100):3d} | "
            f"{sum(c for c in costs if c > 0):+6d} cp")
    out.append(line)
    print(line, flush=True)

# how many moves CHANGE between 2000 and 8000
ch = sum(1 for r in ok if r.get("mv2000") != r.get("mv8000"))
out.append("")
out.append(f"moves that differ between 2000 and 8000 nodes: {ch} of {len(ok)}")
print(out[-1])
with open(os.path.join(OUTDIR, "budget_ladder.txt"), "w") as fh:
    fh.write("\n".join(out) + "\n\n")
    fh.write("idx\tfen\tref\t" + "\t".join(f"mv{B}\tcost{B}" for B in BUDGETS) + "\n")
    for r in rows:
        if "error" in r:
            fh.write(f"{r['idx']}\t{r['fen']}\tERROR\t{r['error']}\n")
        else:
            fh.write(f"{r['idx']}\t{r['fen']}\t{r['ref']}\t" +
                     "\t".join(f"{r.get(f'mv{B}')}\t{r.get(f'cost{B}')}" for B in BUDGETS) + "\n")
