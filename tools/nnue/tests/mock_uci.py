#!/usr/bin/env python
"""Deterministic integration-test UCI peer; never used for real training."""
import json
import os
from pathlib import Path
import sys
import time
import chess

board = chess.Board()
directory = Path(os.environ["FORGE_TEST_TRACE"])
directory.mkdir(parents=True, exist_ok=True)
trace = directory / f"engine-{os.getpid()}.jsonl"


def log(event, **fields):
    with open(trace, "a") as dst:
        dst.write(json.dumps({"event": event, **fields}) + "\n")


log("start")
for raw in sys.stdin:
    command = raw.strip()
    log("command", text=command)
    if command == "uci":
        print("id name ForgeTestPeer\noption name Threads type spin default 4 min 1 max 256\n"
              "option name Hash type spin default 32 min 1 max 1024\nuciok", flush=True)
    elif command == "isready":
        print("readyok", flush=True)
    elif command.startswith("position"):
        assert command.startswith("position startpos moves ")
        board = chess.Board()
        for move in command.split()[3:]:
            board.push_uci(move)
    elif command.startswith("go"):
        mode = os.environ.get("FORGE_TEST_MODE", "normal")
        log("go", affinity=sorted(os.sched_getaffinity(0)),
            nice=os.getpriority(os.PRIO_PROCESS, 0), ply=board.ply())
        if mode == "hang":
            time.sleep(5)
        if mode == "fail":
            raise SystemExit(12)
        time.sleep(.002)
        move = next(iter(board.legal_moves))
        print(f"info depth 1 nodes 3000 score cp 50 lowerbound pv {move.uci()}", flush=True)
        print(f"info depth 2 nodes 5000 score cp 25 pv {move.uci()}\nbestmove {move.uci()}", flush=True)
    elif command == "quit":
        log("quit")
        break
