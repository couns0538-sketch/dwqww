#!/usr/bin/env python3
"""Process-level stop, shutdown, and ponder publication checks."""

import subprocess
import sys
import threading
import time


class Engine:
    def __init__(self, path: str) -> None:
        self.process = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []
        self.lock = threading.Lock()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))

    def send(self, command: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def snapshot(self) -> int:
        with self.lock:
            return len(self.lines)

    def since(self, start: int) -> list[str]:
        with self.lock:
            return self.lines[start:]

    def wait_for(self, predicate, timeout: float, start: int = 0) -> list[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            got = self.since(start)
            if any(predicate(line) for line in got):
                return got
            time.sleep(0.01)
        return self.since(start)

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)


def expect(condition: bool, name: str, detail: str = "") -> None:
    if condition:
        print("PASS", name)
        return
    print("FAIL", name, detail)
    raise SystemExit(1)


def main() -> None:
    engine_path = sys.argv[1]
    engine = Engine(engine_path)
    try:
        engine.send("uci")
        handshake = engine.wait_for(lambda line: line == "uciok", 2)
        expect(any(line == "uciok" for line in handshake), "uci handshake")
        engine.send("isready")
        expect(any(line == "readyok" for line in engine.wait_for(lambda line: line == "readyok", 2)), "ready before search")

        engine.send("position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        mark = engine.snapshot()
        engine.send("go infinite ponder")
        info = engine.wait_for(lambda line: line.startswith("info depth 64 "), 3, mark)
        expect(any(line.startswith("info depth 64 ") for line in info), "infinite ponder reaches depth 64", str(info[-3:]))
        time.sleep(0.05)
        before_hit = engine.snapshot()
        engine.send("ponderhit")
        quiet = engine.wait_for(lambda line: line.startswith("bestmove "), 0.3, before_hit)
        expect(not any(line.startswith("bestmove ") for line in quiet), "ponderhit does not publish an infinite search")
        engine.send("stop")
        stopped = engine.wait_for(lambda line: line.startswith("bestmove "), 2)
        bestmoves = [line for line in stopped if line.startswith("bestmove ")]
        expect(bestmoves == ["bestmove 0000"], "stop after infinite ponderhit publishes one bestmove", str(bestmoves))

        engine.send("position startpos")
        engine.send("setoption name Threads value 2")
        engine.send("isready")
        expect(any(line == "readyok" for line in engine.wait_for(lambda line: line == "readyok", 2)), "threads option")
        mark = engine.snapshot()
        engine.send("go infinite")
        engine.wait_for(lambda line: line.startswith("info depth "), 2, mark)
        burst = engine.snapshot()
        for _ in range(64):
            engine.send("isready")
        ready = engine.wait_for(lambda line: engine.since(burst).count("readyok") >= 64, 2, burst)
        mixed = [line for line in ready if "readyok" in line and line != "readyok"]
        expect(ready.count("readyok") >= 64, "isready stays responsive during search", str(ready.count("readyok")))
        expect(not mixed, "readyok stays on its own line during search", str(mixed[:3]))
        engine.send("stop")
        ended = engine.wait_for(lambda line: line.startswith("bestmove "), 2)
        expect(sum(line.startswith("bestmove ") for line in ended) == 1, "one bestmove after stop")

        mark = engine.snapshot()
        engine.send("go perft 7")
        time.sleep(0.05)
        engine.send("stop")
        engine.send("isready")
        stopped_perft = engine.wait_for(lambda line: line == "readyok", 2, mark)
        expect(any(line == "readyok" for line in stopped_perft), "stop interrupts perft and the engine stays responsive", str(stopped_perft[-5:]))
        expect(any(line == "info string perft stopped" for line in stopped_perft), "perft reports the interrupt")
        expect(not any(line.startswith("nodes ") for line in stopped_perft), "interrupted perft does not publish a partial total")

        mark = engine.snapshot()
        engine.send("go perft 1")
        perft_done = engine.wait_for(lambda line: line.startswith("nodes "), 2, mark)
        expect(any(line == "nodes 20" for line in perft_done), "completed perft 1 is unchanged", str(perft_done))

        mark = engine.snapshot()
        engine.send("bench 10")
        time.sleep(0.05)
        engine.send("stop")
        engine.send("isready")
        stopped_bench = engine.wait_for(lambda line: line == "readyok", 2, mark)
        expect(any(line == "info string bench stopped" for line in stopped_bench), "stop interrupts bench", str(stopped_bench[-5:]))
        expect(any(line == "readyok" for line in stopped_bench), "engine accepts commands after bench stop")

        mark = engine.snapshot()
        engine.send("bench 1")
        completed = engine.wait_for(lambda line: line.startswith("info string bench depth "), 5, mark)
        signature = [line for line in completed if line.startswith("info string bench depth ")]
        expect(len(signature) == 1 and " nodes 884 " in signature[0], "one-thread bench depth 1 node signature is unchanged", str(signature))

        mark = engine.snapshot()
        engine.send("position startpos")
        engine.send("go infinite")
        engine.wait_for(lambda line: line.startswith("info depth "), 2, mark)
        engine.send("quit")
        try:
            code = engine.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            code = None
        expect(code == 0, "quit during search returns", str(code))
    finally:
        if engine.process.poll() is None:
            engine.close()


if __name__ == "__main__":
    main()
