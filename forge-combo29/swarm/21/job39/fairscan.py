#!/usr/bin/env python3
"""fairscan.py EXE OUTDIR [NPOS]

The FAIR test of the position-155 class, which my job39 scan was not.

Why job39's scan was unfair: its lone-king endings started at halfmove counter 0, so the
fifty-move draw was 100 half-moves away and every move lost anyway. A hit (a move whose RESULT is
worse than an available alternative) is impossible when every move loses, so a 0 count from that
design proves nothing.

This design makes a draw actually AVAILABLE:
  - a bare king against a SINGLE minor (K vs K+N, K vs K+B) — drawn by insufficient material only
    if the minor can be captured; otherwise the strong side often cannot mate, so survival is a
    draw;
  - OR a bare king against R or Q with a HIGH starting halfmove counter (90-99), so the bare king
    needs only 1-10 half-moves of survival to reach the fifty-move draw — the exact window where a
    wrong move can throw the draw away.

For every position: every legal root move is played out engine-vs-engine (go nodes 20000, Threads 1,
PC20) and classified with the fifty-move counter honoured; the engine's own `go depth 16` and
`go nodes 20000` answers are compared against the best available RESULT.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
SEED = 2101
RANK = {"loss": 0, "draw": 1, "win": 2}


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    return e


def classify(b, mover):
    """win/draw/loss for `mover`, honouring the fifty-move counter and material."""
    if b.is_checkmate():
        return "win" if b.turn != mover else "loss"
    if b.is_stalemate() or b.is_insufficient_material():
        return "draw"
    if b.halfmove_clock >= 100 or b.can_claim_fifty_moves() or b.can_claim_threefold_repetition():
        return "draw"
    return None


def playout(e, board, mover, cap=400):
    b = board.copy()
    e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
    n = 0
    while n < cap:
        r = classify(b, mover)
        if r is not None:
            return r, n
        e.position("position fen " + b.fen())
        try:
            lines = e.go("go nodes 20000", timeout=180)
        except Exception:
            return "UNKNOWN", n
        bm = bestmove_of(lines)
        if not bm or bm == "0000":
            return classify(b, mover) or "draw", n
        try:
            b.push_uci(bm)
        except Exception:
            return "UNKNOWN", n
        n += 1
    return "CAPPED", n


def make_positions(n):
    rng = random.Random(SEED)
    out = []
    while len(out) < n:
        b = chess.Board(None)
        sq = list(chess.SQUARES)
        wk, bk = rng.sample(sq, 2)
        if chess.square_distance(wk, bk) < 3:
            continue
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        rest = [s for s in sq if s not in (wk, bk)]
        weak_is_white = rng.random() < 0.5
        strong = chess.BLACK if weak_is_white else chess.WHITE
        kind = rng.choice(["minor", "rook_high", "queen_high"])
        if kind == "minor":
            piece = rng.choice([chess.KNIGHT, chess.BISHOP])
            hm = rng.randrange(0, 20)
        elif kind == "rook_high":
            piece = chess.ROOK
            hm = rng.randrange(90, 100)
        else:
            piece = chess.QUEEN
            hm = rng.randrange(90, 100)
        s = rng.choice(rest)
        b.set_piece_at(s, chess.Piece(piece, strong))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        if b.is_check() or b.is_checkmate() or b.is_stalemate():
            continue
        if b.legal_moves.count() == 0:
            continue
        out.append((b.fen().rsplit(" ", 2)[0] + " %d %d" % (hm, 60), kind))
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    os.makedirs(outdir, exist_ok=True)
    e = eng(exe, os.path.join(outdir, "fair_raw.txt"))
    positions = make_positions(npos)
    R = {}
    hits = []
    for i, (fen, kind) in enumerate(positions):
        b = chess.Board(fen)
        mover = b.turn
        results = {}
        for m in list(b.legal_moves):
            c = b.copy(); c.push(m)
            res, plies = playout(e, c, mover)
            results[m.uci()] = dict(result=res, plies=plies)
        # engine's own answers
        chosen = {}
        for name, go in (("depth16", "go depth 16"), ("nodes20k", "go nodes 20000")):
            e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
            e.position("position fen " + fen)
            chosen[name] = bestmove_of(e.go(go, timeout=200))
        rs = [RANK.get(v["result"], -1) for v in results.values()]
        best = max(rs) if rs else -1
        hit_names = [k for k, bm in chosen.items()
                     if RANK.get(results.get(bm, {}).get("result"), -1) < best]
        R["%d" % i] = dict(fen=fen, kind=kind, moves=results, chosen=chosen,
                           best={0: "loss", 1: "draw", 2: "win"}.get(best, "?"),
                           hits=hit_names)
        if hit_names:
            hits.append(i)
        if (i + 1) % 10 == 0:
            print("scanned %d/%d hits %d" % (i + 1, len(positions), len(hits)))
    e.close()
    rows = ["| pos | kind | FEN | chosen d16 | chosen 20k | results | best | hit |",
            "|---|---|---|---|---|---|---|---|"]
    for i, (fen, kind) in enumerate(positions):
        r = R["%d" % i]
        dist = {}
        for v in r["moves"].values():
            dist[v["result"]] = dist.get(v["result"], 0) + 1
        rows.append("| %d | %s | `%s` | %s | %s | %s | %s | %s |" % (
            i, kind, fen, r["chosen"]["depth16"], r["chosen"]["nodes20k"], dist,
            r["best"], "YES" if r["hits"] else "no"))
    text = "\n".join(rows)
    text += "\n\nHITS: %d of %d\n" % (len(hits), len(positions))
    for i in hits:
        r = R["%d" % i]
        text += "  hit %d (%s): `%s` chosen %s; best available %s\n" % (
            i, r["kind"], r["fen"], r["chosen"], r["best"])
    text += "\nby kind: %s\n" % {
        k: sum(1 for i in R if R[i]["kind"] == k) for k in ("minor", "rook_high", "queen_high")}
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-800:])


if __name__ == "__main__":
    main()