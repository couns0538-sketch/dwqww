#!/usr/bin/env python3
"""UCI depth harness. Stops on unknown option, invalid value, invalid FEN, illegal move.
After every setoption and every position it reads until readyok.
ucinewgame + isready before every go.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
]


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit(f"invalid FEN line: {line}")
    return " ".join(parts[:6])


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: measure.py EXE DEPTH FENS OUT_PREFIX [extra setoption lines...]")
    exe, depth, fen_path, prefix = sys.argv[1:5]
    extras = sys.argv[5:]
    fens = [fen_of(line) for line in Path(fen_path).read_text().splitlines() if line.strip()]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
    )
    raw = Path(prefix + ".txt")
    rows = Path(prefix + ".rows")
    meta = Path(prefix + ".meta")
    sent = []

    def fail(msg: str) -> None:
        raw.write_text("".join(log))
        proc.kill()
        raise SystemExit(msg)

    log: list[str] = []

    def read_until(token: str) -> list[str]:
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail("engine closed stdout")
            log.append(line)
            stripped = line.rstrip("\n")
            got.append(stripped)
            low = stripped.lower()
            for bad in BAD:
                if bad.lower() in low:
                    fail(f"STOP {stripped}")
            if token in stripped:
                return got

    def send(line: str) -> None:
        sent.append(line)
        log.append(">>> " + line + "\n")
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    send("uci")
    uci_lines = read_until("uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    options = ["setoption name Threads value 1", "setoption name Hash value 16", *S14, *extras]
    for opt in options:
        send(opt)
        send("isready")
        read_until("readyok")
    nodes = []
    with rows.open("w") as rowf:
        rowf.write("index\tnodes\tfen\n")
        for i, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok")
            send(f"go depth {depth}")
            reply = read_until("bestmove")
            last = None
            for line in reply:
                if line.startswith("info depth ") and " nodes " in line:
                    last = int(line.split(" nodes ")[1].split()[0])
            if last is None:
                fail(f"no nodes for position {i}")
            nodes.append(last)
            rowf.write(f"{i}\t{last}\t{fen}\n")
            rowf.flush()
    send("quit")
    proc.wait(timeout=30)
    raw.write_text("".join(log))
    meta.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"depth={depth}",
                f"positions={len(fens)}",
                f"fen_file={fen_path}",
                "options_sent:",
                *options,
                f"sum={sum(nodes)}",
                "",
            ]
        )
    )
    print(f"positions={len(nodes)} sum={sum(nodes)} first3={' / '.join(str(n) for n in nodes[:3])}")


if __name__ == "__main__":
    main()
