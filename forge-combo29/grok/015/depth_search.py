#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. S14, then one go per FEN.

After every setoption and every position command, send isready and read
every line until readyok. Stop on unknown option, invalid value, invalid
FEN, or illegal move. Writes the transcript, one node count per position,
and a .meta file.
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
    if len(parts) < 4:
        raise SystemExit(f"short fen line: {line!r}")
    if len(parts) >= 6 and parts[4].lstrip("-").isdigit():
        return " ".join(parts[:6])
    return " ".join(parts[:4]) + " 0 1"


def nodes_of(lines: list[str]) -> int:
    found = None
    for line in lines:
        if not line.startswith("info ") or line.startswith("info string"):
            continue
        parts = line.split()
        if "nodes" not in parts:
            continue
        found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes line before bestmove")
    return found


def main() -> None:
    if len(sys.argv) not in (6, 7):
        raise SystemExit("usage: depth_search.py EXE FENS DEPTH OUT_PREFIX SWITCH [OPTION]")
    exe, fens, depth_s, out_prefix, switch = sys.argv[1:6]
    option_name = sys.argv[6] if len(sys.argv) == 7 else "IdeaS6"
    depth = int(depth_s)
    if switch not in ("true", "false", "omit"):
        raise SystemExit("SWITCH must be true, false, or omit")
    exe_path = str(Path(exe).resolve())
    digest = hashlib.sha256(Path(exe_path).read_bytes()).hexdigest()
    positions = [fen_of(line) for line in Path(fens).read_text().splitlines() if line.strip()]
    proc = subprocess.Popen(
        [exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log: list[str] = []
    assert proc.stdin is not None and proc.stdout is not None

    def send(line: str) -> None:
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        log.append("> " + line)

    def read_until(done) -> list[str]:
        got: list[str] = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                Path(out_prefix + ".txt").write_text("\n".join(log) + "\n")
                raise SystemExit("engine closed stdout\n" + "\n".join(log[-40:]))
            line = line.rstrip("\r\n")
            log.append(line)
            got.append(line)
            if any(bad in line for bad in BAD):
                Path(out_prefix + ".txt").write_text("\n".join(log) + "\n")
                raise SystemExit("STOP " + line)
            if done(line):
                return got

    def command_then_ready(line: str) -> None:
        send(line)
        send("isready")
        read_until(lambda got: got == "readyok")

    send("uci")
    uci_lines = read_until(lambda line: line == "uciok")
    id_name = next((line for line in uci_lines if line.startswith("id name ")), "id name MISSING")
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch != "omit":
        options.append(f"setoption name {option_name} value {switch}")
    for option in options:
        command_then_ready(option)

    counts: list[int] = []
    for index, fen in enumerate(positions, start=1):
        command_then_ready("ucinewgame")
        command_then_ready("position fen " + fen)
        send(f"go depth {depth}")
        played = read_until(lambda line: line.startswith("bestmove "))
        counts.append(nodes_of(played))
        if index % 50 == 0 or index == len(positions):
            print(f"{index} {counts[-1]} sum {sum(counts)}", flush=True)

    send("quit")
    proc.stdin.close()
    proc.wait(timeout=30)
    Path(out_prefix + ".txt").write_text("\n".join(log) + "\n")
    Path(out_prefix + ".nodes").write_text("".join(f"{n}\n" for n in counts))
    meta = [
        f"exe={exe_path}",
        f"sha256={digest}",
        f"id_name={id_name}",
        f"fens={Path(fens).resolve()}",
        f"depth={depth}",
        f"positions={len(counts)}",
        "options:",
        *options,
    ]
    Path(out_prefix + ".meta").write_text("\n".join(meta) + "\n")
    print("FIRST", " ".join(str(n) for n in counts[:3]))
    print("SUM", sum(counts))


if __name__ == "__main__":
    main()
