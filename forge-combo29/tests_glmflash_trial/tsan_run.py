#!/usr/bin/env python3
"""glmflash trial Step 4: drive ONE engine process through the TSan soak.

Protocol per run (from the job prompt):
  setoption name Threads value <threads>
  setoption name Hash value 16
  setoption name NNUEArchFile value <net file>
  setoption name NNUEArch value true
  isready                      -> wait for "readyok"
  for each position: position fen <FEN> ; go depth 8 -> wait for "bestmove"
  quit                         -> record exit code

The next command is only sent after the previous search has printed its
"bestmove", so no search is cut short by a queued command.

Engine stdout is teed verbatim to the log file; engine stderr (where
ThreadSanitizer writes its reports) is appended to the same log file by the
operating system, so the log is the raw combined output.

No TSAN_OPTIONS are set (no suppression file, defaults only).

Usage:
  python3 tsan_run.py --engine /tmp/glmflash/build-tsan/forge \
      --net /tmp/glmflash/net/glmflash_net.fnn3 \
      --positions <positions.txt> --threads 2 --out <log file> [--limit N]
"""

import argparse
import subprocess
import time
import select

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--positions", required=True)
    ap.add_argument("--threads", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--search-timeout", type=float, default=300.0,
                    help="seconds to wait for bestmove of one search")
    args = ap.parse_args()

    fens = [l.strip() for l in open(args.positions) if l.strip()][: args.limit]
    done = 0

    log = open(args.out, "wb", buffering=0)  # unbuffered; stderr shares this file
    proc = subprocess.Popen(
        [args.engine],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
        text=True, bufsize=1)

    def send(line: str) -> None:
        log.write(f">>> {line}\n".encode())
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def wait_for(token: str, timeout: float, what: str) -> bool:
        """Read engine stdout until `token`; tee every line to the log."""
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                log.write(f"### TIMEOUT waiting for {what!r} after {timeout}s\n".encode())
                return False
            ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 5.0))
            if not ready:
                continue
            line = proc.stdout.readline()
            if line == "":
                log.write(f"### ENGINE CLOSED stdout while waiting for {what!r}\n".encode())
                return False
            log.write(line.encode())
            if token in line:
                return True

    started = time.monotonic()
    try:
        send("uci")
        if not wait_for("uciok", 60, "uciok"):
            log.write(b"### ABORT: no uciok\n")
            return
        send(f"setoption name Threads value {args.threads}")
        send("setoption name Hash value 16")
        send(f"setoption name NNUEArchFile value {args.net}")
        send("setoption name NNUEArch value true")
        send("isready")
        if not wait_for("readyok", 120, "readyok"):
            log.write(b"### ABORT: engine not ready\n")
            return
        for i, fen in enumerate(fens, 1):
            send(f"position fen {fen}")
            send("go depth 8")
            if not wait_for("bestmove", args.search_timeout, f"bestmove (position {i})"):
                log.write(f"### ABORT at position {i}: {fen}\n".encode())
                break
            done = i
        log.write(f"### positions searched: {done} of {len(fens)}\n".encode())
        send("quit")
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            log.write(b"### engine did not exit after quit; killed\n")
        elapsed = time.monotonic() - started
        log.write(f"### exit code: {proc.returncode}\n".encode())
        log.write(f"### wall seconds: {elapsed:.1f}\n".encode())
        log.write(f"### engine: {args.engine} threads={args.threads} net={args.net}\n".encode())
        log.write(f"### positions searched: {done} of {len(fens)}\n".encode())
        log.close()
        print(f"run threads={args.threads} exit={proc.returncode} wall={elapsed:.1f}s")

if __name__ == "__main__":
    main()
