#!/usr/bin/env python3
"""One engine, S14-style options, then ucinewgame and a fixed-depth go per position.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the engine's stdout, stderr, and a .meta file.
"""
import argparse
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fen_of(line):
    parts = line.split()
    if len(parts) < 4 or parts[1] not in ("w", "b"):
        raise SystemExit(f"bad position line: {line}")
    if len(parts) >= 6:
        try:
            int(parts[4])
            int(parts[5])
            return " ".join(parts[:6])
        except ValueError:
            return " ".join(parts[:4])
    return " ".join(parts[:4])


def load_positions(path, limit):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(fen_of(line))
        if limit and len(rows) >= limit:
            break
    return rows


def load_options(paths):
    lines = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--options", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--ready-timeout", type=float, default=60)
    parser.add_argument("--go-timeout", type=float, default=180)
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    positions = load_positions(args.positions, args.limit)
    option_lines = load_options(args.options)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    id_proc = subprocess.run(
        [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60, check=False
    )
    id_name = "MISSING"
    for line in id_proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break

    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    lines = queue.Queue()

    def pump(stream):
        for line in stream:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, args=(proc.stdout,), daemon=True).start()
    err_box = []

    def pump_err():
        err_box.extend(proc.stderr.readlines())

    threading.Thread(target=pump_err, daemon=True).start()

    engine_out = []
    sent = []

    def fail(message):
        out_path = Path(args.out)
        out_path.write_text("".join(engine_out))
        Path(str(out_path) + ".err").write_text("".join(err_box))
        Path(str(out_path) + ".sent").write_text("\n".join(sent) + "\n")
        print(message, file=sys.stderr)
        proc.kill()
        sys.exit(1)

    def send(line):
        if proc.poll() is not None:
            fail(f"engine exited before {line}")
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        sent.append(line)

    def read_until(predicate, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                fail("timeout waiting for engine")
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                fail("timeout waiting for engine")
            if line is None:
                fail("engine closed stdout")
            engine_out.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    fail(f"STOP {line.rstrip()}")
            if predicate(line):
                return

    for option in option_lines:
        send(option)
        send("isready")
        read_until(lambda line: line.strip() == "readyok", args.ready_timeout)

    for index, fen in enumerate(positions, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line.strip() == "readyok", args.ready_timeout)
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line.strip() == "readyok", args.ready_timeout)
        send(f"go depth {args.depth}")
        read_until(lambda line: line.startswith("bestmove "), args.go_timeout)
        print(f"done {index}/{len(positions)}", flush=True)

    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(engine_out))
    Path(str(out_path) + ".err").write_text("".join(err_box))
    Path(str(out_path) + ".sent").write_text("\n".join(sent) + "\n")
    meta = (
        f"exe {exe}\n"
        f"sha256 {sha}\n"
        f"id name {id_name}\n"
        f"depth {args.depth}\n"
        f"positions {args.positions}\n"
        f"count {len(positions)}\n"
        "options\n"
        + "\n".join(option_lines)
        + "\n"
    )
    Path(str(out_path) + ".meta").write_text(meta)
    print(f"wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
