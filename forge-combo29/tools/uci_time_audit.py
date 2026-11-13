#!/usr/bin/env python3
"""UCI audit of Forge clocks, increments, stop, and perft interruption.

Usage: python3 tools/uci_time_audit.py /path/to/forge
Exits 0 when every case holds. Timing bounds include scheduler slack measured
on a release build; they still reject a search that ignores the clock or stop.
"""
import queue
import subprocess
import sys
import threading
import time

START_PERFT = {1: 20, 2: 400, 4: 197281, 5: 4865609, 6: 119060324}


class Engine:
    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.q = queue.Queue()

        def pump():
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\r\n"))
            self.q.put(None)

        threading.Thread(target=pump, daemon=True).start()

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def wait(self, pred, timeout):
        deadline = time.monotonic() + timeout
        got = []
        while time.monotonic() < deadline:
            try:
                line = self.q.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            got.append(line)
            if pred(line):
                return got
        return got

    def drain(self, timeout=0.02):
        return self.wait(lambda _line: False, timeout)

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def best(lines):
    for line in lines:
        if line.startswith("bestmove "):
            return line
    return None


def fail(message):
    raise SystemExit("FAIL " + message)


def main():
    if len(sys.argv) != 2:
        fail("usage: uci_time_audit.py <forge>")
    engine = Engine(sys.argv[1])
    passed = []
    try:
        engine.send("uci")
        if not any(line == "uciok" for line in engine.wait(lambda line: line == "uciok", 3)):
            fail("uci handshake")
        engine.send("setoption name OwnBook value false")
        engine.send("setoption name Ponder value false")
        engine.send("setoption name Threads value 1")
        engine.send("setoption name Hash value 16")
        engine.send("setoption name Move Overhead value 0")
        engine.send("isready")
        if not any(line == "readyok" for line in engine.wait(lambda line: line == "readyok", 2)):
            fail("ready after options")

        def new_game(position):
            engine.send("ucinewgame")
            engine.send("isready")
            if not any(line == "readyok" for line in engine.wait(lambda line: line == "readyok", 2)):
                fail("ready after ucinewgame")
            engine.send(position)
            engine.drain()

        def go(command, timeout):
            start = time.monotonic()
            engine.send(command)
            lines = engine.wait(lambda line: line.startswith("bestmove "), timeout)
            return (time.monotonic() - start) * 1000.0, lines

        for millis in (40, 100):
            new_game("position startpos")
            wall, lines = go(f"go movetime {millis}", 2)
            if best(lines) is None or not (millis * 0.45 <= wall <= millis + 40):
                fail(f"movetime {millis} wall {wall:.1f} best {best(lines)}")
            passed.append(f"movetime {millis} {wall:.1f}ms")

        engine.send("setoption name Move Overhead value 40")
        engine.send("isready")
        engine.wait(lambda line: line == "readyok", 2)
        new_game("position startpos")
        wall, lines = go("go movetime 100", 2)
        if best(lines) is None or not (20 <= wall <= 85):
            fail(f"overhead reservation wall {wall:.1f}")
        passed.append(f"movetime 100 overhead 40 {wall:.1f}ms")
        engine.send("setoption name Move Overhead value 0")
        engine.send("isready")
        engine.wait(lambda line: line == "readyok", 2)

        new_game("position startpos")
        wall, lines = go("go wtime 70 btime 8000 winc 0 binc 0", 1)
        if best(lines) is None or wall > 110:
            fail(f"white clock wall {wall:.1f} {best(lines)}")
        passed.append(f"white 70ms clock {wall:.1f}ms")

        new_game("position startpos moves e2e4")
        wall, lines = go("go wtime 8000 btime 70 winc 0 binc 0", 1)
        move = best(lines) or ""
        if not move.startswith("bestmove ") or move == "bestmove 0000" or wall > 110:
            fail(f"black clock wall {wall:.1f} {move}")
        passed.append(f"black 70ms clock {wall:.1f}ms {move}")

        new_game("position startpos")
        wall, lines = go("go wtime 100 btime 100 winc 9000 binc 0 movestogo 1", 1)
        if best(lines) is None or wall > 130:
            fail(f"increment spent past the clock wall {wall:.1f}")
        passed.append(f"movestogo 1 plus large increment {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime 160 btime 160 winc 8000 binc 8000", 1)
        if best(lines) is None or wall > 190:
            fail(f"sudden-death increment wall {wall:.1f}")
        passed.append(f"sudden death large increment {wall:.1f}ms")

        budgets = {}
        for moves_to_go in (1, 25):
            new_game("position startpos")
            wall, lines = go(f"go wtime 2000 btime 2000 winc 0 binc 0 movestogo {moves_to_go}", 4)
            if best(lines) is None or wall > 2050:
                fail(f"movestogo {moves_to_go} wall {wall:.1f}")
            budgets[moves_to_go] = wall
        if budgets[1] < budgets[25] + 200:
            fail(f"movestogo did not scale {budgets}")
        passed.append(f"movestogo 1 vs 25 {budgets[1]:.0f}ms vs {budgets[25]:.0f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime 200 btime 200 winc 3000000000 binc 0", 1)
        if best(lines) is None or not (80 <= wall <= 230):
            fail(f"overflow increment wall {wall:.1f}")
        passed.append(f"increment above int max stays inside 200ms {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime 1000 btime 1000 movestogo 3000000000", 2)
        if best(lines) is None or wall > 200:
            fail(f"overflow movestogo wall {wall:.1f}")
        passed.append(f"movestogo above int max is many moves, not one {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime 0 btime 1000", 1)
        if best(lines) is None or wall > 40:
            fail(f"zero clock wall {wall:.1f}")
        passed.append(f"explicit zero clock {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime -3000000000 btime 1000", 1)
        if best(lines) is None or wall > 40:
            fail(f"negative overflow clock wall {wall:.1f} {best(lines)}")
        passed.append(f"negative overflow clock {wall:.1f}ms")

        new_game("position startpos")
        engine.send("go wtime 3000000000 btime 3000000000")
        lines = engine.wait(lambda line: line.startswith("info depth ") or line.startswith("bestmove "), 0.25)
        if best(lines) is not None or not any(line.startswith("info depth ") for line in lines):
            fail(f"positive overflow clock treated as empty {lines[-3:]}")
        start = time.monotonic()
        engine.send("stop")
        stopped = engine.wait(lambda line: line.startswith("bestmove "), 1)
        latency = (time.monotonic() - start) * 1000.0
        if best(stopped) is None or latency > 200:
            fail(f"stop after overflow clock latency {latency:.1f}")
        passed.append(f"wtime above int max keeps searching; stop {latency:.1f}ms")

        new_game("position startpos moves e2e4")
        engine.send("go wtime 20 btime 3000000000")
        lines = engine.wait(lambda line: line.startswith("info depth ") or line.startswith("bestmove "), 0.25)
        if best(lines) is not None or not any(line.startswith("info depth ") for line in lines):
            fail(f"black overflow clock ignored {lines[-3:]}")
        engine.send("stop")
        if best(engine.wait(lambda line: line.startswith("bestmove "), 1)) is None:
            fail("stop after black overflow clock")
        passed.append("black clock above int max is not the opponent clock")

        new_game("position startpos")
        engine.send("go movetime 4000")
        engine.wait(lambda line: line.startswith("info depth "), 2)
        start = time.monotonic()
        engine.send("stop")
        stopped = engine.wait(lambda line: line.startswith("bestmove "), 1)
        latency = (time.monotonic() - start) * 1000.0
        moves = [line for line in stopped if line.startswith("bestmove ")]
        if len(moves) != 1 or latency > 100:
            fail(f"stop during movetime latency {latency:.1f} moves {moves}")
        passed.append(f"stop during movetime {latency:.1f}ms")

        new_game("position startpos")
        engine.send("go infinite")
        engine.wait(lambda line: line.startswith("info depth 2"), 2)
        time.sleep(0.04)
        early = engine.drain(0.01)
        if any(line.startswith("bestmove ") for line in early):
            fail("infinite published bestmove before stop")
        start = time.monotonic()
        engine.send("stop")
        stopped = engine.wait(lambda line: line.startswith("bestmove "), 1)
        latency = (time.monotonic() - start) * 1000.0
        if best(stopped) is None or latency > 100:
            fail(f"stop during infinite latency {latency:.1f}")
        passed.append(f"stop during infinite {latency:.1f}ms")

        engine.send("setoption name Ponder value true")
        engine.send("isready")
        engine.wait(lambda line: line == "readyok", 2)
        new_game("position startpos")
        engine.send("go ponder movetime 120")
        time.sleep(0.08)
        early = engine.drain(0.01)
        if any(line.startswith("bestmove ") for line in early):
            fail("ponder published bestmove before ponderhit")
        start = time.monotonic()
        engine.send("ponderhit")
        lines = engine.wait(lambda line: line.startswith("bestmove "), 1)
        after = (time.monotonic() - start) * 1000.0
        if best(lines) is None or not (60 <= after <= 200):
            fail(f"ponderhit movetime after {after:.1f}")
        passed.append(f"ponderhit starts the 120ms budget {after:.1f}ms")

        new_game("position startpos")
        engine.send("go ponder wtime 500 btime 500")
        time.sleep(0.04)
        start = time.monotonic()
        engine.send("stop")
        stopped = engine.wait(lambda line: line.startswith("bestmove "), 1)
        latency = (time.monotonic() - start) * 1000.0
        moves = [line for line in stopped if line.startswith("bestmove ")]
        if len(moves) != 1 or latency > 100:
            fail(f"stop while pondering {latency:.1f} {moves}")
        passed.append(f"stop while pondering {latency:.1f}ms")
        engine.send("setoption name Ponder value false")
        engine.send("isready")
        engine.wait(lambda line: line == "readyok", 2)

        new_game("position startpos")
        wall, lines = go("go movetime 70 wtime 4000 btime 4000", 1)
        if best(lines) is None or not (30 <= wall <= 110):
            fail(f"movetime did not override the clock wall {wall:.1f}")
        passed.append(f"movetime 70 overrides a 4000ms clock {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go depth 24 wtime 80 btime 80", 1)
        if best(lines) is None or wall > 130:
            fail(f"depth plus clock wall {wall:.1f}")
        passed.append(f"depth and clock {wall:.1f}ms")

        clock = 180
        for ply in range(4):
            engine.send("position startpos")
            start = time.monotonic()
            engine.send(f"go wtime {clock} btime {clock} winc 0 binc 0")
            lines = engine.wait(lambda line: line.startswith("bestmove "), 1)
            used = (time.monotonic() - start) * 1000.0
            if best(lines) is None or used > clock + 30:
                fail(f"forfeit ply {ply} clock {clock} used {used:.1f}")
            clock = int(clock - used)
        passed.append(f"four-ply clock stayed positive at {clock}ms")

        new_game("position startpos")
        for depth, expected in START_PERFT.items():
            engine.send(f"go perft {depth}")
            lines = engine.wait(lambda line: line.startswith("nodes "), 5)
            final = next(line for line in lines if line.startswith("nodes "))
            if final != f"nodes {expected}":
                fail(f"perft {depth} {final}")
            passed.append(f"perft {depth} {expected}")
            engine.drain()

        new_game("position startpos")
        wall, lines = go("go wtime 60 btime 3000000000", 1)
        if best(lines) is None or wall > 110:
            fail(f"opponent overflow changed the side to move wall {wall:.1f}")
        passed.append(f"white 60ms against an overflowing black clock {wall:.1f}ms")

        new_game("position startpos")
        wall, lines = go("go wtime 3000000000abc btime 1000", 1)
        if best(lines) is None or wall > 40:
            fail(f"trailing junk on a clock wall {wall:.1f}")
        passed.append(f"trailing junk clock stays explicit zero {wall:.1f}ms")

        new_game("position startpos")
        engine.send("go perft 6")
        time.sleep(0.05)
        start = time.monotonic()
        engine.send("isready")
        ready = engine.wait(lambda line: line == "readyok", 0.3)
        ready_latency = (time.monotonic() - start) * 1000.0
        if not any(line == "readyok" for line in ready) or ready_latency > 200:
            fail(f"isready blocked by perft {ready_latency:.1f}")
        if any(line == "nodes 119060324" for line in ready):
            fail("perft 6 finished before isready")
        start = time.monotonic()
        engine.send("stop")
        stopped = engine.wait(lambda line: line == "info string perft stopped" or line.startswith("nodes "), 1)
        stop_latency = (time.monotonic() - start) * 1000.0
        if not any(line == "info string perft stopped" for line in stopped):
            fail(f"perft stop missing {stopped[-4:]} latency {stop_latency:.1f}")
        if any(line == "nodes 119060324" for line in stopped):
            fail("perft stop still published the full count")
        if stop_latency > 500:
            fail(f"perft stop latency {stop_latency:.1f}")
        passed.append(f"perft 6 stop {stop_latency:.1f}ms ready {ready_latency:.1f}ms")
    finally:
        engine.close()
    print("PASS")
    for item in passed:
        print(" ", item)


if __name__ == "__main__":
    main()
