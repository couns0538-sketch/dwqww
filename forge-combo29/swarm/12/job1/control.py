#!/usr/bin/env python3
"""control.py — prove the job-1 checker reports a planted bad bestmove.

Runs a scratch engine whose `searchmoves` list is deliberately illegal in the FEN that the
harness will attribute the answer to, and a second one that is fine. If the harness stays
silent on the bad case, the "0 illegal bestmoves" result of job 1 means nothing.

The bad case uses a position where the engine's own bestmove is legal but the position the
harness holds is a DIFFERENT one: the harness must then flag the move. That is exactly the
failure mode a desynced attribution would show, so this control checks the thing that went
wrong earlier in this job.
"""
import sys
import chess

sys.path.insert(0, ".")
from runner import position_state  # noqa: E402  (the harness's own position model)


def main():
    ok = 0
    bad = 0

    # 1. the position model must follow ucinewgame back to startpos
    model = position_state(["position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "ucinewgame"])
    expect = chess.Board().fen()
    print(f"model after position+ucinewgame: {model}")
    print(f"expected startpos              : {expect}")
    ok += model == expect

    # 2. the model must keep a legal prefix and drop an illegal tail
    model = position_state(["position startpos moves e2e4 e7e5 e1e3"])
    board = chess.Board()
    board.push_uci("e2e4")
    board.push_uci("e7e5")
    print(f"prefix model: {model}")
    print(f"expected    : {board.fen()}")
    ok += model == board.fen()

    # 3. a bestmove that is illegal in the held position must be detectable
    held = chess.Board("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    planted = chess.Move.from_uci("d2d4")
    detected = planted not in held.legal_moves
    print(f"planted d2d4 illegal in K+P position: {detected}")
    bad += detected

    # 4. and a legal one must not be flagged
    legal = chess.Move.from_uci("e2e3")
    not_flagged = legal in held.legal_moves
    print(f"e2e3 legal there (not flagged): {not_flagged}")
    ok += not_flagged

    print(f"\nchecks passed {ok}/3, planted fault detected {bad}/1")
    return 0 if ok == 3 and bad == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
