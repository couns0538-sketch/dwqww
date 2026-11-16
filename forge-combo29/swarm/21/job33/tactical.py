#!/usr/bin/env python3
"""tactical.py OUTDIR

Does the node undershoot (21-F16) change the MOVE on tactical positions?

Set construction (myself, with python-chess, no labels trusted):
  from set G, keep positions where the side to move has a capture that wins at least a minor
  piece after the opponent's best recapture (a 1-ply greedy SEE: play the capture, let the
  opponent recapture greedily, compare material). Keep the first 12.

For each: `go nodes 20000` and `go nodes 400000` on the PC build under PC20, Threads 1; record
depth, nodes, bestmove, score. Where the bestmoves differ, score BOTH moves with a fixed reference
search at `go nodes 200000` from the position reached after that move, and compare from the mover's
point of view.
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
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def material(b):
    s = 0
    for sq, p in b.piece_map().items():
        v = VAL.get(p.piece_type, 0)
        s += v if p.color == chess.WHITE else -v
    return s


def winning_capture(b):
    """True if a capture wins at least a minor piece against a greedy recapture."""
    me = b.turn
    base = material(b) * (1 if me == chess.WHITE else -1)
    best = 0
    for m in list(b.legal_moves):
        if not b.is_capture(m):
            continue
        c = b.copy()
        c.push(m)
        # opponent's greedy recapture
        best_recap = None
        for r in list(c.legal_moves):
            if c.is_capture(r):
                captured = c.piece_at(r.to_square)
                gain = VAL.get(captured.piece_type, 0) if captured else 0
                if best_recap is None or gain > best_recap[0]:
                    best_recap = (gain, r)
        if best_recap:
            c.push(best_recap[1])
        after = material(c) * (1 if me == chess.WHITE else -1)
        best = max(best, after - base)
    return best >= 3


def engine(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    return e


def search(exe, outdir, tag, pos, go):
    e = engine(exe, os.path.join(outdir, tag + "_raw.txt"))
    e.position(pos)
    lines = e.go(go, timeout=600)
    e.close()
    info = last_info(lines)
    d = re.search(r"info depth (\d+)", info)
    n = re.search(r" nodes (\d+)", info)
    sc = re.search(r"score (cp|mate) (-?\d+)", info)
    return dict(depth=int(d.group(1)) if d else None,
                nodes=int(n.group(1)) if n else None,
                bestmove=bestmove_of(lines),
                score=(sc.group(1), int(sc.group(2))) if sc else None)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    gf = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()]
    picked = []
    for fen in gf:
        try:
            b = chess.Board(fen)
        except Exception:
            continue
        if winning_capture(b):
            picked.append(fen)
        if len(picked) >= 12:
            break
    with open(os.path.join(outdir, "tactical.fens"), "w") as fh:
        fh.write("\n".join(picked) + "\n")
    exe = os.path.expanduser("~/b/pc_asan/forge")
    R = {}
    rows = ["| pos | d@20k | nodes@20k | move@20k | d@400k | nodes@400k | move@400k | moved? |",
            "|---|---|---|---|---|---|---|---|"]
    diffs = []
    for pi, fen in enumerate(picked):
        a = search(exe, outdir, "p%d_n20k" % pi, "position fen " + fen, "go nodes 20000")
        b_ = search(exe, outdir, "p%d_n400k" % pi, "position fen " + fen, "go nodes 400000")
        moved = a["bestmove"] != b_["bestmove"]
        R["%d" % pi] = dict(fen=fen, small=a, large=b_, moved=moved)
        if moved:
            diffs.append(pi)
        rows.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
            pi, a["depth"], a["nodes"], a["bestmove"], b_["depth"], b_["nodes"],
            b_["bestmove"], moved))

    # score both moves with a fixed reference search from the resulting positions
    ref_rows = ["| pos | small move | eval after | large move | eval after | delta (large - small) |",
                "|---|---|---|---|---|---|"]
    deltas = []
    for pi in diffs:
        fen = R["%d" % pi]["fen"]
        b = chess.Board(fen)
        out = {}
        for which in ("small", "large"):
            mv = R["%d" % pi][which]["bestmove"]
            c = b.copy()
            try:
                c.push_uci(mv)
            except Exception:
                out[which] = None
                continue
            # reference search from the OPPONENT's side; negate to the mover's view
            r = search(exe, outdir, "p%d_ref_%s" % (pi, which),
                       "position fen " + c.fen(), "go nodes 200000")
            if r["score"] and r["score"][0] == "cp":
                out[which] = -r["score"][1]
            elif r["score"] and r["score"][0] == "mate":
                out[which] = -10000 if r["score"][1] > 0 else 10000
            else:
                out[which] = None
        d = None
        if out.get("small") is not None and out.get("large") is not None:
            d = out["large"] - out["small"]
            deltas.append(d)
        ref_rows.append("| %d | %s | %s | %s | %s | %s |" % (
            pi, R["%d" % pi]["small"]["bestmove"], out.get("small"),
            R["%d" % pi]["large"]["bestmove"], out.get("large"), d))

    text = "\n".join(rows) + "\n\n" + "\n".join(ref_rows)
    text += "\n\npositions where the move changed: %d of %d\n" % (len(diffs), len(picked))
    text += "mean delta (large - small) on the changed positions: %s\n" % (
        round(sum(deltas) / len(deltas), 1) if deltas else "n/a")
    text += "all runs deterministic: yes (each pair run once; determinism established in 21-F15/F17)\n"
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1500:])


if __name__ == "__main__":
    main()