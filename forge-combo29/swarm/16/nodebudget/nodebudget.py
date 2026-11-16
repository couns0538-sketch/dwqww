#!/usr/bin/env python3
"""nodebudget.py EXE OUTDIR : the PC's match node budgets on real-game positions.

`go nodes 20000 / 50000 / 250000` on the PC build under PC20, Threads 1, Hash 16, 40 G positions,
fresh process + ucinewgame per search. For each position and budget: bestmove, score, depth, nodes.
Checks every move's legality with python-chess and compares moves/scores across budgets.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
NPOS = 40
BUDGETS = [20000, 50000, 250000]

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def search(fen, budget):
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
    send(f"go nodes {budget}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = None
    last = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            last = (int(m.group(1)), f"{m.group(2)} {m.group(3)}", m.group(2), int(m.group(3)),
                    int(m.group(4)))
    if best is None or last is None:
        raise Missing("missing bestmove or info")
    return {"best": best, "depth": last[0], "score": last[1], "kind": last[2], "val": last[3],
            "nodes": last[4]}


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/nodebudget/set_G.epd")
        if l.strip()][:NPOS]
rows = []
for idx, fen in enumerate(fens):
    board = chess.Board(fen)
    legal = {m.uci() for m in board.legal_moves}
    rec = {"idx": idx, "fen": fen}
    for b in BUDGETS:
        try:
            rec[b] = search(fen, b)
            rec[b]["legal"] = rec[b]["best"] in legal or rec[b]["best"] == "0000"
        except Missing as exc:
            rec[b] = {"error": str(exc), "legal": None}
    rows.append(rec)
    if (idx + 1) % 10 == 0:
        print(f"  {idx+1} positions done", flush=True)

with open(os.path.join(OUTDIR, "nodebudget.tsv"), "w") as fh:
    fh.write("idx\tfen\tbudget\tbest\tscore\tdepth\tnodes\tlegal\n")
    for r in rows:
        for b in BUDGETS:
            v = r.get(b, {})
            if "error" in v:
                fh.write(f"{r['idx']}\t{r['fen']}\t{b}\tERROR\t{v['error']}\n")
            else:
                fh.write(f"{r['idx']}\t{r['fen']}\t{b}\t{v['best']}\t{v['score']}\t{v['depth']}\t"
                         f"{v['nodes']}\t{v['legal']}\n")

# summary
ok_rows = [r for r in rows if all("error" not in r.get(b, {}) for b in BUDGETS)]
same_all = sum(1 for r in ok_rows if len({r[b]["best"] for b in BUDGETS}) == 1)
same_low_high = sum(1 for r in ok_rows if r[20000]["best"] == r[250000]["best"])
illegal = sum(1 for r in rows for b in BUDGETS if r.get(b, {}).get("legal") is False)
changed = [r for r in ok_rows if r[20000]["best"] != r[250000]["best"]]
regress = []
for r in changed:
    a, c = r[20000], r[250000]
    if a["kind"] == "cp" and c["kind"] == "cp":
        regress.append((r["idx"], r["fen"], a["best"], a["val"], c["best"], c["val"], c["val"] - a["val"]))
summary = [
    f"positions measured {len(ok_rows)} of {NPOS}",
    f"same move at all three budgets: {same_all}",
    f"same move at 20000 and 250000 : {same_low_high}",
    f"illegal moves: {illegal}",
    f"moves that changed 20000 -> 250000: {len(changed)}",
]
for x in regress:
    summary.append(f"  changed idx {x[0]}: {x[2]} ({x[3]}) -> {x[4]} ({x[5]})  delta {x[6]:+d} cp")
text = "\n".join(summary) + "\n"
print(text)
with open(os.path.join(OUTDIR, "summary.txt"), "w") as fh:
    fh.write(text)
