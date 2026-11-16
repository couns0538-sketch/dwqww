#!/usr/bin/env python3
"""deepseek6 long 61 plant: fake engines that violate ONE MultiPV contract clause each.

The checker (multipv61.py) asserts, per position:
  (a) the returned moves are distinct,
  (b) the scores do not increase down the list,
  (c) every returned move is legal, and the first line equals `bestmove`.

A plant should break exactly one of those and nothing else, so the checker's count can be read
as "it saw THIS defect". This fake therefore:
  * answers the real position (it parses `position fen ...` with python-chess),
  * returns min(k, legal moves) lines using LEGAL moves taken from that position,
  * answers MultiPV 1 in the plain form the engine uses (no `multipv` token),
  * and then breaks exactly one clause in MultiPV 3, under FAKE_MODE:
      dup   -- line 2 repeats line 1                      (breaks a)
      rise  -- scores increase down the list               (breaks b)
      clean -- breaks nothing (the control)
An illegal move is available as `illegal` but is not needed by file 22's two plants.

usage: FAKE_MODE=dup|rise|clean multipv_fake.py
"""
import os
import sys

import chess

MODE = os.environ.get("FAKE_MODE", sys.argv[1] if len(sys.argv) > 1 else "clean")

for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name multipv-fake-%s" % MODE)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("setoption"):
        if "MultiPV" in c:
            try: globals()["k_wanted"] = int(c.split()[-1])
            except ValueError: pass
        continue
    elif c == "ucinewgame":
        continue
    elif c.startswith("position"):
        fen = c.split("fen", 1)[1].strip() if "fen" in c else chess.STARTING_FEN
        board = chess.Board(fen)
        legal = sorted(m.uci() for m in board.legal_moves)
    elif c.startswith("go"):
        # how many lines does the driver want? it sets MultiPV before `go`; track it
        k = globals().get("k_wanted", 1)
        avail = legal[:k] if legal else ["0000"]
        n = len(avail)
        if MODE == "dup" and n >= 2:
            moves = [avail[0], avail[0]] + avail[2:]
            n = len(moves)
        elif MODE == "rise":
            moves = list(avail)
        else:
            moves = list(avail)
        # descending scores by default; `rise` inverts them
        base = 30
        scores = [base - 10 * i for i in range(n)]
        if MODE == "rise":
            scores = [10 + 10 * i for i in range(n)]
        if k == 1:
            # the plain form: no "multipv" token, exactly as the real engine prints it
            print("info depth 10 seldepth 12 score cp %d nodes 4000 pv %s" % (scores[0], moves[0]), flush=True)
        else:
            for i in range(n):
                print("info depth 10 multipv %d score cp %d nodes %d pv %s" %
                      (i + 1, scores[i], 1000 * (i + 1), moves[i]), flush=True)
        print("bestmove %s" % moves[0], flush=True)
    elif c == "quit":
        break
