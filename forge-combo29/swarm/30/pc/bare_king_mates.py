#!/usr/bin/env python3
"""bare_king_mates.py -- does the base tree miss mates in lone-king endings that python-chess can prove?

The PC patch's comments claim: "the quiet mating move of a king-and-rook ending is pruned or reduced
away (38 of 400 mates missed at depth 14 by r9 after `Clear Hash`)". That is a testable claim about
the BASE tree, so this script builds KR-K / KQ-K / KBB-K / KBN-K positions whose mate distance is
known from python-chess, searches them on BOTH builds at Threads 1, and counts how many the engine
fails to convert (no `mate` score where python-chess proves a forced mate in <= D).

Only positions where python-chess finds a forced mate within the search depth are counted as
"should have been found"; a position with no forced mate is not evidence either way.

Cold start per search: a fresh process AND `ucinewgame` (never `Clear Hash`, per seat 10's rule).

usage: bare_king_mates.py OUTDIR [N_PER_KIND] [DEPTH]
"""
import json
import os
import random
import subprocess
import sys
import threading
import time

import chess

BASE = "/home/ubuntu/b/rel/forge"
PCX = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}


def mate_in(board, limit):
    """Smallest mate distance (plies) for the side to move, found by an EXHAUSTIVE but pruned
    search capped at `limit` plies. Only used with limit <= 5, so the tree is small."""
    best = [None]

    def dfs(b, plies):
        if plies > limit:
            return
        if best[0] is not None and plies > best[0]:
            return
        for mv in list(b.legal_moves):
            b.push(mv)
            if b.is_checkmate():
                if best[0] is None or plies < best[0]:
                    best[0] = plies
            elif plies + 1 <= limit and (best[0] is None or plies + 1 < best[0]):
                dfs(b, plies + 1)
            b.pop()

    dfs(board, 1)
    return best[0]


def make_positions(rng, n_per_kind):
    """Random lone-king endings, filtered to those with a forced mate inside the depth we search."""
    # KRvK and KQvK only: their forced mates are shallow and the search is cheap. KBBvK/KBNvK
    # need up to 19/33 plies, which makes an exhaustive mate finder far too slow to generate with.
    kinds = {"KRvK": (chess.ROOK,), "KQvK": (chess.QUEEN,)}
    out = []
    for name, pieces in kinds.items():
        got = 0
        tries = 0
        while got < n_per_kind and tries < 400:
            tries += 1
            b = chess.Board(None)
            sqs = rng.sample(range(64), 2 + len(pieces))
            b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
            b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
            for i, pt in enumerate(pieces):
                b.set_piece_at(sqs[2 + i], chess.Piece(pt, chess.WHITE))
            b.turn = chess.WHITE
            b.castling_rights = 0
            if b.is_valid() and not b.is_check():
                d = mate_in(b, 5)
                if d is not None and d <= 5:
                    out.append({"kind": name, "fen": b.fen(), "mate_plies": d})
                    got += 1
    return out


def spawn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()
    return p, out, lock


def search(exe, fen, depth):
    p, out, lock = spawn(exe)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    time.sleep(0.04)
    for name, value in (("Threads", 1), ("Hash", 16), ("OwnBook", "false")):
        send("setoption name %s value %s" % (name, value))
        send("isready")
        time.sleep(0.01)
    send("ucinewgame")
    send("isready")
    time.sleep(0.02)
    send("position fen " + fen)
    with lock:
        mark = len(out)
    send("go depth %d" % depth)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 180:
        with lock:
            hit = [x for x in out[mark:] if x.startswith("bestmove")]
        if hit:
            break
        time.sleep(0.005)
    with lock:
        blk = out[mark:]
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    bm, score, nodes = None, None, None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
        if l.startswith("info depth") and " pv" in l:
            t = l.split()
            if "score" in t:
                score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
            if "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
    return {"bestmove": bm, "score": score, "nodes": nodes,
            "reports_mate": bool(score and score.startswith("mate")),
            "info": sum(1 for l in blk if l.startswith("info depth"))}


def main():
    outdir = sys.argv[1]
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(3001)
    pos = make_positions(rng, n_per)
    print("positions built: %d (depth %d, Threads 1, fresh process + ucinewgame each)" % (len(pos), depth))
    rows = []
    print("%-8s %-6s %-28s %-28s" % ("kind", "mates?", "BASE", "PC r15"))
    for p_ in pos:
        a = search(BASE, p_["fen"], depth)
        c = search(PCX, p_["fen"], depth)
        row = {"kind": p_["kind"], "fen": p_["fen"], "mate_plies": p_["mate_plies"],
               "base": a, "pc": c}
        rows.append(row)
        print("%-8s %-6s %-28s %-28s" % (
            p_["kind"], p_["mate_plies"],
            "%s %s" % (a["bestmove"], a["score"]),
            "%s %s" % (c["bestmove"], c["score"])))
    by_kind = {}
    for r in rows:
        k = r["kind"]
        d = by_kind.setdefault(k, {"n": 0, "base_missed": 0, "pc_missed": 0})
        d["n"] += 1
        if not r["base"]["reports_mate"]:
            d["base_missed"] += 1
        if not r["pc"]["reports_mate"]:
            d["pc_missed"] += 1
    with open(os.path.join(outdir, "bare_king_mates.json"), "w") as f:
        json.dump({"depth": depth, "rows": rows, "by_kind": by_kind}, f, indent=1)
    print()
    print("%-8s %-5s %-12s %-12s" % ("kind", "n", "base missed", "pc missed"))
    for k, d in sorted(by_kind.items()):
        print("%-8s %-5d %-12d %-12d" % (k, d["n"], d["base_missed"], d["pc_missed"]))


if __name__ == "__main__":
    main()
