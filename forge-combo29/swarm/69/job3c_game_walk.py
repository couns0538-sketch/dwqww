"""JOB 3c: the reuse trap on the pattern a real harness uses — walking games.

A harness that evaluates positions from games usually keeps ONE process and sends
`position startpos moves ...` for each ply, or `position fen ...` for a list. Jobs 3 and
3b used `position fen` on independent openings. This job uses both command forms on
positions reached by actual random-legal games, and measures which reset restores the
fresh-process answer.

Also verifies that `position fen X` and `position startpos moves <moves reaching X>`
produce the same cell in a fresh process — if they did not, a harness would be measuring
something other than the board it thinks it has.
"""

import json
import random
import sys

import chess

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS = [("Threads", 1), ("Hash", 16)]
BUDGET = "go nodes 50000"
SEED = 6901
N_GAMES = 6


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def random_game(seed, maxply=40):
    rng = random.Random(seed)
    board = chess.Board()
    moves = []
    for _ in range(maxply):
        if board.is_game_over():
            break
        move = rng.choice(list(board.legal_moves))
        moves.append(move.uci())
        board.push(move)
    return moves, board.fen()


def fresh_fen(fen):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return key(engine.go(BUDGET))
    finally:
        engine.close()


def fresh_moves(moves):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_startpos(moves)
        return key(engine.go(BUDGET))
    finally:
        engine.close()


def walk(games, reset, use_moves):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    out = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        for moves, fen in games:
            if reset == "ucinewgame":
                engine.newgame()
            elif reset == "clearhash":
                engine.clear_hash()
            if use_moves:
                engine.position_startpos(moves)
            else:
                engine.position_fen(fen)
            out.append(key(engine.go(BUDGET)))
    finally:
        engine.close()
    return out


def main():
    games = [random_game(SEED + i) for i in range(N_GAMES)]
    report = {"seed": SEED, "n_games": N_GAMES, "budget": BUDGET, "games": []}

    print("=== JOB 3c: reuse trap while walking games, %s ===" % BUDGET)
    print("games: %d, seed %d, plies each: %s\n"
          % (N_GAMES, SEED, [len(m) for m, _ in games]))

    ref_fen = [fresh_fen(fen) for _, fen in games]
    ref_moves = [fresh_moves(moves) for moves, _ in games]
    form_diff = [i for i in range(N_GAMES) if ref_fen[i] != ref_moves[i]]
    print("position fen vs position startpos moves, fresh process: %d / %d differ %s\n"
          % (len(form_diff), N_GAMES, form_diff))
    report["fen_vs_moves"] = {"n": N_GAMES, "n_differing": len(form_diff),
                              "differing": form_diff}

    for use_moves in (True, False):
        label = "position startpos moves" if use_moves else "position fen"
        print("-- %s --" % label)
        for reset in ("none", "clearhash", "ucinewgame"):
            got = walk(games, reset, use_moves)
            diff = [i for i in range(N_GAMES) if got[i] != ref_fen[i]]
            print("   reset=%-11s differ %d / %d %s" % (reset, len(diff), N_GAMES, diff))
            report.setdefault("walks", {}).setdefault(label, {})[reset] = {
                "n": N_GAMES, "n_differing": len(diff), "differing": diff,
                "cells": [list(c) for c in got],
            }
        print()

    report["reference"] = [list(c) for c in ref_fen]

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job3/game_walk.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("raw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
