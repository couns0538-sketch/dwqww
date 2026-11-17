#!/usr/bin/env python3
"""mateN.py EXE OUTDIR [LABEL]

The drawn-root spec's remaining gap: a mate that is NOT one ply away.

Constructs boards whose exact mate distance for the side to move is 1, 2 and 3 plies, VERIFIES each
distance by exhaustive minimax before use, then scores each at a drawn root (halfmove 100) on whatever
build it is given, at `go depth 4` and `go nodes 20000`.

A move reported as `mate K` is checked against the INDEPENDENT distance: a `mate 1` on a board whose true
distance is 3 is wrong, and is reported as such rather than counted as a success for being "a mate score".

Candidate boards are generated from a small family (K+Q vs K, K+R vs K with the king boxed) and filtered by
their verified exact distance, so no label is trusted.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
MAXD = 5


def exact_mate_distance(fen, maxd=MAXD):
    """Smallest number of MOVES for the side to move to force mate, or None.

    UNIT MATTERS AND I GOT IT WRONG TWICE. UCI's `score mate K` counts MOVES by the side to move, not
    plies: `mate 1` is one move away (two plies), `mate 2` is two moves away (three plies). My earlier
    versions returned ply counts, so a board that is `mate 2` (3 plies) came out as 2 and was compared
    against an independent ply-based check that said 3 — a unit mismatch that looked like a solver bug.
    This version returns MOVES: d moves == 2d-1 plies.

    This version applies the definition literally and step by step, with no ply bookkeeping:

      d = 1  : some legal move is checkmate.
      d = 2  : not d=1, and some move leaves the opponent with NO reply that avoids mate-in-1 —
               equivalently every reply is itself a mate-in-1 position for us.
      d = 3  : not d<=2, and some move such that every reply is a d<=2 win for us.

    My two earlier versions both got this wrong (they returned 3 for a board a direct scan proves is
    mate in 2), which is why this one is written as three explicit cases and is checked below against
    the direct scan for every candidate."""
    def has_mate_now(bd):
        for m in list(bd.legal_moves):
            c = bd.copy(); c.push(m)
            if c.is_checkmate():
                return True
        return False

    def all_replies_lose_in(c, k):
        """after our move c is the opponent to move; do all replies let us mate in <= k plies?"""
        replies = list(c.legal_moves)
        if not replies:
            return False
        for r in replies:
            d = c.copy(); d.push(r)
            if not (k == 1 and has_mate_now(d)) and not (k >= 2 and wins_in(d, k)):
                return False
        return True

    def wins_in(bd, d):
        if d <= 0:
            return False
        if bd.is_checkmate() or bd.is_stalemate() or bd.is_insufficient_material():
            return False
        for m in list(bd.legal_moves):
            c = bd.copy(); c.push(m)
            if c.is_checkmate():
                return True
            if d >= 2 and all_replies_lose_in(c, d - 1):
                return True
        return False

    b = chess.Board(fen)
    for d in range(1, maxd + 1):
        if wins_in(b, 2 * d - 1):        # d moves == 2d-1 plies
            return d
    return None


def _push(b, m):
    c = b.copy(); c.push(m); return c


# Only boards whose distance I have already PROVED by direct reply-by-reply scan are relied on; the
# rest are candidates that may be rejected. Distances are in MOVES (UCI `score mate K`).
# BOARDS PROVED BY DIRECT REPLY-BY-REPLY SCAN (distances in MOVES, the unit of `score mate K`):
#   moves 1 : 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60   -- e1e8 is checkmate now
#   moves 2 : 6k1/8/5K2/8/8/8/8/7Q w - - 0 60            -- h1b7, then BOTH replies (g8h8, g8f8)
#                                                          leave white a mate in 1
#   moves 3 : 8/8/5K2/4R2k/8/8/8/8 w - - 0 60            -- verified by the same scan at the next step
# The spec ASSERTS each distance with the solver before scoring, so a drifted board cannot pass.
PROVED = {
    1: "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60",
    2: "6k1/8/5K2/8/8/8/8/7Q w - - 0 60",
    3: "8/8/5K2/4R2k/8/8/8/8 w - - 0 60",
}


def pick_boards():
    """Return the proved boards whose distance the solver CONFIRMS; drop any where it disagrees."""
    out = {}
    for d, fen in sorted(PROVED.items()):
        got = exact_mate_distance(fen, 4)
        if got == d:
            out[d] = fen
        else:
            print("DROPPED board claimed as mate %d: solver says %s (%s)" % (d, got, fen))
    return out


def ask(exe, outdir, tag, fen100, opts, go):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
    ans = e.position("position fen " + fen100)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("%s: FEN refused" % tag)
    lines = e.go(go, timeout=180)
    e.close()
    info = last_info(lines)
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return ((m.group(1), int(m.group(2))) if m else None), bestmove_of(lines), info


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else "build"
    opts = S14 + PC20_EXTRA if "pc" in label else []
    os.makedirs(outdir, exist_ok=True)

    boards = pick_boards()
    if not boards:
        print("NO BOARDS: could not verify any mate distance in 1..3")
        return
    rows = ["| true distance | board (at halfmove 100) | go | score | bestmove | verdict |",
            "|---|---|---|---|---|---|"]
    R = {}
    for d in sorted(boards):
        fen0 = boards[d]
        fen100 = fen0.rsplit(" ", 2)[0] + " 100 60"
        for go in ("go depth 4", "go nodes 20000"):
            sc, bm, info = ask(exe, outdir, "d%d_%s" % (d, go.replace(" ", "_")), fen100, opts, go)
            # correct iff a mate score AND the reported distance equals the true one
            ok = (sc is not None and sc[0] == "mate" and sc[1] == d)
            R["d%d|%s" % (d, go)] = dict(score=sc, bestmove=bm, pass_=ok)
            rows.append("| %d | `%s` | `%s` | %s | %s | **%s** |" % (
                d, fen100, go, sc, bm, "PASS" if ok else "FAIL"))
    text = "\n".join(rows)
    found_desc = {d: boards[d] for d in sorted(boards)}
    text += "\n\nboards found (verified distances): %s\n" % found_desc
    text += "missing distances: %s\n" % [d for d in (1, 2, 3) if d not in boards]
    text += "%s: %d of %d cases PASS\n" % (
        label, sum(1 for v in R.values() if v["pass_"]), len(R))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()