#!/usr/bin/env python3
"""Does the built-in book's play agree with the engine's own judgement?

This follows S-F15 (the book answers game searches with no search at all, for the first ~16 plies).
The owner's match uses the book, so the natural question is: are the book's moves good ones *by this
engine's own evaluation*? If the book plays a move the engine would never choose and scores it much
worse than its own preference, then a book-on match is partly measuring a third party's opening file
rather than the engine.

Method, for each position reached by walking the book:
  A. ask the engine with OwnBook TRUE on a game search (clock) -> the book move
  B. ask the engine with OwnBook FALSE on the SAME clock search -> its own preferred move and score
  C. ask with OwnBook FALSE at a FIXED depth (12) for both the book move and the engine's move,
     so the comparison is at equal depth and not confounded by the book position being searched
     longer or shorter.
Then classify:
  agrees      : book move == engine move
  disagrees   : different move; report the score difference at equal depth
A score difference of 0 means the two moves are equivalent to the engine; a large negative difference
means the book played a move the engine thinks is worse.

Book-on searches emit no `info depth` lines, so the book move is taken from `info string book move`.

Usage: book_quality.py EXE OUTDIR [MAXPLIES] [DEPTH]
"""
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
MAXPLIES = int(sys.argv[3]) if len(sys.argv) > 3 else 22
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 12
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6BASE = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
           ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
BASE = [("Threads", "1"), ("Hash", "16")]
BAD = ("unknown option", "invalid value", "error")


def search(fen, own_book, go_cmd):
    """One search. Returns dict with bestmove, book_move (if any), score at the last info line."""
    opts = BASE + S14 + PC6BASE + [("OwnBook", "true" if own_book else "false")]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in opts:
        if not any(o.startswith("option name %s " % n) for o in seen):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok")
    send(go_cmd)

    book_move = None
    last = None
    bm = None
    info_lines = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if "book move" in l:
            m = re.search(r"book move (\S+)", l)
            if m:
                book_move = m.group(1)
        if l.startswith("info depth"):
            last = l
            info_lines += 1
        if l.startswith("bestmove"):
            bm = l
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()

    def g(pat):
        m = re.search(pat, last) if last else None
        return int(m.group(1)) if m else None

    return {
        "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
        "book_move": book_move,
        "cp": g(r"\bscore cp (-?\d+)"),
        "mate": g(r"\bscore mate (-?\d+)"),
        "depth": g(r"\bdepth (\d+)"),
        "nodes": g(r"\bnodes (\d+)"),
        "info_lines": info_lines,
    }


def score_move_at_depth(fen, move, depth):
    """Score a SPECIFIC move by playing it then searching the reply at `depth` from the opponent's
    side, and negating. Equal-depth comparison of two candidate moves, without searchmoves options."""
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(move)
    except ValueError:
        return None
    if m not in b.legal_moves:
        return None
    b.push(m)
    r = search(b.fen(), False, "go depth %d" % depth)
    if r["mate"] is not None:
        return ("mate", -r["mate"])
    if r["cp"] is None:
        return None
    return ("cp", -r["cp"])


rows = []
board = chess.Board()
for ply in range(MAXPLIES):
    if not board.legal_moves:
        break
    fen = board.fen()
    withb = search(fen, True, "go movetime 100")
    without = search(fen, False, "go movetime 100")
    row = {"ply": ply, "fen": fen,
           "book_on_move": withb["bestmove"], "book_reported": withb["book_move"],
           "book_on_info_lines": withb["info_lines"],
           "engine_move": without["bestmove"], "engine_cp": without["cp"],
           "engine_mate": without["mate"], "engine_depth": without["depth"]}
    # was the book actually used? (reported book move present)
    used = withb["book_move"] is not None
    row["book_used"] = used
    if used:
        row["agrees"] = (withb["bestmove"] == without["bestmove"])
        a = score_move_at_depth(fen, withb["bestmove"], DEPTH)
        c = score_move_at_depth(fen, without["bestmove"], DEPTH)
        row["book_move_score"] = a
        row["engine_move_score"] = c
        if a and c and a[0] == "cp" and c[0] == "cp":
            row["score_gap_cp"] = a[1] - c[1]     # negative = book move worse
        else:
            row["score_gap_cp"] = None
    rows.append(row)
    mv = without["bestmove"]
    try:
        board.push(chess.Move.from_uci(withb["bestmove"]))
    except Exception:
        break
    print("ply %-2d book=%-5s engine=%-5s agrees=%-5s gap=%s"
          % (ply, withb["bestmove"], without["bestmove"], row.get("agrees"),
             row.get("score_gap_cp")), flush=True)

used_rows = [r for r in rows if r["book_used"]]
gaps = [r["score_gap_cp"] for r in used_rows if r["score_gap_cp"] is not None]
summary = {
    "exe": os.path.abspath(EXE),
    "plies_walked": len(rows),
    "plies_from_book": len(used_rows),
    "book_move_equals_engine_move": sum(1 for r in used_rows if r.get("agrees")),
    "book_move_disagrees": sum(1 for r in used_rows if r.get("agrees") is False),
    "comparisons_at_equal_depth": len(gaps),
    "gap_cp_median": (sorted(gaps)[len(gaps) // 2] if gaps else None),
    "gap_cp_min": min(gaps) if gaps else None,
    "gap_cp_max": max(gaps) if gaps else None,
    "book_moves_scored_worse_by_50cp_or_more": sum(1 for g in gaps if g <= -50),
    "depth_for_comparison": DEPTH,
    "note": "gap = book move score minus engine move score at equal depth; negative means the book "
            "played a move the engine rates worse.",
}
json.dump({"summary": summary, "rows": rows},
          open(os.path.join(OUTDIR, "book_quality.json"), "w"), indent=1)
print()
for k, v in summary.items():
    print("%-42s %s" % (k, v))
