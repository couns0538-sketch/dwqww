"""Validate the BASELINE used by job3 before trusting its verdict.

job3 compares the ordering from pinned single-move searches against the ordering
from a MultiPV 5 search.  That is only a baseline if MultiPV's rank 1 is the
engine's ordinary answer.  Source: the MultiPV secondary lines are produced by a
separate `alt_worker` (src/search.cpp:2384) with its own hash, so rank 1 is the
only line guaranteed to come from the main search.

This script measures, at the same depth on the same positions:
  * agree_move  : MultiPV rank-1 move == plain `go depth 12` bestmove
  * agree_score : MultiPV rank-1 score == plain score
  * monotone    : MultiPV scores non-increasing with rank (a ranking must be)
A low agree_move makes MultiPV an unusable baseline and job3 must be re-run
against something else; that would be reported, not papered over.

Run: python3 job3/baseline_check.py [--limit N]
Writes job3/baseline_check.txt
"""
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402
from rank_order import multipv_scores  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    lines, mv_ok, sc_ok, mono_ok, n = [], 0, 0, 0, 0
    for idx, fen in enumerate(fens):
        plain = engine.run_session(f"position fen {fen}", f"go depth {DEPTH}")
        order, scores, _ = multipv_scores(fen, DEPTH, 5)
        if not order or plain.fatal:
            lines.append(f"SKIP {idx} fatal={plain.fatal}")
            continue
        n += 1
        first = order[0]
        a_mv = int(first == plain.bestmove)
        a_sc = int(scores[first] == plain.signed_score)
        vals = [scores[m] for m in order]
        mono = int(all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)))
        mv_ok += a_mv
        sc_ok += a_sc
        mono_ok += mono
        lines.append(f"[{idx:2d}] plain {plain.bestmove} {plain.signed_score} | "
                     f"multipv1 {first} {scores[first]} | move_same {a_mv} score_same {a_sc} "
                     f"monotone {mono} | all {vals}")

    lines += ["", "== BASELINE CHECK (MultiPV 5 vs plain search, depth 12) ==",
              f"positions compared: {n}",
              f"MultiPV rank-1 move == plain bestmove : {mv_ok}/{n}",
              f"MultiPV rank-1 score == plain score  : {sc_ok}/{n}",
              f"MultiPV scores non-increasing         : {mono_ok}/{n}"]
    text = "\n".join(lines)
    with open(os.path.join(HERE, "baseline_check.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
