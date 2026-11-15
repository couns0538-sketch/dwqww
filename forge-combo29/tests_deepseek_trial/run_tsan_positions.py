#!/usr/bin/env python3
"""Step 4 of the deepseek trial: drive one engine process through one TSan run.

The job requires that every `go depth 8` is allowed to finish before the next
`position` line is sent ("wait for the line bestmove"). This driver therefore
reads stdout line by line through a pipe and blocks on `bestmove` (or on a
hard timeout) instead of writing all commands at once.

stdout and stderr are kept in separate files, so the ThreadSanitizer reports
(which go to stderr) are not mixed with the engine's search output.

Usage:
  run_tsan_positions.py <engine> <net> <positions.txt> <threads> <depth>
                        <stdout.log> <stderr.log> [first] [count]

Exit status: 0 if every position reached bestmove, 3 if the engine died or a
search timed out (the logs say which position).
"""
import subprocess
import sys
import time

SEARCH_TIMEOUT_S = 300.0
STARTUP_TIMEOUT_S = 60.0


def read_until(proc, needle, timeout, out_log, tag):
    """Read stdout lines until one starts with `needle`. Returns that line or None."""
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        line = proc.stdout.readline()
        if not line:
            return None
        out_log.write(line)
        out_log.flush()
        if line.startswith(needle):
            return line.rstrip("\n")


def main():
    (engine, net, positions_file, threads, depth, stdout_path, stderr_path) = sys.argv[1:8]
    first = int(sys.argv[8]) if len(sys.argv) > 8 else 0
    count = int(sys.argv[9]) if len(sys.argv) > 9 else None
    threads = int(threads)
    depth = int(depth)

    with open(positions_file) as f:
        fens = [line.strip() for line in f if line.strip()]
    fens = fens[first:] if count is None else fens[first:first + count]

    err_log = open(stderr_path, "w")
    proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=err_log, text=True, bufsize=1)

    started = time.monotonic()
    ok = True
    with open(stdout_path, "w") as out_log:
        for command in (f"setoption name Threads value {threads}",
                        "setoption name Hash value 16",
                        f"setoption name NNUEArchFile value {net}",
                        "setoption name NNUEArch value true"):
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
        proc.stdin.write("isready\n")
        proc.stdin.flush()
        if read_until(proc, "readyok", STARTUP_TIMEOUT_S, out_log, "isready") is None:
            print("FAIL: no readyok", flush=True)
            ok = False

        searched = 0
        for index, fen in enumerate(fens):
            proc.stdin.write(f"position fen {fen}\n")
            proc.stdin.write(f"go depth {depth}\n")
            proc.stdin.flush()
            line = read_until(proc, "bestmove", SEARCH_TIMEOUT_S, out_log, f"position {index}")
            if line is None:
                print(f"FAIL: no bestmove for position {index} (threads {threads}): {fen}", flush=True)
                ok = False
                break
            searched += 1
            if (index + 1) % 25 == 0:
                print(f"  threads {threads}: {index + 1}/{len(fens)} positions, "
                      f"{time.monotonic() - started:.1f}s", flush=True)

        proc.stdin.write("quit\n")
        proc.stdin.flush()
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print("FAIL: engine did not quit", flush=True)
            ok = False
        code = proc.returncode
        err_log.close()
        elapsed = time.monotonic() - started
        print(f"threads {threads} depth {depth}: searched {searched}/{len(fens)} positions, "
              f"exit code {code}, {elapsed:.1f}s", flush=True)
        if code != 0:
            ok = False
        if not ok:
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
