#!/usr/bin/env python3
"""UCI protocol checks for the built forge binary.

Covers an illegal move inside `position` and `stop` during `go perft`.
A script that sends `quit` in the same burst as `go perft` must still receive
the finished node count: existing pin scripts do that.
"""
import queue
import subprocess
import sys
import threading
import time


def launch(exe):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    proc.lines = queue.Queue()

    def pump():
        for line in proc.stdout:
            proc.lines.put(line.rstrip("\n"))
        proc.lines.put(None)

    proc.pump = threading.Thread(target=pump, daemon=True)
    proc.pump.start()
    return proc


def send(proc, line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_until(proc, predicate, timeout):
    lines = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            line = proc.lines.get(timeout=0.05)
        except queue.Empty:
            if proc.poll() is not None and proc.lines.empty():
                break
            continue
        if line is None:
            break
        lines.append(line)
        if predicate(line):
            return lines, True
    return lines, False


def close(proc):
    if proc.poll() is None:
        try:
            send(proc, "quit")
        except BrokenPipeError:
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def fail(message):
    print("FAIL:", message)
    return 1


def bestmove(lines):
    for line in reversed(lines):
        if line.startswith("bestmove "):
            return line.split()[1]
    return None


def test_illegal_move(exe):
    proc = launch(exe)
    send(proc, "uci")
    send(proc, "setoption name OwnBook value false")
    send(proc, "setoption name UseNNUE value false")
    send(proc, "isready")
    send(proc, "ucinewgame")
    send(proc, "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    send(proc, "go depth 2")
    lines, ok = read_until(proc, lambda line: line.startswith("bestmove "), 10)
    if not ok or bestmove(lines) != "0000":
        close(proc)
        return fail("checkmate did not answer bestmove 0000: " + " | ".join(lines[-4:]))
    send(proc, "position startpos moves NOTAMOVE")
    send(proc, "go depth 1")
    lines, ok = read_until(proc, lambda line: line.startswith("bestmove "), 10)
    close(proc)
    move = bestmove(lines)
    illegal = any(line == "info string illegal move NOTAMOVE" for line in lines)
    if not ok or not illegal or move in (None, "0000"):
        return fail("illegal move did not keep startpos: " + " | ".join(lines[-6:]))
    print("illegal-move bestmove", move)
    return 0


def test_position_extra_token(exe):
    proc = launch(exe)
    for line in (
        "uci",
        "setoption name OwnBook value false",
        "setoption name UseNNUE value false",
        "isready",
        "ucinewgame",
        "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
        "position startpos extra",
        "go depth 1",
    ):
        send(proc, line)
    lines, ok = read_until(proc, lambda line: line.startswith("bestmove "), 10)
    move = bestmove(lines)
    if not ok or move in (None, "0000"):
        close(proc)
        return fail("position startpos extra stayed in checkmate: " + " | ".join(lines[-4:]))
    send(proc, "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    send(proc, "position startpos extra moves e2e4")
    send(proc, "go depth 1")
    lines, ok = read_until(proc, lambda line: line.startswith("bestmove "), 10)
    close(proc)
    move = bestmove(lines)
    # After 1.e4 it is Black to move, so the piece starts on rank 7 or 8.
    if not ok or move is None or len(move) < 4 or move[1] not in "78":
        return fail("extra token swallowed the move list: " + " | ".join(lines[-4:]))
    print("position extra token bestmove", move)
    return 0


def test_scripted_perft(exe):
    # quit is already in the pipe when perft starts. The count must finish.
    text = "position startpos\ngo perft 5\nquit\n"
    proc = subprocess.run([exe], input=text, capture_output=True, text=True, timeout=30)
    if "nodes 4865609" not in proc.stdout.splitlines():
        print(proc.stdout[-400:])
        return fail("scripted perft+quit lost the node count, exit " + str(proc.returncode))
    print("scripted perft nodes 4865609")
    return 0


def test_perft_stop(exe):
    proc = launch(exe)
    send(proc, "position startpos")
    send(proc, "go perft 8")
    early, early_stopped = read_until(proc, lambda line: line == "info string perft stopped", 0.3)
    if early_stopped:
        close(proc)
        return fail("perft aborted before stop: " + " | ".join(early[-4:]))
    started = time.monotonic()
    send(proc, "stop")
    lines, ok = read_until(proc, lambda line: line == "info string perft stopped", 2)
    elapsed = time.monotonic() - started
    alive = proc.poll() is None
    close(proc)
    if not ok or not alive or elapsed >= 2:
        return fail(f"perft stop elapsed={elapsed:.3f}s alive_before_quit={alive} lines={lines[-4:]}")
    print(f"perft stop in {elapsed:.3f}s")
    return 0


def main():
    if len(sys.argv) != 2:
        print("usage: uci_protocol_tests.py <forge>", file=sys.stderr)
        return 2
    exe = sys.argv[1]
    status = 0
    status |= test_illegal_move(exe)
    status |= test_position_extra_token(exe)
    status |= test_scripted_perft(exe)
    status |= test_perft_stop(exe)
    print("uci protocol failures=" + str(status))
    return status


if __name__ == "__main__":
    sys.exit(main())
