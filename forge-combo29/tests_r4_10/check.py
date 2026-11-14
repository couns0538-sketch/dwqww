#!/usr/bin/env python3
"""Finding 10: setoption values that contain spaces or the word "value".

Drives the engine over UCI. Book File and NnueFile must keep the value text,
including repeated spaces, tabs, and the token "value". Pins 312866, 862329,
and 4865609 must hold. Two hundred depth-10 searches must each return a move
from that position's legal list. The binary must be linked with AddressSanitizer
and UndefinedBehaviorSanitizer. Any failed check exits non-zero.
"""

import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

MASK = (1 << 64) - 1
PINS = (312866, 862329, 4865609)

SEEDS = (
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4",
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    "2rq1rk1/pb1nbppp/1p2pn2/2pp4/3P4/1PN1PN2/PB1NBPPP/2RQ1RK1 w - - 0 10",
    "r2qkb1r/pp2pppp/2n2n2/3p1b2/3P1B2/2N2N2/PP2PPPP/R2QKB1R w KQkq - 4 6",
    "8/5pk1/4p1p1/3pP1P1/3P4/5K2/8/8 w - - 0 1",
    "8/8/2k5/4b3/8/3N4/4K3/8 w - - 0 1",
    "4r1k1/p1p2ppp/1p6/3p4/3P4/1P2R3/P1P2PPP/6K1 w - - 0 1",
    "r4rk1/pp1b1ppp/2n1p3/q2pP3/3P4/P1PB1N2/2Q2PPP/R3K2R w KQ - 1 13",
    "r1b1k2r/pp1n1ppp/2pbpn2/q7/1b1PP3/2NB1N2/PPQ2PPP/R1B1K2R w KQkq - 4 8",
    "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 8",
    "3r2k1/pp3ppp/2n1b3/8/3p4/1B3N2/PP3PPP/3R2K1 w - - 0 1",
    "2kr3r/ppp2ppp/2n1b3/3q4/3P4/2PB1N2/P4PPP/R2Q1RK1 w - - 0 12",
    "8/1p4k1/p1p2pp1/2P5/1P1R4/P5P1/5PK1/3r4 w - - 0 1",
    "r1b2rk1/ppq1bppp/2n1pn2/2pp4/3P4/1PN1PN2/PB1PBPPP/R2Q1RK1 w - - 4 9",
)


class Fail(Exception):
    pass


def fail(message):
    raise Fail(message)


class Engine:
    def __init__(self, path):
        os.environ["ASAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:detect_leaks=1"
        os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:print_stacktrace=1"
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stdout_queue = queue.Queue()
        self.stderr_lines = []
        self.stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()

    def _read_stdout(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.stdout_queue.put(line)
        self.stdout_queue.put(None)

    def _read_stderr(self):
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr_lines.append(line)

    def send(self, line):
        if self.proc.poll() is not None:
            fail(f"engine exited {self.proc.returncode} before: {line}")
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def readline(self, timeout):
        try:
            line = self.stdout_queue.get(timeout=timeout)
        except queue.Empty:
            fail(f"timed out after {timeout}s; stderr={self.stderr_text()}")
        if line is None:
            fail(f"engine closed stdout; stderr={self.stderr_text()}")
        return line.rstrip("\r\n")

    def exchange(self, line, timeout=60):
        self.send(line)
        self.send("isready")
        rows = []
        while True:
            row = self.readline(timeout)
            if row == "readyok":
                return rows
            rows.append(row)

    def stderr_text(self):
        return "".join(self.stderr_lines).strip()

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except Fail:
                self.proc.kill()
            try:
                self.proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
        self.stderr_thread.join(timeout=2)
        return self.proc.returncode


def require_sanitizers(engine_path):
    linked = subprocess.check_output(["ldd", engine_path], text=True)
    if "libasan" not in linked:
        fail("engine is not linked with AddressSanitizer")
    if "libubsan" not in linked:
        fail("engine is not linked with UndefinedBehaviorSanitizer")
    print("sanitizers: address and undefined")


def write_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def expect_exact(engine, command, expected, timeout=30):
    got = engine.exchange(command, timeout=timeout)
    if got != expected:
        fail(f"command {command!r}\n expected {expected!r}\n got {got!r}")
    print(f"ok {expected[0] if expected else '(no diagnostic)'}")


def quiet(engine, command):
    got = engine.exchange(command)
    bad = [row for row in got if row.startswith("info string ")]
    if bad:
        fail(f"command {command!r} printed {bad!r}")
    print(f"ok quiet {command}")


def check_string_options(engine):
    root = Path(tempfile.mkdtemp(prefix="r4_10_"))
    directory = root / "book dir"
    three = directory / "my   book.bin"
    two = directory / "a  b.bin"
    value_token = directory / "value book.bin"
    value_word = directory / "my value.bin"
    value_gaps = directory / "a  value  b.bin"
    value_twice = directory / "value value.bin"
    bar_value = directory / "Bar value Baz"
    tabbed = directory / "tab\tname.bin"
    plain = directory / "plain.bin"
    collapsed = directory / "my book.bin"
    nnue = directory / "nnue value.bin"
    for path in (three, two, value_token, value_word, value_gaps, value_twice, bar_value, tabbed, plain):
        write_bytes(path, b"\x00" * 16)
    write_bytes(nnue, b"FORGENET")
    if collapsed.exists():
        fail("negative-control book path must not exist")

    cases = (
        three,
        two,
        value_token,
        value_word,
        value_gaps,
        value_twice,
        bar_value,
        tabbed,
    )
    for path in cases:
        expect_exact(
            engine,
            f"setoption name Book File value {path}",
            [f"info string loaded book {path} with 1 entries"],
        )
    expect_exact(
        engine,
        f"setoption name Book File value {three}   ",
        [f"info string loaded book {three} with 1 entries"],
    )
    expect_exact(
        engine,
        f"setoption name Book File value   {plain}",
        [f"info string loaded book {plain} with 1 entries"],
    )
    expect_exact(
        engine,
        f"setoption name Book File value {collapsed}",
        [f"info string cannot load book {collapsed}"],
    )
    expect_exact(
        engine,
        f"setoption name NnueFile value {nnue}",
        ["info string nnue: wrong size"],
    )
    expect_exact(engine, "setoption name Book File value <empty>", [])
    expect_exact(engine, "setoption name NnueFile value <empty>", [])
    for command in (
        "setoption name Hash value 16",
        "setoption name Threads value 1",
        "setoption name Move Overhead value 10",
        "setoption name OwnBook value false",
        "setoption name Ponder value false",
        "setoption name Clear Hash",
    ):
        quiet(engine, command)
    expect_exact(
        engine,
        "setoption name Not A Real Option value 1",
        ["info string unknown option Not A Real Option"],
    )
    print(f"PASS setoption spaces and value ({root})")
    return root


def bench_nodes(engine, depth):
    rows = engine.exchange(f"bench {depth}", timeout=180)
    prefix = f"info string bench depth {depth} nodes "
    matches = [row for row in rows if row.startswith(prefix)]
    if len(matches) != 1:
        fail(f"bench {depth} output {rows!r}")
    fields = matches[0].split()
    try:
        nodes_at = fields.index("nodes")
        return int(fields[nodes_at + 1])
    except (ValueError, IndexError) as error:
        fail(f"bench {depth} line {matches[0]!r} ({error})")


def perft_nodes(engine, depth):
    engine.exchange("position startpos")
    rows = engine.exchange(f"go perft {depth}", timeout=180)
    nodes = [row for row in rows if row.startswith("nodes ")]
    if len(nodes) != 1:
        fail(f"perft {depth} output {rows!r}")
    return int(nodes[0].split()[1])


def check_pins(engine):
    got = (bench_nodes(engine, 11), bench_nodes(engine, 13), perft_nodes(engine, 5))
    print(f"pins {got[0]} {got[1]} {got[2]}")
    if got != PINS:
        fail(f"pin mismatch got {got} want {PINS}")
    print("PASS pins 312866 862329 4865609")


def next_u64(state):
    state[0] ^= (state[0] >> 12) & MASK
    state[0] = (state[0] ^ ((state[0] << 25) & MASK)) & MASK
    state[0] ^= (state[0] >> 27) & MASK
    state[0] = (state[0] * 0x2545F4914F6CDD1D) & MASK
    return state[0]


def position_command(fen, moves):
    command = f"position fen {fen}"
    if moves:
        command += " moves " + " ".join(moves)
    return command


def legal_moves(engine, fen, moves):
    rows = engine.exchange(position_command(fen, moves), timeout=30)
    if any(row.startswith("info string ") for row in rows):
        fail(f"position rejected {fen} {moves}: {rows}")
    rows = engine.exchange("go perft 1", timeout=30)
    found = []
    total = None
    for row in rows:
        if row.startswith("nodes "):
            total = int(row.split()[1])
        elif ": " in row:
            move, count = row.split(": ", 1)
            if count != "1":
                fail(f"perft 1 count {row}")
            found.append(move)
    if total != len(found):
        fail(f"perft 1 nodes {total} listed {len(found)} for {fen} {moves}")
    return found


def build_positions(engine):
    positions = []
    state = [0x9E3779B97F4A7C15]
    for fen in SEEDS:
        moves = []
        for _step in range(8):
            if len(positions) >= 200:
                return positions
            legal = legal_moves(engine, fen, moves)
            if not legal:
                break
            positions.append((fen, list(moves)))
            moves.append(legal[next_u64(state) % len(legal)])
    if len(positions) < 200:
        fail(f"only gathered {len(positions)} positions")
    return positions


def check_searches(engine):
    positions = build_positions(engine)
    if len(positions) != 200:
        fail(f"expected 200 positions, got {len(positions)}")
    started = time.monotonic()
    for index, (fen, moves) in enumerate(positions, start=1):
        legal = legal_moves(engine, fen, moves)
        if not legal:
            fail(f"search {index} has no legal move")
        engine.send("go depth 10")
        best = None
        while True:
            row = engine.readline(90)
            if row.startswith("bestmove "):
                parts = row.split()
                if len(parts) < 2:
                    fail(f"search {index} bad bestmove line {row!r}")
                best = parts[1]
                break
        if best not in legal:
            fail(f"search {index} bestmove {best} not in {legal} fen {fen} moves {moves}")
        if index == 1 or index == 200 or index % 25 == 0:
            print(f"search {index} bestmove {best} legal {len(legal)}")
    elapsed = time.monotonic() - started
    print(f"PASS 200 depth-10 searches legal in {elapsed:.1f}s")


def main():
    if len(sys.argv) != 2:
        print("usage: check.py /path/to/forge", file=sys.stderr)
        return 2
    engine_path = sys.argv[1]
    try:
        require_sanitizers(engine_path)
        engine = Engine(engine_path)
    except Fail as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    code = 1
    try:
        rows = engine.exchange("uci", timeout=30)
        if "uciok" not in rows:
            fail(f"uci did not answer uciok: {rows!r}")
        check_string_options(engine)
        check_pins(engine)
        check_searches(engine)
        code_after = engine.close()
        if code_after != 0:
            fail(f"engine exit {code_after}; stderr={engine.stderr_text()}")
        if engine.stderr_text():
            fail(f"sanitizer or engine stderr: {engine.stderr_text()}")
        print("PASS r4-10")
        code = 0
    except Fail as error:
        print(f"FAIL {error}", file=sys.stderr)
        print(engine.stderr_text(), file=sys.stderr)
        engine.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
