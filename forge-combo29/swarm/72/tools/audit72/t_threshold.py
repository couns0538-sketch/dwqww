"""Threshold and drawn-root behaviour, measured through the search.

The engine's root draw bail is `alpha_beta(ply=0)` -> `is_repetition() ||
halfmove_clock() >= 100 || is_insufficient_material()` returns 0.  So the
observable signature of "root deemed drawn" is score 0 with a tiny node count.

Every fixture is gated by `Probe`, which validates the FEN with python-chess,
scans both reply streams for a refusal, and asserts perft-1 agreement.
"""

import subprocess

import chess

from engine import Probe

# Rook shuffle: 4 ply cycle returning to the start.  Material-bearing so
# is_insufficient_material() cannot mask the verdict.
BASE = "4k3/8/8/8/8/8/8/1R2K3 w - - 0 1"
CYCLE = ["b1b2", "e8d8", "b2b1", "d8e8"]


def cycles(n):
    moves = []
    for _ in range(n):
        moves.extend(CYCLE)
    return moves


def oracle_occurrences(fen, moves):
    board = chess.Board(fen)
    for m in moves:
        board.push_uci(m)
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


ROWS = []


def halfmove_after(fen, moves):
    seq = subprocess.run(["build/probe", "seq", fen, *moves],
                         capture_output=True, text=True, timeout=30)
    last = [l for l in seq.stdout.splitlines() if l.startswith("PLY ")][-1]
    return int([t for t in last.split() if t.startswith("halfmove=")][0].split("=")[1])


def record(section, fixture, occ, draw_expected, result, note=""):
    drawn = result["score"] == ("cp", 0) and result["nodes"] <= 64
    agree = drawn == draw_expected
    ROWS.append({
        "section": section, "fixture": fixture, "occurrences": occ,
        "engine_drawn_root": drawn, "fide_draw": draw_expected,
        "agree": agree, "score": result["score"], "nodes": result["nodes"],
        "bestmove": result["bestmove"], "note": note,
    })
    score_text = "%s%d" % result["score"] if result["score"] else "-"
    print("%-44s occ=%d score=%-9s nodes=%-6d drawn=%-5s want=%-5s %s %s" % (
        fixture, occ, score_text, result["nodes"], drawn, draw_expected,
        "OK" if agree else "WRONG", note))
    return agree


def main():
    fails = []

    print("=" * 92)
    print("1) THRESHOLD: 1..5 occurrences of the root position (FIDE draws at 3)")
    print("=" * 92)
    for n in range(0, 5):
        moves = cycles(n)
        occ = oracle_occurrences(BASE, moves)
        assert occ == n + 1, (occ, n)
        p = Probe(BASE, name="occ%d" % occ, moves=moves)
        try:
            res = p.search("depth 5")
        finally:
            p.close()
        if not record("threshold", "rook cycle x%d" % n, occ, occ >= 3, res):
            fails.append("threshold occ=%d" % occ)

    print()
    print("=" * 92)
    print("2) FIFTY-MOVE at the root: 99, 100, 101")
    print("=" * 92)
    for hm in (99, 100, 101):
        fen = "4k3/8/8/8/8/8/8/1R2K3 w - - %d 60" % hm
        p = Probe(fen, name="hm%d" % hm)
        try:
            res = p.search("depth 5")
        finally:
            p.close()
        if not record("fifty", "halfmove %d" % hm, 1, hm >= 100, res):
            fails.append("fifty hm=%d" % hm)

    print()
    print("=" * 92)
    print("3) FIFTY-MOVE RESET: pawn move / capture clears the clock")
    print("=" * 92)
    reset_fen = "4k3/8/8/8/8/8/P7/1R2K3 w - - 99 60"
    p = Probe(reset_fen, name="hm99-pawn")
    try:
        res = p.search("depth 5")
    finally:
        p.close()
    drew = res["score"] == ("cp", 0) and res["nodes"] <= 64
    score_text = "%s%d" % res["score"] if res["score"] else "-"
    print("%-44s score=%-9s nodes=%-6d drawn=%-5s (want False)" % (
        "hm=99 with a pawn move available", score_text, res["nodes"], drew))
    ROWS.append({"section": "fifty-reset", "fixture": "hm=99 pawn available",
                 "occurrences": 1, "engine_drawn_root": drew, "fide_draw": False,
                 "agree": not drew, "score": res["score"], "nodes": res["nodes"],
                 "bestmove": res["bestmove"], "note": "clock reset visible to search"})
    if drew:
        fails.append("hm=99 with a real alternative was called drawn at the root")

    print("%-44s halfmove=%d (want 0)" % ("pawn move a2a3 resets clock",
                                          halfmove_after("4k3/8/8/8/8/8/P7/1R2K3 w - - 99 60", ["a2a3"])))
    if halfmove_after("4k3/8/8/8/8/8/P7/1R2K3 w - - 99 60", ["a2a3"]) != 0:
        fails.append("pawn move did not reset the halfmove clock")

    quiet = halfmove_after("4k3/8/8/8/8/8/8/1R2K3 w - - 99 60", ["e1d1"])
    print("%-44s halfmove=%d (want 100)" % ("quiet king move increments clock", quiet))
    if quiet != 100:
        fails.append("quiet move did not increment the clock")

    cap = halfmove_after("1r2k3/8/8/8/8/8/8/1R2K3 w - - 99 60", ["b1b8"])
    print("%-44s halfmove=%d (want 0)" % ("capture b1b8 resets clock", cap))
    if cap != 0:
        fails.append("capture did not reset the halfmove clock")

    print()
    print("=" * 92)
    print("4) INTERACTION: threefold AND halfmove 100 simultaneously")
    print("=" * 92)
    fen100 = "4k3/8/8/8/8/8/8/1R2K3 w - - 100 60"
    p = Probe(fen100, name="threefold+hm100", moves=cycles(2))
    try:
        res = p.search("depth 5")
    finally:
        p.close()
    occ = oracle_occurrences(fen100, cycles(2))
    if not record("interaction", "threefold and hm=100", occ, True, res):
        fails.append("threefold+hm100")

    print()
    print("=" * 92)
    print("5) INTERACTION: hm=99 at root, clock-resetting move available, mate exists")
    print("=" * 92)
    # Ra1-a8 is mate (rook on the 8th, black Kh8 boxed by white Kg6).
    # a2a3 also exists and resets the clock.  FIDE: a mate that is legally
    # deliverable must still be found; the 50-move rule is a claim, not an
    # automatic draw, so the engine must not bail out at the root.
    mate_fen = "7k/8/6K1/8/8/8/P7/R7 w - - 99 60"
    p = Probe(mate_fen, name="hm99-mate")
    try:
        res = p.search("depth 6")
    finally:
        p.close()
    score_text = "%s%d" % res["score"] if res["score"] else "-"
    print("%-44s score=%-9s nodes=%-6d best=%s (mate a1a8)" % (
        "hm=99, mate in 1 + pawn reset available", score_text, res["nodes"], res["bestmove"]))
    # At hm=99 the exact mate distance is not the point: a2a4 resets the clock
    # and mate still follows, which is a win. The requirement is only that the
    # engine does not bail out of a won position.
    mate_found = res["score"] is not None and res["score"][0] == "mate"
    ROWS.append({"section": "interaction", "fixture": "hm=99 mate available",
                 "occurrences": 1, "engine_drawn_root": res["nodes"] <= 64,
                 "fide_draw": False, "agree": mate_found, "score": res["score"],
                 "nodes": res["nodes"], "bestmove": res["bestmove"],
                 "note": "must find a win, not bail"})
    if not mate_found:
        fails.append("winning position at hm=99 reported as %s" % (res["score"],))

    print()
    print("=" * 92)
    print("5b) hm=100 with mate in 1 -- the strict FIDE reading vs the engine")
    print("=" * 92)
    mate100 = "7k/8/6K1/8/8/8/8/R7 w - - 100 60"
    p = Probe(mate100, name="hm100-mate")
    try:
        res = p.search("depth 6")
    finally:
        p.close()
    score_text = "%s%d" % res["score"] if res["score"] else "-"
    print("%-44s score=%-9s nodes=%-6d best=%s" % (
        "hm=100 with mate a1a8 available", score_text, res["nodes"], res["bestmove"]))
    ROWS.append({"section": "interaction", "fixture": "hm=100 mate in 1",
                 "occurrences": 1, "engine_drawn_root": res["nodes"] <= 64,
                 "fide_draw": False, "agree": res["score"] == ("mate", 1),
                 "score": res["score"], "nodes": res["nodes"],
                 "bestmove": res["bestmove"], "note": "mate beats a 50-move claim"})
    if res["score"] != ("mate", 1):
        fails.append("mate a1a8 not reported at hm=100 (got %s)" % (res["score"],))

    return fails


if __name__ == "__main__":
    f = main()
    print()
    if f:
        print("FAILURES: %d" % len(f))
        for x in f:
            print("  -", x)
    else:
        print("no failures")
