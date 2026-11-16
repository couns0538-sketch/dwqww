#!/usr/bin/env python3
"""gui_sequence.py EXE BUILD — realistic GUI flow on PC20, Threads 1.
The dangerous sequence: a game ends, GUI sends a malformed/truncated FEN for the next game,
gets readyok, and asks for a move. What does it receive?"""
import os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
SEQ=[("1. game 1 position (Black to move)","position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"),
     ("2. GUI switches to game 2, sends TRUNCATED fen","position fen 4k3/8/8/8/8/8/8/4K3 w - -"),
     ("   ...gets readyok, asks for a move","go depth 5")]
e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
try:
    for label,cmd in SEQ:
        e.send(cmd)
        if cmd.startswith("position"):
            e.send("isready"); sync=e.read_until("readyok")
            ref=[l for l in sync if "invalid" in l]
            print(f"{label}\n    sent. refusal={ref if ref else 'none (silent)'}")
        else:
            infos,bm,_=e.go(cmd)
            b_old=chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3")
            b_new=chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
            mv=chess.Move.from_uci(bm)
            which = "GAME 1 (stale!)" if (mv in b_old.legal_moves and mv not in b_new.legal_moves) else \
                    ("game 2 (correct)" if mv in b_new.legal_moves else "neither")
            print(f"{label}\n    bestmove={bm}  belongs to: {which}")
finally: e.quit()
