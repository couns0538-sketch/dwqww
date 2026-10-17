#!/usr/bin/env python3
"""Process-level UCI regression driver (MIT; no third-party Python modules)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import queue
import re
import subprocess
import threading
import time


class Engine:
    def __init__(self, executable: Path):
        self.process = subprocess.Popen([str(executable.resolve())], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1)
        self.lines: queue.Queue = queue.Queue()
        self.transcript: list[str] = []
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            line = line.rstrip()
            self.transcript.append("< " + line)
            self.lines.put(line)
        self.lines.put(None)

    def send(self, command: str):
        self.transcript.append("> " + command)
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def until(self, predicate, timeout: float = 15.0):
        deadline = time.monotonic() + timeout
        seen = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError("UCI response deadline exceeded")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise AssertionError("UCI response deadline exceeded") from error
            if line is None:
                raise AssertionError("engine exited before expected UCI response")
            seen.append(line)
            if predicate(line):
                return seen

    def ready(self):
        self.send("isready")
        self.until(lambda line: line == "readyok")

    def ready_burst(self, count: int, timeout: float = 5.0):
        self.transcript.extend(["> isready"] * count)
        self.process.stdin.write("isready\n" * count)
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        seen = 0
        while seen < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"received only {seen}/{count} standalone readyok records")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise AssertionError(f"received only {seen}/{count} standalone readyok records") from error
            if line is None:
                raise AssertionError("engine exited during readiness burst")
            if "readyok" in line and line != "readyok":
                raise AssertionError(f"interleaved UCI output record: {line!r}")
            if line == "readyok":
                seen += 1

    def assert_absent(self, predicate, duration: float):
        deadline = time.monotonic() + duration
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return
            if line is None:
                raise AssertionError("engine exited during absence check")
            if predicate(line):
                raise AssertionError(f"unexpected UCI response: {line}")

    def position(self, text="startpos"):
        self.send("position " + text)
        self.ready()

    def search(self, command):
        self.send(command)
        lines = self.until(lambda line: line.startswith("bestmove "))
        move = lines[-1].split()[1]
        assert re.fullmatch(r"0000|[a-h][1-8][a-h][1-8][qrbn]?", move), move
        return move, lines

    def close(self):
        if self.process.poll() is None:
            self.send("quit")
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                raise AssertionError("quit failed")
        self.reader.join(timeout=2)
        assert self.process.returncode == 0, f"engine exited {self.process.returncode}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--known-v56", action="store_true")
    parser.add_argument("--extended-perft", action="store_true")
    a = parser.parse_args()
    e = Engine(a.engine)
    passed = []
    known_failures = []
    timings = {}
    try:
        e.send("uci")
        identification = e.until(lambda line: line == "uciok")
        assert any(line.startswith("id name Chess Engine Forge") for line in identification)
        e.ready(); passed.append("handshake/readiness")
        e.send("setoption name Hash value 33")
        e.ready()
        e.position()
        move, lines = e.search("go depth 4")
        assert move != "0000" and any("info depth 4 " in line for line in lines)
        passed.append("finite depth and non-power-of-two Hash")
        e.position()
        move, _ = e.search("go depth 3 searchmoves e2e4 d2d4")
        assert move in ("e2e4", "d2d4")
        passed.append("restricted searchmoves")
        null_fen = "fen 2rqNN2/4k3/ppp2pB1/3p4/PPPp1Prb/n3P2b/K7/4Q3 b - - 0 34"
        null_cases = (
            ("a3b5", ("a3b5",)),
            ("g4g3", ("g4g3",)),
            ("a3b5 g4g3", ("a3b5", "g4g3")),
        )
        for restricted, allowed in null_cases:
            e.send("setoption name Clear Hash")
            e.ready()
            e.position(null_fen)
            move, lines = e.search("go depth 6 searchmoves " + restricted)
            assert move in allowed, (restricted, move)
            depth6 = [line for line in lines if "info depth 6 " in line]
            assert depth6 and all(" pv " + m in line for line in depth6 for m in (move,)), lines
            assert all("score cp " in line for line in depth6), lines
        passed.append("restricted-root search reports the restricted move with a finite score")
        e.position()
        start = time.monotonic()
        move, lines = e.search("go nodes 0 searchmoves e2e4")
        timings["nodes_0_wall_seconds"] = time.monotonic() - start
        assert move == "e2e4", move
        assert not any(line.startswith("info depth ") for line in lines), lines
        assert timings["nodes_0_wall_seconds"] < 1
        passed.append("explicit zero nodes is an immediate bounded search")
        e.position()
        move, _ = e.search("go nodes 1 searchmoves e2e4")
        if a.known_v56 and move == "0000":
            known_failures.append("one-node restricted fallback returns 0000")
        else:
            assert move == "e2e4", move
            passed.append("one-node restricted fallback")
        e.position()
        empty_move, empty_lines = e.search("go depth 2 searchmoves a1a8")
        assert empty_move == "0000" and any("score cp 0" in line for line in empty_lines), empty_lines
        assert not any("score mate" in line for line in empty_lines), empty_lines
        passed.append("empty restricted intersection")
        e.position("fen 4r2k/8/8/8/8/8/8/4K3 w - - 0 1")
        move, lines = e.search("go depth 2 searchmoves a1a8")
        assert move == "0000", lines
        assert any("score cp 0" in line for line in lines), lines
        assert not any("score mate" in line for line in lines), lines
        assert any("info string searchmoves" in line for line in lines), lines
        passed.append("in-check empty searchmoves reports no result, not mate")
        e.position("fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        move, lines = e.search("go depth 2 searchmoves a1a8")
        assert move == "0000" and any("score mate 0" in line for line in lines), lines
        passed.append("true mate is preserved under restriction")
        e.position("fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        move, lines = e.search("go depth 2 searchmoves a1a8")
        assert move == "0000" and any("score cp 0" in line for line in lines), lines
        assert not any("score mate" in line for line in lines), lines
        passed.append("true stalemate is preserved under restriction")
        e.position()
        move, lines = e.search("go depth 2 searchmoves e2e4")
        assert move == "e2e4" and any(" pv e2e4" in line for line in lines), lines
        passed.append("nonempty restricted root still searches allowed move")
        e.position("fen 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1")
        move, lines = e.search("go mate 1")
        assert move == "e1e8" and any("score mate 1" in line for line in lines)
        passed.append("mate in one")
        e.position("fen 4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        assert e.search("go depth 2 searchmoves a7a8n")[0] == "a7a8n"
        passed.append("underpromotion restriction")
        e.position("fen 4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        assert e.search("go depth 2 searchmoves e5d6")[0] == "e5d6"
        e.position("fen k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        assert e.search("go depth 2 searchmoves e5d6")[0] == "0000"
        passed.append("legal and pinned en passant")
        e.send("ucinewgame")
        e.position("startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8")
        _, lines = e.search("go depth 2")
        assert any("score cp 0" in line for line in lines)
        passed.append("threefold history")
        e.send("ucinewgame")
        e.position("fen 7k/8/8/8/8/8/8/KR6 w - - 100 1")
        _, lines = e.search("go depth 2")
        assert any("score cp 0" in line for line in lines)
        passed.append("cold rule-50 draw (not TT cross-context safety)")
        e.position("fen 7k/6Q1/6K1/8/8/8/8/8 b - - 100 1")
        assert e.search("go depth 2")[0] == "0000"
        passed.append("rule-50 checkmate has no legal move")
        e.position("fen 7k/6Q1/6K1/8/8/8/8/8 b - - 100 1")
        e.send("go infinite")
        e.until(lambda line: line.startswith("info depth 64 "), timeout=2)
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.02)
        e.ready()
        start = time.monotonic()
        e.send("stop")
        reply = e.until(lambda line: line.startswith("bestmove "), timeout=2)
        timings["terminal_infinite_stop_seconds"] = time.monotonic() - start
        assert reply[-1] == "bestmove 0000"
        passed.append("terminal infinite waits for stop")
        e.position("fen 7k/8/8/8/8/8/8/K7 w - - 0 1")
        e.send("go infinite")
        e.until(lambda line: line.startswith("info depth 64 "), timeout=2)
        e.assert_absent(lambda line: line.startswith("bestmove "), 0.02)
        e.send("stop")
        reply = e.until(lambda line: line.startswith("bestmove "), timeout=2)
        assert reply[-1] != "bestmove 0000"
        passed.append("adjudicated legal-move infinite waits for stop")
        e.position()
        e.send("go infinite")
        e.until(lambda line: line.startswith("info depth "))
        e.ready_burst(512)
        start = time.monotonic()
        e.send("stop")
        reply = e.until(lambda line: line.startswith("bestmove "), timeout=2)
        timings["stop_seconds"] = time.monotonic() - start
        assert reply[-1] != "bestmove 0000"
        passed.append("atomic concurrent info/readiness records and stop")
        e.position()
        start = time.monotonic()
        assert e.search("go movetime 50")[0] != "0000"
        timings["movetime_50_wall_seconds"] = time.monotonic() - start
        assert timings["movetime_50_wall_seconds"] < 2
        passed.append("finite movetime responsiveness")
        e.position()
        start = time.monotonic()
        assert e.search("go movetime 0")[0] != "0000"
        timings["movetime_0_wall_seconds"] = time.monotonic() - start
        assert timings["movetime_0_wall_seconds"] < 1
        passed.append("explicit zero movetime is bounded")
        e.position()
        start = time.monotonic()
        assert e.search("go wtime 0 btime 1000 movestogo 30")[0] != "0000"
        timings["white_clock_0_wall_seconds"] = time.monotonic() - start
        assert timings["white_clock_0_wall_seconds"] < 1
        e.position("startpos moves e2e4")
        start = time.monotonic()
        assert e.search("go wtime 1000 btime 0 movestogo 30")[0] != "0000"
        timings["black_clock_0_wall_seconds"] = time.monotonic() - start
        assert timings["black_clock_0_wall_seconds"] < 1
        passed.append("explicit zero side clocks are bounded")
        if not a.known_v56:
            e.position()
            assert e.search("go depth 1 wtime 2147483647 winc 2147483647")[0] != "0000"
            passed.append("maximum signed-int clock/increment")
        for value in ("oops", "9999999999999999999999", "4junk"):
            e.send("setoption name Hash value " + value)
            e.until(lambda line: "invalid value for option Hash" in line)
        e.send("setoption name Move Overhead value -1")
        e.send("setoption name Clear Hash")
        e.ready(); passed.append("malformed options and clear hash")
        e.position()
        e.send("position startpos moves e2e4 illegal")
        e.until(lambda line: "illegal move illegal" in line)
        e.send("go perft 1")
        assert e.until(lambda line: line.startswith("nodes "))[-1] == "nodes 20"
        passed.append("transactional invalid move sequence")
        for depth in ("-1", "x", "9999999999999999999", "11"):
            e.send("go perft " + depth)
            e.until(lambda line: "perft depth must be" in line)
        e.send("go perft 0")
        assert e.until(lambda line: line.startswith("nodes "))[-1] == "nodes 1"
        passed.append("perft zero and invalid depths")
        if a.extended_perft:
            for fen, depth, expected in (
                ("startpos", 6, 119060324),
                ("fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, 4085603),
                ("fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624)):
                e.position(fen)
                e.send(f"go perft {depth}")
                assert e.until(lambda line: line.startswith("nodes "), timeout=60)[-1] == f"nodes {expected}"
                passed.append(f"perft depth {depth}: {expected}")
        print(json.dumps({"passed": passed, "known_failures": known_failures, "timings": timings}, indent=2))
    finally:
        try:
            e.close()
        finally:
            a.log.parent.mkdir(parents=True, exist_ok=True)
            a.log.write_text("\n".join(e.transcript) + "\n")


if __name__ == "__main__":
    main()
