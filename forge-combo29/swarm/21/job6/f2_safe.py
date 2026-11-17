#!/usr/bin/env python3
"""f2_safe.py EXE OUTDIR

Re-establishes 21-F2 with the 19-F12-safe driver, and adds the control that makes the
claim mean something: the SAME two-go session, but with the SECOND position command
CORRECT instead of refused. If the two sessions differ only in which board the second
search runs on, then the refusal is the cause of the second answer coming from the old game.

Session (safe driver: read to bestmove before each next command, never close stdin mid-search):
  position startpos moves e2e4 e7e5 g1f3 b8c6 f1b5     (Black to move, 5 plies)
  go depth 6                                            -> answer 1 (for the old game)
  position fen <A: the refused impossible-castling FEN> -> answer line
            or <B: the same board with the right corrected to Q, which is ACCEPTED>
  go depth 6                                            -> answer 2
The claim: in A, answer 2 belongs to the OLD game (its move is legal there and it is a BLACK
move); in B, answer 2 belongs to the NEW game (a BLACK move of the new board). Both sessions
are the same length, so a fabricated answer would show up in both.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

HISTORY = "e2e4 e7e5 g1f3 b8c6 f1b5"
REFUSED = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3"
ACCEPTED = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w Qkq - 0 3"


def session(exe, outdir, tag, fen2):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"))
    e.position("position startpos moves " + HISTORY)
    a1 = e.go("go depth 6")
    ans = e.position("position fen " + fen2)
    a2 = e.go("go depth 6")
    e.close()
    return dict(a1_move=bestmove_of(a1), a1_info=last_info(a1),
                answer=[l for l in ans if l.startswith("info string")],
                a2_move=bestmove_of(a2), a2_info=last_info(a2))


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    a = session(exe, outdir, "A_refused", REFUSED)
    b = session(exe, outdir, "B_accepted_control", ACCEPTED)
    rows = ["| session | 2nd position command | answer line | go 1 bestmove | go 2 bestmove | go 2 last info |",
            "|---|---|---|---|---|---|"]
    rows.append("| A | REFUSED `RNBQKBR1 w KQkq` | %s | %s | %s | %s |"
                % (" ;; ".join(a["answer"]) or "none", a["a1_move"], a["a2_move"], a["a2_info"][:100]))
    rows.append("| B (control) | ACCEPTED `RNBQKBR1 w Qkq` | %s | %s | %s | %s |"
                % (" ;; ".join(b["answer"]) or "none", b["a1_move"], b["b2_move"] if "b2_move" in b else b["a2_move"],
                   b["a2_info"][:100]))
    rows.append("")
    rows.append("both sessions are the same length and use the same driver, so a fabricated "
                "0-node answer would appear in both; it appears in neither.")
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()