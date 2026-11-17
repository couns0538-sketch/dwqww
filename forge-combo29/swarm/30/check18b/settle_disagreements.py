#!/usr/bin/env python3
"""settle_disagreements.py -- adjudicate ALL of the S14-vs-PC20 disagreements from check16, so the
question "is the 203 cp case typical or an outlier?" gets answered rather than guessed.

For each disagreeing position, for each of the two candidate moves, at depths 12/14/16/18, score the
move IN ISOLATION (root restricted with `searchmoves`) on both option sets. The isolated score is the
direct comparison: it removes the search's freedom to choose.

Then classify the position:
  * ONE MOVE CLEARLY BETTER — the better move leads by > 100 cp at every depth;
  * NEAR-TIE — the two moves are within 50 cp of each other at every depth;
  * MIXED — anything else (and such a position is reported as unresolved, not forced into a box).

Threads 1, Hash 64 (room for the deepest searches), OwnBook false, PC20 for the option set unless the
arm says otherwise, fresh process per row, every setoption confirmed by readyok.

usage: settle_disagreements.py OUTDIR
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "check17"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "sp", os.path.join(HERE, "..", "check17", "settle_pos29.py"))
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)

CASES = [
    ("13", "2bq4/r1pnpkbr/1p3p1p/p2P1P2/3p1Kp1/P1NP2PP/RPPBB2R/1N3Q2 b - - 5 25", "h6h5", "d4c3"),
    ("24", "r4bn1/pkp1q3/bp4pr/3p3p/1PPBP1P1/5N1B/P2P1P1P/R2QK1R1 b Q - 3 20", "h5g4", "e7e4"),
    ("29", "rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18", "f3g2", "f3g3"),
    ("35", "2b1qb1r/2p3pB/k2pp3/P1pP1p2/pnP4N/2N3BP/P4PP1/R2K2R1 w - - 4 26", "h7f5", "a2a3"),
]
DEPTHS = [12, 14, 16, 18]
ARMS = [("S14", sp.S14), ("PC20", sp.S14 + sp.PC20EXTRA)]   # TRUE PC20: S14 + the six extras (30-C57)


def score_in_isolation(fen, move, depth, settings):
    sp.FEN = fen
    return sp.search(settings, "go depth %d searchmoves %s" % (depth, move))


def cp_of(score):
    """-> (kind, value) where kind is 'cp' or 'mate'."""
    if not score:
        return (None, None)
    parts = score.split()
    if len(parts) < 2:
        return (None, None)
    try:
        return (parts[0], int(parts[1]))
    except ValueError:
        return (None, None)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    import hashlib
    import chess as _chess
    # FEN GATE (30-C58 lesson, second form): an invalid FEN is REFUSED by the engine, which leaves
    # the previous position and can report cp 0 -- indistinguishable from a real evaluation.
    for _lbl, _fen, _m1, _m2 in CASES:
        try:
            _b = _chess.Board(_fen)
        except ValueError as _e:
            raise SystemExit("REFUSING: position %s has an INVALID FEN: %s" % (_lbl, _e))
        if sum(1 for _ in _b.legal_moves) == 0:
            raise SystemExit("REFUSING: position %s has no legal moves" % _lbl)
        if _chess.Move.from_uci(_m1) not in _b.legal_moves or _chess.Move.from_uci(_m2) not in _b.legal_moves:
            raise SystemExit("REFUSING: position %s: a candidate move is illegal" % _lbl)
    report = {"cases": {}, "summary": {}, "provenance": {}}
    # PROVENANCE FIRST (30-C57 lesson): exe identity and the FULL ordered option lists, in the output.
    sha = hashlib.sha256(open(sp.EXE, "rb").read()).hexdigest()
    idname = [l for l in os.popen("printf 'uci\nisready\nquit\n' | %s" % sp.EXE).read().splitlines()
              if l.startswith("id name")]
    report["provenance"] = {"exe": os.path.realpath(sp.EXE), "sha256": sha,
                            "id_name": idname,
                            "S14_arm_options": ["Threads 1", "Hash 64"] + ["%s %s" % (n, v) for n, v in sp.S14],
                            "PC20_arm_options": ["Threads 1", "Hash 64"] + ["%s %s" % (n, v) for n, v in (sp.S14 + sp.PC20EXTRA)],
                            "arm_option_counts": {"S14": 2 + len(sp.S14), "PC20": 2 + len(sp.S14 + sp.PC20EXTRA)}}
    print("PROVENANCE: exe sha256 %s | %s" % (sha, idname))
    print("S14 arm: %d options; PC20 arm: %d options (MUST be 16 and 22 incl. Threads+Hash)"
          % (2 + len(sp.S14), 2 + len(sp.S14 + sp.PC20EXTRA)))
    assert 2 + len(sp.S14 + sp.PC20EXTRA) == 22, "PC20 arm is not the true 20-option arm"
    verdicts = {}
    for label, fen, m1, m2 in CASES:
        row = {"fen": fen, "moves": [m1, m2], "isolated": {}}
        print("\n=== position %s  (%s vs %s) ===" % (label, m1, m2))
        print("%-14s %-7s %-8s %-11s %-11s %s" % ("arm/depth", "", m1, m2, "gap m1-m2", "leader"))
        gaps = []
        for depth in DEPTHS:
            for aname, st in ARMS:
                a = score_in_isolation(fen, m1, depth, st)
                b = score_in_isolation(fen, m2, depth, st)
                ka, va = cp_of(a["score"])
                kb, vb = cp_of(b["score"])
                if ka != "cp" or kb != "cp":
                    gap = None
                    leader = "MATE SCORE - not comparable arithmetically"
                else:
                    gap = va - vb
                    gaps.append(gap)
                    leader = m1 if gap > 0 else (m2 if gap < 0 else "equal")
                row["isolated"]["%s/d%d" % (aname, depth)] = {
                    "m1": a, "m2": b, "gap": gap, "leader": leader}
                print("%-14s %-7s %-8s %-11s %-11s %s" % (
                    aname, depth, "%s %s" % (ka, va), "%s %s" % (kb, vb), gap, leader))
        # classify
        if gaps:
            all_pos = all(g > 0 for g in gaps)
            all_neg = all(g < 0 for g in gaps)
            min_abs = min(abs(g) for g in gaps)
            max_abs = max(abs(g) for g in gaps)
            if (all_pos or all_neg) and min_abs > 100:
                cls = "ONE MOVE CLEARLY BETTER (%s)" % (m1 if all_pos else m2)
            elif max_abs <= 50:
                cls = "NEAR-TIE (max gap %d cp)" % max_abs
            else:
                cls = "MIXED (gap range %d..%d cp) - UNRESOLVED" % (min_abs, max_abs)
        else:
            cls = "CONTAINS MATE SCORES - UNRESOLVED by cp comparison"
        row["classification"] = cls
        verdicts[label] = cls
        report["cases"][label] = row
        print("  --> %s" % cls)
    report["summary"] = verdicts
    with open(os.path.join(outdir, "settle_disagreements.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("\nSUMMARY")
    for k, v in verdicts.items():
        print("  position %-3s %s" % (k, v))


if __name__ == "__main__":
    main()
