#!/usr/bin/env bash
# fake_engine.sh : a CONTROL engine that answers perft-1 correctly EXCEPT on the position whose FEN is in
# $FAKE_FEN (then it omits one legal move and invents another). It exists only to prove that divide_sets.py
# REPORTS a disagreement when one is really there. It is not an engine and never touches the real binary.
set -u
FAKE_FEN="${FAKE_FEN:?set FAKE_FEN}"
python3 -u - "$FAKE_FEN" <<'PY'
import re, sys
import chess
bad = sys.argv[1]
cur = None
for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name fake-control"); print("uciok")
    elif cmd == "isready":
        print("readyok")
    elif cmd == "ucinewgame":
        pass
    elif cmd.startswith("position fen "):
        cur = cmd[len("position fen "):].strip()
    elif cmd.startswith("go perft 1"):
        b = chess.Board(cur) if cur else chess.Board()
        moves = sorted(m.uci() for m in b.legal_moves)
        if cur == bad and moves:
            # drop one real move, add one that is NOT legal here (a1a1 is never legal)
            moves = moves[1:] + ["a1a1"]
        for m in moves:
            print(f"{m}: 1")
        print(f"nodes {len(moves)}")
    elif cmd == "quit":
        break
PY
