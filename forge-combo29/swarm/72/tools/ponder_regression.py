#!/usr/bin/env python3
"""Independent UCI process tests for genuine pondering and publication ordering."""
import argparse
import re
import time
from pathlib import Path
from uci_regression import Engine


def run(engine):
    e = Engine(engine)
    passed = []
    try:
        e.send("uci")
        text = e.until(lambda line: line == "uciok")
        assert "option name Ponder type check default false" in text, text
        e.ready()
        passed.append("Ponder UCI option advertised")
        e.send("setoption name Ponder value true")
        e.ready()
        e.position()
        e.send("go depth 5")
        standard = e.until(lambda line: line.startswith("bestmove "))[-1]
        assert re.fullmatch(r"bestmove [a-h][1-8][a-h][1-8][qrbn]? ponder [a-h][1-8][a-h][1-8][qrbn]?", standard), standard
        root, reply = standard.split()[1], standard.split()[3]
        e.position("startpos moves " + root)
        assert e.search("go depth 1 searchmoves " + reply)[0] == reply
        passed.append("normal search publishes a legal ponder prediction")
        e.position()
        e.send("go ponder movetime 25 searchmoves e2e4")
        e.until(lambda line: line.startswith("info depth "))
        time.sleep(0.12)  # Exceeds requested own-clock movetime before ponderhit.
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.05)
        e.ready()
        start = time.monotonic()
        e.send("ponderhit")
        answer = e.until(lambda line: line.startswith("bestmove "), timeout=4)[-1]
        assert answer.split()[1] == "e2e4", answer
        assert time.monotonic() - start < 3
        passed.append("movetime does not expire until ponderhit; restricted root")
        e.position("fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        e.send("go ponder depth 2")
        e.until(lambda line: line.startswith("info depth 2 "))
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.05)
        e.send("ponderhit")
        assert e.until(lambda line: line.startswith("bestmove "))[-1] == "bestmove 0000"
        passed.append("terminal ponder waits for hit")
        e.position()
        e.send("go ponder infinite")
        e.until(lambda line: line.startswith("info depth "))
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.02)
        e.send("stop")
        assert e.until(lambda line: line.startswith("bestmove "))[-1].startswith("bestmove ")
        passed.append("stop while pondering publishes one result")
        e.position()
        e.send("go ponder nodes 0 searchmoves e2e4")
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.05)
        e.send("ponderhit")
        assert e.until(lambda line: line.startswith("bestmove "))[-1].split()[1] == "e2e4"
        passed.append("zero-node ponder waits for hit and preserves legal fallback")
        # Immediate ponderhit can arrive before the worker thread starts.
        for _ in range(16):
            e.position()
            e.send("go ponder movetime 10")
            e.send("ponderhit")
            assert e.until(lambda line: line.startswith("bestmove "), timeout=3)[-1].split()[1] != "0000"
        passed.append("sixteen immediate ponderhits are race-safe")
        e.position("startpos moves e2e4")
        e.send("go ponder wtime 200 btime 180 winc 2 binc 5 movestogo 30")
        e.until(lambda line: line.startswith("info depth "))
        time.sleep(0.1)
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.04)
        e.send("ponderhit")
        assert e.until(lambda line: line.startswith("bestmove "), timeout=3)[-1].split()[1] != "0000"
        passed.append("opponent-side clock starts on hit, not on ponder start")
        e.send("setoption name Ponder value false")
        e.ready()
        e.position()
        plain = e.search("go depth 3")[1][-1]
        assert " ponder " not in plain
        passed.append("Ponder disabled omits predicted move")
        e.send("setoption name Ponder value invalid")
        assert "invalid value for option Ponder" in e.until(lambda line: "invalid value for option Ponder" in line)[-1]
        e.ready()
        e.position()
        assert e.search("go depth 2")[0] != "0000"
        passed.append("invalid option rejected; subsequent ordinary search")
    finally:
        e.close()
    return passed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", type=Path)
    a = ap.parse_args()
    for item in run(a.engine):
        print("PASS", item)
