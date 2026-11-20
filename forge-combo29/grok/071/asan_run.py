#!/usr/bin/env python3
"""Same UCI runner as measure.py, also keeping stderr for sanitizer lines."""
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
    exe, depth, fen_path, prefix = sys.argv[1:5]
    extras = sys.argv[5:]
    fens = [fen_of(line) for line in Path(fen_path).read_text().splitlines() if line.strip()]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    asan_syms = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    sent = []

    def send(line: str) -> None:
        sent.append(line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(token: str) -> list[str]:
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                err = proc.stderr.read()
                Path(prefix + ".stderr").write_text(err)
                raise SystemExit("engine closed stdout\n" + err[-2000:])
            stripped = line.rstrip("\n")
            got.append(stripped)
            low = stripped.lower()
            for bad in BAD:
                if bad.lower() in low:
                    err = proc.stderr.read()
                    Path(prefix + ".stderr").write_text(err)
                    raise SystemExit(f"STOP {stripped}")
            if token in stripped:
                return got

    send("uci")
    uci_lines = read_until("uciok")
    id_name = next((line[len("id name "):] for line in uci_lines if line.startswith("id name ")), "")
    options = ["setoption name Threads value 1", "setoption name Hash value 16", *S14, *extras]
    for opt in options:
        send(opt)
        send("isready")
        read_until("readyok")
    out_lines = []
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
                last = line.split(" nodes ")[1].split()[0]
        out_lines.append(f"{i}\t{last}\t{fen}")
    send("quit")
    stdout, stderr = proc.communicate(timeout=60)
    Path(prefix + ".stdout").write_text("\n".join(out_lines) + "\n" + stdout)
    Path(prefix + ".stderr").write_text(stderr)
    san_lines = [line for line in stderr.splitlines() if "Sanitizer" in line or "sanitizer" in line]
    Path(prefix + ".meta").write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"asan_symbol_count={asan_syms}",
                f"depth={depth}",
                f"positions={len(fens)}",
                f"fen_file={fen_path}",
                "options_sent:",
                *options,
                f"sanitizer_lines={len(san_lines)}",
                *san_lines,
                "",
            ]
        )
    )
    print(f"asan_symbols={asan_syms} positions={len(fens)} sanitizer_lines={len(san_lines)}")
    if san_lines:
        print(san_lines[0])


if __name__ == "__main__":
    main()
