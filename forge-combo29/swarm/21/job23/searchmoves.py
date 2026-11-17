#!/usr/bin/env python3
"""searchmoves.py OUTDIR

`searchmoves` and drawn-root interaction on both builds, Threads 1.

Cases (fresh process each, read to bestmove, FEN acceptance asserted):
  1 illegal name only          go searchmoves e2e5 depth 2
  2 one legal name             go searchmoves e2e4 depth 2
  3 two legal names            go searchmoves d2d4 e2e4 depth 4
  4 legal name at hm 100       position <mate-in-1 board at hm 100>, go searchmoves e1e8 depth 4
  5 no names at all            go searchmoves depth 2
  6 names + a real depth       go searchmoves g1f3 depth 4

Case 4 is the new question: the PC build searches drawn roots (FORGE_FIX_ROOT_DRAWN), so a
restricted search there should search too. On the base build it is the 0-node adjudication.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
HM100 = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"

CASES = [
    ("1_illegal_name", START, "go searchmoves e2e5 depth 2"),
    ("2_one_legal", START, "go searchmoves e2e4 depth 2"),
    ("3_two_legal", START, "go searchmoves d2d4 e2e4 depth 4"),
    ("4_legal_at_hm100", HM100, "go searchmoves e1e8 depth 4"),
    ("5_no_names", START, "go searchmoves depth 2"),
    ("6_legal_knight", START, "go searchmoves g1f3 depth 4"),
]


def nodes_of(lines):
    for l in reversed(lines):
        m = re.search(r" nodes (\d+)", l)
        if m:
            return int(m.group(1))
    vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
    return vals[0] if vals else None


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("pc", os.path.expanduser("~/b/pc_asan/forge")),
              ("base", os.path.expanduser("~/b/asan/forge"))]
    R = {}
    rows = ["| build | case | go line | bestmove | nodes | answer lines |",
            "|---|---|---|---|---|---|"]
    for bname, exe in builds:
        for tag, fen, go in CASES:
            e = SafeEngine(exe, os.path.join(outdir, "%s_%s_raw.txt" % (bname, tag)),
                           hash_mb=16, threads=1)
            ans = e.position("position fen " + fen)
            if any("invalid FEN" in l for l in ans):
                e.close()
                raise AssertionError("%s/%s FEN refused" % (bname, tag))
            lines = e.go(go, timeout=60)
            e.close()
            bm = bestmove_of(lines)
            if bm == "":
                raise AssertionError("%s/%s: no bestmove" % (bname, tag))
            info = last_info(lines) or next(
                (l for l in reversed(lines) if l.startswith("info")), "")
            answers = " | ".join(l for l in lines if l.startswith("info string")) or "-"
            legal = {m.uci() for m in chess.Board(fen).legal_moves}
            R["%s|%s" % (bname, tag)] = dict(bestmove=bm, nodes=nodes_of(lines),
                                             info=info, answers=answers,
                                             legal=bm in legal)
            rows.append("| %s | %s | `%s` | %s | %s | %s |" % (
                bname, tag, go, bm, nodes_of(lines), answers[:70]))
    text = "\n".join(rows)

    # the questions that decide the outcome
    def g(b, t):
        return R["%s|%s" % (b, t)]
    q = {
        "P1 PC illegal name still says no-legal-root and answers 0000":
            "no legal root moves" in g("pc", "1_illegal_name")["answers"],
        "P2 PC one legal name returns exactly e2e4":
            g("pc", "2_one_legal")["bestmove"] == "e2e4",
        "P3 PC two legal names returns one of them":
            g("pc", "3_two_legal")["bestmove"] in ("d2d4", "e2e4"),
        "P4 PC restricted search at hm100 actually SEARCHES (nodes > 0)":
            (g("pc", "4_legal_at_hm100")["nodes"] or 0) > 0,
        "P5 base build reproduces seats 02/24 on the illegal-name case":
            "no legal root moves" in g("base", "1_illegal_name")["answers"],
        "base build at hm100 is 0-node adjudication":
            g("base", "4_legal_at_hm100")["nodes"] == 0,
    }
    text += "\n\n| question | outcome |\n|---|---|\n"
    for k, v in q.items():
        text += "| %s | %s |\n" % (k, "yes" if v else "NO")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()