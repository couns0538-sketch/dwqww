#!/usr/bin/env python3
"""doors_side_by_side.py — one table: per door, base tree vs PC r15, with node counts.

Builds differ in which options exist (the PC build has CuckooRep/HistRework/TtPruneV2/CorrHistV2/
MateAlphaGuard; the base tree does not), so each build is given its own settings:

  base  : Threads 1, Hash 16, OwnBook false (the four honesty-pin style; S14 also sent, harmless)
  PC r15: PC20 = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
          MateAlphaGuard true, OwnBook false, Threads 1

Every search is a fresh-ish process state via `ucinewgame` + `isready`, and an option the build rejects
stops the run loudly rather than being skipped.

Print one Markdown table: door | base bestmove | base score | base nodes | PC20 bestmove | PC20 score |
PC20 nodes | verdict.

Usage: doors_side_by_side.py BASE_EXE PC_EXE OUTDIR
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
MATE = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - {hm} 1"
SHUF = "a1b1 g8f8 b1a1 f8g8"

# door, position command, board FEN (for the mate judgement), what "fixed" means
CASES = [
    ("door A1: mate in 1, halfmove 100", "position fen " + MATE.format(hm=100), MATE.format(hm=100),
     "must find the mate"),
    ("door A2: mate in 1, halfmove 150", "position fen " + MATE.format(hm=150), MATE.format(hm=150),
     "must find the mate"),
    ("door A3: counter-resetting pawn mate, halfmove 100",
     "position fen 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1", "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1",
     "must find mate 2"),
    ("door B1: mate in 1 on the third repetition",
     "position fen " + MATE.format(hm=0) + " moves " + SHUF + " " + SHUF, MATE.format(hm=0),
     "must find the mate"),
    ("control C1: mate in 1, halfmove 99 (always worked)",
     "position fen " + MATE.format(hm=99), MATE.format(hm=99), "must find the mate"),
    ("control C2: K v K (genuine automatic draw)",
     "position fen 7k/8/8/8/8/8/8/K7 w - - 0 1", "7k/8/8/8/8/8/8/K7 w - - 0 1",
     "may answer at once, 0 nodes is correct"),
    ("control C3: KQ v K at halfmove 150 (claimable draw)",
     "position fen 8/5K2/7Q/4k3/8/8/8/8 w - - 150 1", "8/5K2/7Q/4k3/8/8/8/8 w - - 150 1",
     "score must stay cp 0"),
]


def probe(exe, pos, pc20, depth=12):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items())
    if pc20:
        sent += PC20_EXTRA
    else:
        sent += [("OwnBook", "false")]
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP on {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(pos)
    eng.send("isready")
    _l, ok = eng.read_until("readyok", 20)
    if not ok:
        eng.close()
        return {"best": "NOREOK", "score": "", "nodes": "", "depth": 0}
    eng.send(f"go depth {depth}")
    out, ok = eng.read_until("bestmove", 300)
    eng.close()
    best, score, nodes, d = "", "", "", 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            d = max(d, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = f[f.index("nodes") + 1]
            if "score" in f:
                score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
    return {"best": best, "score": score, "nodes": nodes, "depth": d}


def main() -> int:
    base, pc, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("| door | base: bestmove | base: score | base: nodes | PC20: bestmove | PC20: score | "
          "PC20: nodes | requirement | verdict |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, pos, fen, requires in CASES:
        b = probe(base, pos, pc20=False)
        p = probe(pc, pos, pc20=True)
        # Judge only whether the required outcome is met on each build.
        def found_mate(r):
            try:
                board = chess.Board(fen)
                mv = chess.Move.from_uci(r["best"])
                if mv not in board.legal_moves:
                    return "illegal"
                board.push(mv)
                return "mate" if board.is_checkmate() else "no"
            except ValueError:
                return "n/a"

        # A mate in 2 is NOT an immediately mating move, so "found the mate" must be judged by the
        # reported SCORE for that case, not by whether the played move is itself checkmate.
        mate2 = requires.startswith("must find mate 2")

        def delivered(r):
            if mate2:
                return r["score"] == "mate 2"
            return found_mate(r) == "mate"

        bm, pm = delivered(b), delivered(p)
        if requires.startswith("must find"):
            verdict = ("PC20 FIXED" if (not bm and pm)
                       else ("both OK" if bm and pm else "**PC20 STILL BROKEN**"))
        else:
            ok = True
            verdict = "unchanged" if b["score"] == p["score"] else "**CHANGED**"
        print(f"| {name} | {b['best']} | {b['score']} | {b['nodes']} | {p['best']} | {p['score']} | "
              f"{p['nodes']} | {requires} | {verdict} |")
        rows.append((name, b, p, requires, verdict))
    with open(os.path.join(outdir, "doors_side_by_side.tsv"), "w") as fh:
        fh.write("door\tbase_best\tbase_score\tbase_nodes\tpc20_best\tpc20_score\tpc20_nodes\t"
                 "requirement\tverdict\n")
        for name, b, p, requires, verdict in rows:
            fh.write(f"{name}\t{b['best']}\t{b['score']}\t{b['nodes']}\t{p['best']}\t{p['score']}\t"
                     f"{p['nodes']}\t{requires}\t{verdict}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
