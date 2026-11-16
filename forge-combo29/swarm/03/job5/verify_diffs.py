#!/usr/bin/env python3
"""verify_diffs.py BASE_EXE PC_EXE TSFILE OUT : for each position where the two builds played different moves,
establish whether each played move is LEGAL and how the builds compare when searched deeper.

For each such position:
  * legality of both played moves (python-chess) — an illegal move would be a real fault;
  * `go depth` 8, 12, 16 on BOTH builds, fresh process each, Threads 1, recording bestmove + score + nodes;
  * whether the two builds CONVERGE (same bestmove) at some depth, and at which.
It does not decide "which is better"; it reports the evidence (score, and whether a claimed mate's PV really ends in
checkmate, checked by replaying the PV with python-chess).
"""
import os
import re
import subprocess
import sys

import chess

BASE, PC, TSFILE, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
fens_all = [l.strip().split("\t")[-1] for l in open(TSFILE) if l.strip()]
rows = [l.rstrip("\n").split("\t") for l in open(OUT + ".input.tsv") if l.strip()]
os.makedirs(OUT + ".raw", exist_ok=True)


def search(exe, fen, depth, tag):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(f"{OUT}.raw/{tag}.txt", "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        lines = []
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            lines.append(s)
            if s.startswith(tok):
                return lines

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {depth}")
    lines = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    bm = [s for s in lines if s.startswith("bestmove")][-1].split()[1]
    info = [s for s in lines if s.startswith("info depth") and " pv " in s]
    last = info[-1] if info else ""
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    score = f"{m.group(1)} {m.group(2)}" if m else "?"
    n = re.search(r" nodes (\d+)", last)
    nodes = int(n.group(1)) if n else -1
    pv = last.split(" pv ")[1].split() if " pv " in last else []
    return bm, score, nodes, pv


def pv_is_mate(fen, pv):
    b = chess.Board(fen)
    try:
        for mv in pv:
            b.push_uci(mv)
    except Exception:  # noqa: BLE001
        return "PV_ILLEGAL"
    return b.is_checkmate()


out = []
for r in rows:
    idx = int(r[0])
    fen = fens_all[idx]
    board = chess.Board(fen)
    legal = {m.uci() for m in board.legal_moves}
    base_bm, pc_bm = r[1], r[2]
    out.append(f"=== position {idx}")
    out.append(f"FEN: {fen}")
    out.append(f"legal moves: {len(legal)}   base plays {base_bm} (legal={base_bm in legal}, "
               f"legal in python-chess={base_bm in legal})   pc plays {pc_bm} (legal={pc_bm in legal})")
    if base_bm not in legal or pc_bm not in legal:
        out.append("!!! AN ILLEGAL MOVE WAS PLAYED — this is a real fault, not a tie-break")
    for depth in (8, 12, 16):
        bb, bs, bn, bpv = search(BASE, fen, depth, f"p{idx}_d{depth}_base")
        qb, qs, qn, qpv = search(PC, fen, depth, f"p{idx}_d{depth}_pc")
        conv = "SAME" if bb == qb else "differ"
        extra = ""
        for who, sc, pv in (("base", bs, bpv), ("pc", qs, qpv)):
            if sc.startswith("mate"):
                extra += f" [{who} mate PV ends in checkmate: {pv_is_mate(fen, pv)}]"
        out.append(f"  depth {depth:2d}: base {bb:6s} {bs:9s} {bn:>8} nodes | "
                   f"pc {qb:6s} {qs:9s} {qn:>8} nodes | {conv}{extra}")
    out.append("")

open(OUT + ".txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
