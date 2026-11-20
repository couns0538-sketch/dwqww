#!/usr/bin/env python3
"""One engine process. S14, then Threads and Hash, then each position.

Usage: uci_search.py EXE POSITIONS RAW META DEPTH [IdeaA5]
IdeaA5 is omitted, or the word true, or the word false.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys
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
    ("Threads", "1"),
    ("Hash", "16"),
]

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def main() -> int:
    exe = str(Path(sys.argv[1]).resolve())
    positions = Path(sys.argv[2])
    raw_path = Path(sys.argv[3])
    meta_path = Path(sys.argv[4])
    depth = int(sys.argv[5])
    idea = sys.argv[6] if len(sys.argv) > 6 else ""
    if idea not in ("", "true", "false"):
        print("IdeaA5 argument must be true, false, or omitted", file=sys.stderr)
        return 2

    fens = []
    for line in positions.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(fen_of(line))

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    log: list[str] = []
    options_sent: list[str] = []

    def send(line: str) -> None:
        log.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done) -> str:
        while True:
            line = proc.stdout.readline()
            if line == "":
                err = proc.stderr.read() if proc.stderr is not None else ""
                if err:
                    log.append("---- stderr ----")
                    log.extend(err.splitlines())
                raw_path.write_text("\n".join(log) + "\n")
                raise SystemExit("engine closed stdout\n" + err)
            line = line.rstrip("\n")
            log.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raw_path.write_text("\n".join(log) + "\n")
                    raise SystemExit(f"STOP {mark}: {line}")
            if done(line):
                return line

    send("uci")
    id_name = ""
    while True:
        line = read_until(lambda s: s == "uciok" or s.startswith("id name "))
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            continue
        break

    for name, value in S14:
        command = f"setoption name {name} value {value}"
        options_sent.append(command)
        send(command)
        send("isready")
        read_until(lambda s: s == "readyok")

    if idea:
        command = f"setoption name IdeaA5 value {idea}"
        options_sent.append(command)
        send(command)
        send("isready")
        read_until(lambda s: s == "readyok")

    for fen in fens:
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda s: s == "readyok")
        send(f"go depth {depth}")
        read_until(lambda s: s.startswith("bestmove "))

    send("quit")
    proc.stdin.close()
    rest = proc.stdout.read()
    if rest:
        log.extend(rest.splitlines())
    proc.wait(timeout=60)
    if proc.stderr is not None:
        err = proc.stderr.read()
        if err:
            log.append("---- stderr ----")
            log.extend(err.splitlines())
    raw_path.write_text("\n".join(log) + "\n")
    meta_path.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"positions={positions.resolve()}",
                f"depth={depth}",
                f"count={len(fens)}",
                "options:",
                *options_sent,
                "",
            ]
        )
    )
    print(f"positions {len(fens)} raw {raw_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
