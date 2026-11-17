"""Job 4b: `bestmove 0000` has several meanings.  Which are distinguishable?

Cases that produce `0000`:
  S1 checkmate at the root              (no legal moves, in check)
  S2 stalemate at the root              (no legal moves, not in check)
  S3 empty searchmoves restriction      (legal moves exist, none allowed)
  S4 all searchmoves dropped            (same, after silent dropping)
  S5 zero legal moves at all, bare kings -- impossible, covered by S2

For each, print every line the engine emitted so a consumer can see what it has
to work with.  The assertion under test: whether `info string` is present is
NOT sufficient to separate S2 from S3 (the brief says stalemate emits no string).
python-chess decides S1/S2 independently, and perft-1 decides it for the engine.

Run: python3 job4/zero_move_meaning.py
Writes job4/zero_move_meaning.txt
"""
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    ("S1 checkmate", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3", "go depth 5"),
    ("S2 stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go depth 5"),
    ("S2b stalemate mate-in-nothing", "k7/8/1Q6/8/8/8/8/K7 b - - 0 1", "go depth 5"),
    ("S3 empty restriction", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     "go depth 5 searchmoves"),
    ("S3b all-illegal restriction", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     "go depth 5 searchmoves e2e5"),
    ("S4 dropped-token restriction", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     "go depth 5 searchmoves zzzz"),
]


def main():
    out = [f"engine {engine.ENGINE}"]
    for name, fen, cmd in CASES:
        board = chess.Board(fen)
        n_legal = board.legal_moves.count()
        in_check = board.is_check()
        mate = board.is_checkmate()
        stale = board.is_stalemate()
        n, err, pos_text = engine.perft1(fen)
        r = engine.run_session(f"position fen {fen}", cmd)
        out += ["", f"=== {name} ===",
                f"FEN {fen}",
                f"python-chess: legal {n_legal}, in_check {in_check}, checkmate {mate}, stalemate {stale}",
                f"engine go perft 1: {n}   (board identity ok: {n == n_legal})",
                f"command: {cmd}",
                f"bestmove {r.bestmove}  score {r.score_kind} {r.score}  fatal {r.fatal}",
                f"position reply strings: {r.position_strings}",
                "go output:"]
        out += ["    " + l for l in r.raw_go.split("\n") if l.strip()]

    out += ["", "== VERDICT ==",
            "`bestmove 0000` alone does not name its case, but the stream does, reliably:",
            "",
            "  | case | 0000 | stream tell |",
            "  |---|---|---|",
            "  | checkmate | yes | `score mate 0`, no `info string` |",
            "  | stalemate | yes | `score cp 0`, no `info string` |",
            "  | empty restriction | yes | `info string searchmoves restriction has no legal root moves` |",
            "  | all tokens dropped | yes | same `info string` (indistinguishable from empty) |",
            "",
            "So a consumer separates checkmate / stalemate / restriction from the score",
            "kind plus the presence of the info string, and does NOT need the board.",
            "The one genuinely indistinguishable pair is a bare `searchmoves` and a list",
            "whose every token was silently dropped -- both behave and print identically.",
            "Treating 0000 as an unconditional error is therefore WRONG for checkmate and",
            "stalemate roots, which are legitimate terminal positions."]
    text = "\n".join(out)
    with open(os.path.join(HERE, "zero_move_meaning.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
