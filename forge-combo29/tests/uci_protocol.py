#!/usr/bin/env python3
"""Interactive UCI checks. A command that starts a search is not followed by quit
until bestmove has been read: quit stops the search, and an aborted search is not
evidence about the move the engine would have played.
"""

import queue
import subprocess
import sys
import threading
import time


START_MOVES = {
    "a2a3", "a2a4", "b2b3", "b2b4", "c2c3", "c2c4", "d2d3", "d2d4",
    "e2e3", "e2e4", "f2f3", "f2f4", "g2g3", "g2g4", "h2h3", "h2h4",
    "b1a3", "b1c3", "g1f3", "g1h3",
}
# After 1.e4 e5 the side to move is White. Used to tell a rejected 4-field FEN
# (the previous position was stalemate, bestmove 0000) from a real position.
OPEN_GAME_MOVES = {
    "a2a3", "a2a4", "b2b3", "b2b4", "c2c3", "c2c4", "d2d3", "d2d4",
    "f2f3", "f2f4", "g2g3", "g2g4", "h2h3", "h2h4", "g1f3", "g1h3", "g1e2",
    "b1c3", "b1a3", "f1c4", "f1b5", "f1a6", "f1e2", "f1d3", "d1h5", "d1f3",
    "d1g4", "d1e2", "e1e2",
}
# Oracle in engine_checks: Qg7 is the only mate in one.
MATE_MOVES = {"f6g7"}
PROMO_MATE_MOVES = {"f7f8q", "f7f8r"}
# Black king on h1, white queen on a8, white king on a1.
AFTER_PROMO = {"h1g1", "h1h2"}


class ProtocolError(Exception):
    pass


class Uci:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1)
        self.lines = queue.Queue()
        self.collected = []
        thread = threading.Thread(target=self._read, daemon=True)
        thread.start()

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.lines.put(None)

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_for(self, seconds):
        lines = []
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            lines.append(line)
            self.collected.append(line)
        return lines

    def read_until(self, predicate, timeout):
        lines = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            lines.append(line)
            self.collected.append(line)
            if predicate(line):
                return lines
        raise ProtocolError("timed out after:\n" + "\n".join(lines[-30:]))

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def bestmove_of(lines):
    for line in lines:
        if line.startswith("bestmove "):
            return line.split()[1]
    raise ProtocolError("no bestmove in:\n" + "\n".join(lines))


def main():
    if len(sys.argv) != 2:
        print("usage: uci_protocol.py <forge>", file=sys.stderr)
        return 2
    engine = Uci(sys.argv[1])
    failures = 0

    def check(condition, what):
        nonlocal failures
        if condition:
            print("ok", what)
        else:
            failures += 1
            print("FAIL", what)

    try:
        engine.send("uci")
        ident = engine.read_until(lambda line: line == "uciok", 3)
        text = "\n".join(ident)
        check("option name UseNNUE" in text, "uci lists UseNNUE")
        check("option name Ponder" in text, "uci lists Ponder")
        check("option name OwnBook" in text, "uci lists OwnBook")
        check("option name Hash" in text, "uci lists Hash")

        engine.send("isready")
        engine.read_until(lambda line: line == "readyok", 3)

        # Lowercase option names are required by the UCI spec. The bench pins
        # tell UseNNUE apart: depth 11 is 312866 with the net and 375354 without.
        engine.send("setoption name usennue value false")
        engine.send("isready")
        engine.read_until(lambda line: line == "readyok", 3)
        engine.send("bench 11")
        bench = engine.read_until(lambda line: line.startswith("info string bench"), 30)
        check(any("nodes 375354" in line for line in bench), "lowercase UseNNUE false -> net-off bench 11: " + " | ".join(bench))

        engine.send("setoption name UseNNUE value True")
        engine.send("isready")
        engine.read_until(lambda line: line == "readyok", 3)
        engine.send("bench 11")
        bench = engine.read_until(lambda line: line.startswith("info string bench"), 30)
        check(any("nodes 312866" in line for line in bench), "UseNNUE True -> net-on bench 11: " + " | ".join(bench))

        engine.send("setoption name UseNNUE value yes")
        invalid = engine.read_for(0.3)
        check(any("invalid value for option UseNNUE" in line for line in invalid), "rejected checkbox 'yes'")

        engine.send("setoption name hash value 32")
        engine.send("isready")
        ready = engine.read_until(lambda line: line == "readyok", 3)
        check(not any(line.startswith("info string invalid") for line in ready), "lowercase Hash is accepted")

        # Book Variety defaults to 30, and the book then picks a weighted random
        # move among the near-best entries. Variety 0 returns the single highest
        # weight, which for the embedded start position is e2e4.
        engine.send("setoption name Book Variety value 0")
        engine.send("position startpos")
        engine.send("go movetime 80")
        booked = engine.read_until(lambda line: line.startswith("bestmove "), 3)
        check(any("book move e2e4" in line for line in booked), "variety 0 book plays e2e4: " + " | ".join(booked))
        check(bestmove_of(booked) == "e2e4", "book bestmove e2e4")

        engine.send("setoption name OwnBook value False")
        engine.send("position startpos")
        engine.send("go movetime 80")
        searched = engine.read_until(lambda line: line.startswith("bestmove "), 3)
        check(not any("book move" in line for line in searched), "OwnBook False is accepted: " + " | ".join(searched))
        check(bestmove_of(searched) in START_MOVES, "book-off bestmove is legal: " + bestmove_of(searched))

        engine.send("setoption name ownbook value false")
        engine.send("position startpos")
        engine.send("go depth 1")
        depth = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(not any("book move" in line for line in depth), "lowercase ownbook stays off")
        check(bestmove_of(depth) in START_MOVES, "depth 1 bestmove is legal: " + bestmove_of(depth))
        check(any(line.startswith("info depth ") for line in depth), "depth 1 emits an info line before bestmove")

        engine.send("stop")
        stopped = engine.read_for(0.3)
        check(not any(line.startswith("bestmove") for line in stopped), "stop with no search prints nothing")
        engine.send("isready")
        engine.read_until(lambda line: line == "readyok", 3)

        # A four-field FEN used to swallow the word "moves". The board is first
        # set to a stalemate, so a rejected FEN would answer 0000.
        engine.send("position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        engine.send("position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 moves e7e5")
        engine.send("go depth 1")
        four = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(not any("invalid FEN" in line for line in four), "four-field FEN accepted: " + " | ".join(four))
        check(bestmove_of(four) in OPEN_GAME_MOVES, "position after e4 e5, got " + bestmove_of(four))

        engine.send("position fen 8/P7/8/8/8/8/8/K6k w - - 0 1 moves a7a8Q")
        engine.send("go depth 1")
        promo = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(not any("illegal move" in line for line in promo), "a7a8Q accepted: " + " | ".join(promo))
        check(bestmove_of(promo) in AFTER_PROMO, "side to move is Black after a7a8Q, got " + bestmove_of(promo))

        engine.send("position startpos moves E2E4")
        engine.send("go depth 1")
        upper = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        move = bestmove_of(upper)
        check(not any("illegal move" in line for line in upper) and len(move) == 4 and move[1] in "78",
              "E2E4 leaves Black to move, got " + move)

        engine.send("position startpos")
        engine.send("go depth 1 searchmoves h7h5 a7a6")
        restricted = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(any("no legal root moves" in line for line in restricted), "empty searchmoves is reported")
        check(bestmove_of(restricted) in START_MOVES, "empty searchmoves is not 0000, got " + bestmove_of(restricted))

        engine.send("position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        engine.send("go depth 1")
        stale = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(bestmove_of(stale) == "0000", "stalemate bestmove 0000")
        check(any("score cp 0" in line for line in stale), "stalemate score 0")

        engine.send("position fen 6k1/8/5QK1/8/8/8/8/8 w - - 0 1")
        engine.send("go depth 3")
        mate = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(bestmove_of(mate) in MATE_MOVES, "mate in one, got " + bestmove_of(mate) + " | " + " | ".join(mate[-4:]))

        engine.send("position fen 7k/5P2/6K1/8/8/8/8/8 w - - 0 1")
        engine.send("go depth 3")
        promo_mate = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(bestmove_of(promo_mate) in PROMO_MATE_MOVES,
              "promotion mate, got " + bestmove_of(promo_mate))

        engine.send("setoption name ponder value true")
        engine.send("position startpos")
        engine.send("go depth 3")
        ponder = engine.read_until(lambda line: line.startswith("bestmove "), 8)
        ponder_line = next(line for line in ponder if line.startswith("bestmove "))
        parts = ponder_line.split()
        check(len(parts) == 4 and parts[2] == "ponder" and len(parts[3]) == 4 and parts[1] in START_MOVES,
              "ponder move appended: " + ponder_line)

        engine.send("position startpos")
        engine.send("go ponder depth 3")
        early = engine.read_for(0.4)
        check(not any(line.startswith("bestmove") for line in early),
              "go ponder holds bestmove until ponderhit: " + " | ".join(early[-4:]))
        engine.send("ponderhit")
        released = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        check(bestmove_of(released) in START_MOVES, "ponderhit releases a legal move " + bestmove_of(released))

        engine.send("position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        started = time.monotonic()
        engine.send("go wtime 120000 btime 60")
        timed = engine.read_until(lambda line: line.startswith("bestmove "), 3)
        elapsed = time.monotonic() - started
        black = bestmove_of(timed)
        check(elapsed < 2.0 and len(black) == 4 and black[1] in "78",
              "black clock is the one that is used, elapsed %.2fs move %s" % (elapsed, black))

        engine.send("position fen 8/8/8/8/8/8/8/K6k w - - 0 1")
        engine.send("go depth 1")
        quiet = engine.read_until(lambda line: line.startswith("bestmove "), 5)
        # Not a claim about the move, only that a finished search does not print 0000.
        check(bestmove_of(quiet) != "0000", "KvK with a legal move does not play 0000")

        engine.send("quit")
        engine.proc.wait(timeout=3)
        check(engine.proc.returncode == 0, "quit exits")
    except (ProtocolError, subprocess.TimeoutExpired, BrokenPipeError) as exc:
        failures += 1
        print("FAIL", exc)
    finally:
        engine.close()

    print("uci_protocol failures", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
