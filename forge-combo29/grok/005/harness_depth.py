#!/usr/bin/env python3
"""Depth-node harness.

One engine process. After every setoption and every position command, sends
isready and reads every line up to readyok. Stops on unknown option, invalid
value, invalid FEN, or illegal move.

Usage:
  harness_depth.py EXE FENS DEPTH OUT.txt SWITCH
SWITCH is none, false, or true. none does not send IdeaS37.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


LOG: list[str] = []
OUT_PATH: Path | None = None


def die(message: str) -> None:
    if OUT_PATH is not None:
        OUT_PATH.write_text("".join(LOG) + "HARNESS_STOP " + message + "\n")
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        fens.append(text.split(";")[0].strip())
    return fens


def main() -> None:
    if len(sys.argv) != 6:
        die("usage: harness_depth.py EXE FENS DEPTH OUT.txt SWITCH")
    exe = str(Path(sys.argv[1]).resolve())
    fens = load_fens(Path(sys.argv[2]))
    depth = int(sys.argv[3])
    out_path = Path(sys.argv[4])
    global OUT_PATH
    OUT_PATH = out_path
    switch = sys.argv[5]
    if switch not in ("none", "false", "true"):
        die("SWITCH must be none, false, or true")
    if not fens:
        die("no positions")

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    options_sent: list[str] = []

    def send(command: str) -> None:
        proc.stdin.write(command + "\n")
        proc.stdin.flush()

    def read_until(marker: str, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                die(f"timeout waiting for {marker}")
            line = proc.stdout.readline()
            if line == "":
                die(f"engine closed stdout waiting for {marker}")
            LOG.append(line)
            if any(bit in line for bit in STOP_BITS):
                die("STOP " + line.rstrip())
            if line.startswith(marker):
                return

    def ready(timeout: float = 30.0) -> None:
        send("isready")
        read_until("readyok", timeout)

    send("uci")
    read_until("uciok", 30.0)
    id_name = ""
    for line in LOG:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip()
            break

    preamble = [("Threads", "1"), ("Hash", "16"), *S14]
    if switch != "none":
        preamble.append(("IdeaS37", switch))
    for name, value in preamble:
        command = f"setoption name {name} value {value}"
        options_sent.append(command)
        send(command)
        ready()

    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        ready()
        send(f"position fen {fen}")
        ready()
        send(f"go depth {depth}")
        read_until("bestmove", 180.0)
        if index % 50 == 0:
            print(f"searched {index}/{len(fens)}", file=sys.stderr)

    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    out_path.write_text("".join(LOG))
    meta = out_path.with_suffix(out_path.suffix + ".meta")
    meta.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"depth={depth}",
                f"positions={len(fens)}",
                f"switch={switch}",
                "option_lines:",
                *options_sent,
                "",
            ]
        )
    )
    print(f"wrote {out_path} positions {len(fens)}")


if __name__ == "__main__":
    main()
