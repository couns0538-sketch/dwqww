#!/usr/bin/env python3
"""Depth search over a FEN list. S14, then Threads 1, Hash 16, then an optional check.

One engine process. ucinewgame + isready before every go. isready after every
setoption and every position. Stops on unknown option, invalid value, invalid
FEN, or illegal move. Writes the engine's stdout and stderr unchanged.
"""
import argparse
import queue
import subprocess
import threading
from pathlib import Path

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
        if limit and len(fens) >= limit:
            break
    return fens


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--err", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--check", default="", help="check option name to send after S14")
    parser.add_argument("--check-value", default="false")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    exe = str(Path(args.exe).resolve())
    fens = load_fens(Path(args.fens), args.limit)
    options = list(S14)
    if args.check:
        if args.check_value not in ("true", "false"):
            raise SystemExit(f"check value must be true or false, got {args.check_value}")
        options.append(f"setoption name {args.check} value {args.check_value}")

    sha = subprocess.check_output(["sha256sum", exe], text=True).split()[0]
    id_probe = subprocess.run([exe], input="uci\nquit\n", text=True, capture_output=True, check=False)
    id_name = ""
    for line in id_probe.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line
            break

    meta_lines = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"depth={args.depth}",
        f"fens={Path(args.fens).resolve()}",
        f"fen_count={len(fens)}",
        "options_sent:",
        *options,
    ]
    Path(args.meta).write_text("\n".join(meta_lines) + "\n")

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    out_q: queue.Queue[str | None] = queue.Queue()
    err_chunks: list[str] = []

    def read_out() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            out_q.put(line)
        out_q.put(None)

    def read_err() -> None:
        assert proc.stderr is not None
        err_chunks.append(proc.stderr.read())

    threading.Thread(target=read_out, daemon=True).start()
    threading.Thread(target=read_err, daemon=True).start()
    raw: list[str] = []
    failed = False

    def send(cmd: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def take_until(kind: str, timeout: float) -> None:
        nonlocal failed
        while True:
            try:
                line = out_q.get(timeout=timeout)
            except queue.Empty:
                failed = True
                raw.append(f"HARNESS TIMEOUT waiting for {kind}\n")
                return
            if line is None:
                failed = True
                raw.append(f"HARNESS EOF waiting for {kind}\n")
                return
            raw.append(line)
            if any(bit in line for bit in STOP_BITS):
                failed = True
                return
            if kind == "readyok" and line.strip() == "readyok":
                return
            if kind == "bestmove" and line.startswith("bestmove "):
                return

    for opt in options:
        send(opt)
        send("isready")
        take_until("readyok", args.timeout)
        if failed:
            break

    if not failed:
        for fen in fens:
            send("ucinewgame")
            send("isready")
            take_until("readyok", args.timeout)
            if failed:
                break
            send("position fen " + fen)
            send("isready")
            take_until("readyok", args.timeout)
            if failed:
                break
            send(f"go depth {args.depth}")
            take_until("bestmove", args.timeout)
            if failed:
                break

    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    Path(args.out).write_text("".join(raw))
    Path(args.err).write_text("".join(err_chunks))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
