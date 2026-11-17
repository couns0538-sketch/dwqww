"""JOB 11: does `ucinewgame` fully reset a reused process, or does board history leak?

Jobs 3/3b/3c showed `ucinewgame` restores the fresh-process answer on isolated positions
(0/25) and across a game walk (0/6). That tests the NODE COUNT. It does not test whether
the position HISTORY (the repetition-detection state) leaks, because a leaked history
does not change a node count on a position that has no repetition in it.

This matters for a harness in one specific way: repetition and fifty-move scores are
computed from history the engine retains, so if history survived a `ucinewgame` a position
reached twice in one process could be scored as a draw while the same position in a fresh
process is scored on its merits. That is a silently different measurement.

Three probes:

  P1 REPETITION CARRIED IN A MOVE LIST. Two different move orders reaching the SAME board,
     one of which passes through the position twice (a real threefold is present in the
     move list) and one which does not. In a FRESH process both must be scored on the
     board. If `position startpos moves ...` retains repetitions, the repeated one shows a
     draw score. This tests the engine's own history handling, independent of ucinewgame.

  P2 HISTORY ACROSS SEARCHES. Search a repetition position, then `ucinewgame`, then search
     a clean position. Compare against a fresh process. A leak would show as the clean
     position scoring 0.

  P3 UCI `position fen` AFTER A REPETITION POSITION. The strongest form: the same FEN,
     reached (a) in a fresh process, (b) after a repetition-laden position in the same
     process with `ucinewgame` between. Any difference is a leak that survives ucinewgame.

A repetition-bearing move list is built with python-chess so the threefold is real, not
assumed: the script asserts `board.is_repetition(3)` before using it.
"""

import json
import os
import sys

import chess

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS = [("Threads", 1), ("Hash", 16)]
BUDGET = "go depth 12"


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def build_repetition_moves():
    """A legal move list that reaches a threefold repetition. Asserted, not assumed."""
    board = chess.Board()
    moves = []
    # Knight shuffle: g1f3 g8f6 f3g1 f6g8, twice. Reaches startpos a third time.
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    for _ in range(2):
        for uci in cycle:
            move = chess.Move.from_uci(uci)
            assert move in board.legal_moves, (uci, board.fen())
            board.push(move)
            moves.append(uci)
    assert board.is_repetition(3), "the built move list is not a threefold repetition"
    return moves, board.fen()


def fresh_fen(fen, budget=BUDGET):
    engine = ucih.Engine(BASE_EXE, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def fresh_moves(moves, budget=BUDGET):
    engine = ucih.Engine(BASE_EXE, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_startpos(moves)
        return key(engine.go(budget))
    finally:
        engine.close()


def main():
    rep_moves, rep_fen = build_repetition_moves()
    print("=== JOB 11: history leakage across ucinewgame ===")
    print("budget %s, Threads 1, Hash 16\n" % BUDGET)
    print("repetition move list (%d plies) reaches %s" % (len(rep_moves), rep_fen))
    print("  python-chess is_repetition(3) asserted True\n")

    report = {"budget": BUDGET, "rep_moves": rep_moves, "rep_fen": rep_fen}
    fails = 0

    # ---- P1: the move list itself carries the repetition ----
    print("-- P1: does a repetition in the move list change the score? --")
    rep_score = fresh_moves(rep_moves)
    fen_score = fresh_fen(rep_fen)
    print("   via moves (3rd occurrence in list): %s" % (rep_score,))
    print("   via fen   (same board, no history): %s" % (fen_score,))
    p1_differs = rep_score != fen_score
    print("   the two agree: %s" % (not p1_differs))
    report["P1"] = {"via_moves": list(rep_score), "via_fen": list(fen_score),
                    "differ": p1_differs}

    # A clean control: a move list with no repetition must equal its FEN.
    clean_moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    board = chess.Board()
    for uci in clean_moves:
        board.push(chess.Move.from_uci(uci))
    clean_fen = board.fen()
    clean_via_moves = fresh_moves(clean_moves)
    clean_via_fen = fresh_fen(clean_fen)
    print("   control (no repetition): moves %s / fen %s -> agree %s"
          % (clean_via_moves, clean_via_fen, clean_via_moves == clean_via_fen))
    report["P1_control"] = {"via_moves": list(clean_via_moves),
                            "via_fen": list(clean_via_fen),
                            "agree": clean_via_moves == clean_via_fen}
    print()

    # ---- P2 / P3: does ucinewgame remove whatever P1 shows ----
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    target = valid[2]
    fresh_target = fresh_fen(target)
    print("-- P2/P3: target position searched after a repetition, with ucinewgame between --")
    print("   fresh reference for the target: %s" % (fresh_target,))

    for order, label in (
        (("rep_moves", "ucinewgame", "target_fen"), "repetition(moves) -> ucinewgame -> target"),
        (("rep_fen", "ucinewgame", "target_fen"), "repetition(fen)   -> ucinewgame -> target"),
        (("target_fen", "ucinewgame", "target_fen"), "target            -> ucinewgame -> target"),
    ):
        engine = ucih.Engine(BASE_EXE, timeout=600)
        try:
            engine.uci()
            for name, value in OPTIONS:
                engine.setoption(name, value)
            for step in order:
                if step == "ucinewgame":
                    engine.newgame()
                elif step == "rep_moves":
                    engine.position_startpos(rep_moves)
                    engine.go(BUDGET)
                elif step == "rep_fen":
                    engine.position_fen(rep_fen)
                    engine.go(BUDGET)
                elif step == "target_fen":
                    engine.position_fen(target)
                    got = key(engine.go(BUDGET))
        finally:
            engine.close()
        same = got == fresh_target
        print("   %-42s %s  %s" % (label, got, "same" if same else "<-- DIFFERS"))
        report.setdefault("P2P3", {})[label] = {"cell": list(got), "same_as_fresh": same}
        if not same:
            fails += 1
    print()

    # ---- P3b: the same, but WITHOUT ucinewgame, to show the leak exists at all ----
    print("-- P3b: same sequence WITHOUT ucinewgame (the leak, if any) --")
    engine = ucih.Engine(BASE_EXE, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_startpos(rep_moves)
        engine.go(BUDGET)
        engine.position_fen(target)
        leaked = key(engine.go(BUDGET))
    finally:
        engine.close()
    print("   repetition(moves) -> target, no reset: %s  %s"
          % (leaked, "same" if leaked == fresh_target else "<-- DIFFERS (leak)"))
    report["P3b_no_reset"] = {"cell": list(leaked), "same_as_fresh": leaked == fresh_target}

    report["n_differing_after_ucinewgame"] = fails
    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job11/history_leak.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
