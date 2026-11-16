#!/usr/bin/env python3
"""Dump EVERYTHING observable about one mismatching colour-mirror pair, data first.

For a chosen FEN and its colour mirror, at two depths:
  - the move list in GENERATION order (what the move generator produces, before scoring)
  - the per-root-move score and node count (from the instrumented build's rootnodes line)
  - the full final PV and its score
Then aligns the two sides through the colour mirror so the first point of divergence is visible.

Nothing here instruments anything new: it reads what the engine already prints plus python-chess's own
move generation for the generation-order column.

usage: dump_one.py INSTRUMENTED_EXE FEN DEPTH1 DEPTH2 OUTFILE
"""
import subprocess
import sys

import chess


def run(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + fen)
    w("isready")
    ready()
    w("go depth %d" % depth)
    roots = {}
    pvs = {}
    best = None
    while True:
        line = r().strip()
        if line.startswith("info string rootnodes"):
            t = line.split()
            d = int(t[3])
            roots[d] = [(x.split(":")[0], int(x.split(":")[1])) for x in t[4:] if ":" in x and not x.startswith("total")]
        elif line.startswith("info") and " pv " in line:
            t = line.split()
            pvs[int(t[t.index("depth") + 1])] = {
                "score_kind": t[t.index("score") + 1], "score": int(t[t.index("score") + 2]),
                "nodes": int(t[t.index("nodes") + 1]),
                "pv": t[t.index("pv") + 1:]}
        elif line.startswith("bestmove"):
            best = line.split()[1]
            break
    p.kill()
    return {"roots": roots, "pvs": pvs, "bestmove": best}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def gen_order(fen):
    """python-chess move generation order (its own ordering; the engine's differs, but this shows the
    SET and gives a stable canonical listing)."""
    b = chess.Board(fen)
    return [m.uci() for m in b.legal_moves]


def main():
    exe, fen, d1, d2, outfile = sys.argv[1:6]
    d1, d2 = int(d1), int(d2)
    mfen = chess.Board(fen).mirror().fen()
    fh = open(outfile, "w")

    def say(s=""):
        fh.write(s + "\n")
        print(s)

    say("POSITION : " + fen)
    say("MIRROR   : " + mfen)
    say("")
    say("=== BOARD ===")
    say(str(chess.Board(fen)))
    say("")
    say("=== MIRRORED BOARD ===")
    say(str(chess.Board(mfen)))
    say("")

    go = gen_order(fen)
    gm = gen_order(mfen)
    say("=== GENERATED MOVE SETS (python-chess order) ===")
    say("self   (%d): %s" % (len(go), " ".join(go)))
    say("mirror (%d): %s" % (len(gm), " ".join(gm)))
    say("mirror, mapped back to the self frame: %s" % " ".join(sorted(mir(x) for x in gm)))
    say("sets equal after mirroring: %s" % (sorted(go) == sorted(mir(x) for x in gm)))
    say("")

    for d in (d1, d2):
        a = run(exe, fen, d)
        b = run(exe, mfen, d)
        say("=== DEPTH %d ===" % d)
        pa = a["pvs"].get(d)
        pb = b["pvs"].get(d)
        say("self   last PV (depth %d): score %s %s nodes %s" %
            (d, pa["score_kind"], pa["score"] if pa else "?", pa["nodes"] if pa else "?"))
        say("       pv: %s" % (" ".join(pa["pv"]) if pa else "?"))
        say("mirror last PV (depth %d): score %s %s nodes %s" %
            (d, pb["score_kind"], pb["score"] if pb else "?", pb["nodes"] if pb else "?"))
        say("       pv: %s" % (" ".join(pb["pv"]) if pb else "?"))
        say("       pv mapped back: %s" % (" ".join(mir(x) for x in pb["pv"]) if pb and pb["pv"] else "?"))
        say("self   bestmove %s | mirror bestmove %s (mapped %s)" %
            (a["bestmove"], b["bestmove"], mir(b["bestmove"]) if b["bestmove"] else "?"))
        say("")
        ra = dict(a["roots"].get(d, []))
        rb = {mir(k): v for k, v in b["roots"].get(d, [])}
        if ra and rb:
            keys = sorted(set(ra) | set(rb))
            say("  per-root-move node counts (self vs mirror mapped back):")
            say("  | move | self nodes | mirror nodes | same |")
            say("  |---|---|---|---|")
            first_diff = None
            for k in keys:
                sa, sb = ra.get(k), rb.get(k)
                same = sa == sb
                if not same and first_diff is None:
                    first_diff = k
                say("  | %s | %s | %s | %s |" % (k, sa, sb, same))
            say("  FIRST DIVERGENCE in generation order: %s" % first_diff)
            say("")
            order_a = [k for k, _ in a["roots"].get(d, [])]
            order_b = [mir(k) for k, _ in b["roots"].get(d, [])]
            say("  GENERATION ORDER self   : %s" % " ".join(order_a))
            say("  GENERATION ORDER mirror : %s" % " ".join(order_b))
            say("  orders identical: %s" % (order_a == order_b))
            for i, (x, y) in enumerate(zip(order_a, order_b)):
                if x != y:
                    say("  FIRST POSITION WHERE THE ORDER DIFFERS: slot %d, self has %s, mirror has %s" % (i, x, y))
                    break
        say("")
    fh.close()


if __name__ == "__main__":
    main()
