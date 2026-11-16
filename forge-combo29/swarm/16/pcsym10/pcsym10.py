#!/usr/bin/env python3
"""pcsym10.py EXE OUT.tsv META.txt [--limit N] : the 353-pair colour sweep at depth 10 on the PC build under
PC20, Threads 1, fresh process per search with ucinewgame.

One row per position: its depth-10 score/nodes/bestmove, its mirror's, and whether they match. A missing score
or a refused option fails loudly. Resumable: rows already present in OUT.tsv are skipped.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUT, META = sys.argv[1], sys.argv[2], sys.argv[3]
LIMIT = None
if "--limit" in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index("--limit") + 1])
DEPTH = 10

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def search(fen):
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
    known = set()
    for l in uci:
        m = re.match(r"option name (.*) type ", l)
        if m:
            known.add(m.group(1))
    send("isready"); to("readyok", 20)
    for name, val in PC20.items():
        if name not in known:
            raise Missing(f"option {name} absent")
        send(f"setoption name {name} value {val}")
        send("isready")
        got, ok = to("readyok", 20)
        for l in got:
            low = l.lower()
            if "unknown option" in low or "invalid value" in low:
                raise Missing(f"refused: {l}")
    send("ucinewgame"); send("isready"); to("readyok", 20)
    send("position fen " + fen)
    send("isready"); to("readyok", 20)
    send(f"go depth {DEPTH}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = score = nodes = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {DEPTH} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
            nodes = int(m.group(3))
    if score is None:
        raise Missing("no depth-10 score")
    return best, score, nodes


def back(mv):
    if not mv or mv == "0000":
        return None
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/pcsym10/set_G.epd") if l.strip()]
if LIMIT:
    fens = fens[:LIMIT]

done = set()
if os.path.exists(OUT):
    with open(OUT) as fh:
        fh.readline()
        for line in fh:
            done.add(int(line.split("\t")[0]))

if not os.path.exists(OUT):
    with open(OUT, "w") as fh:
        fh.write("idx\tfen\tbm\tscore\tnodes\tmirror_fen\tbm_m\tbm_m_back\tscore_m\tnodes_m\t"
                 "score_equal\tbm_equal\tnodes_equal\n")
with open(META, "w") as m:
    m.write(f"exe {EXE}\ndepth {DEPTH}\nsettings PC20 + Threads 1 + Hash 16\n"
            f"positions {len(fens)}\nThreads 1 per the swarm rule\n")

rows = 0
with open(OUT, "a") as out:
    for idx, fen in enumerate(fens):
        if idx in done:
            continue
        mir = chess.Board(fen).mirror().fen()
        try:
            ba, sa, na = search(fen)
            bb, sb, nb = search(mir)
        except Missing as exc:
            out.write(f"{idx}\t{fen}\tMISSING\t{exc}\n")
            out.flush()
            continue
        bk = back(bb)
        out.write(f"{idx}\t{fen}\t{ba}\t{sa}\t{na}\t{mir}\t{bb}\t{bk}\t{sb}\t{nb}\t"
                  f"{sa == sb}\t{ba == bk}\t{na == nb}\n")
        out.flush()
        rows += 1
        if rows % 25 == 0:
            print(f"  {rows} rows done (idx {idx})", flush=True)
print(f"wrote {rows} new rows")
