#!/usr/bin/env python3
"""Fixed-depth search of a FEN list. One engine process.

S14, then Threads 1, Hash 16, then the IdeaE2 switch if requested.
ucinewgame + isready before every go. isready after every setoption and position.
Stops on unknown option, invalid value, invalid FEN, illegal move.
Raw files are written even when the engine dies, so a sanitizer abort is kept.
"""
import argparse
import hashlib
import os
import subprocess
import sys
import threading
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
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True, help="output prefix, no extension")
    parser.add_argument("--switch", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0, help="first N positions, 0 = all")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    fens_path = Path(args.fens).resolve()
    prefix = Path(args.out)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    fens = [line.strip() for line in fens_path.read_text().splitlines() if line.strip()]
    if args.limit:
        fens = fens[: args.limit]

    options = [f"setoption name {name} value {value}" for name, value in S14]
    options.append("setoption name Threads value 1")
    options.append("setoption name Hash value 16")
    if args.switch != "omit":
        options.append(f"setoption name IdeaE2 value {args.switch}")
        options.append("setoption name IdeaE2_Span value 100")

    log: list[str] = []
    stderr_lines: list[str] = []
    node_rows: list[str] = []
    id_name = ""
    env = os.environ.copy()
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
    env.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdin and proc.stdout and proc.stderr

    def read_stderr() -> None:
        for line in proc.stderr:
            stderr_lines.append(line)

    threading.Thread(target=read_stderr, daemon=True).start()

    def send(line: str) -> None:
        log.append("> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done) -> list[str]:
        got: list[str] = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout early")
            line = line.rstrip("\n")
            log.append("< " + line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit("STOP " + line)
            if done(line):
                return got

    failure = ""
    try:
        send("uci")
        uci_lines = read_until(lambda line: line == "uciok")
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for option in options:
            send(option)
            send("isready")
            read_until(lambda line: line == "readyok")

        depth = args.depth
        for index, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line == "readyok")
            send("position fen " + fen)
            send("isready")
            read_until(lambda line: line == "readyok")
            send(f"go depth {depth}")
            go_lines = read_until(lambda line: line.startswith("bestmove "))
            nodes = ""
            marker = f"info depth {depth} "
            for line in go_lines:
                if line.startswith(marker) or line == f"info depth {depth}":
                    parts = line.split()
                    if "nodes" in parts:
                        nodes = parts[parts.index("nodes") + 1]
            if nodes == "":
                raise SystemExit(f"no depth {depth} nodes for position {index}")
            node_rows.append(f"{index} {nodes}")
            print(f"{index} {nodes}", flush=True)
        send("quit")
    except SystemExit as exc:
        failure = str(exc)
        print(failure, file=sys.stderr)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()
        prefix.with_suffix(".txt").write_text("\n".join(log) + "\n")
        prefix.with_suffix(".nodes").write_text(("\n".join(node_rows) + "\n") if node_rows else "")
        prefix.with_suffix(".stderr").write_text("".join(stderr_lines))
        total = sum(int(row.split()[1]) for row in node_rows) if node_rows else 0
        summary = [
            f"positions {len(node_rows)}",
            f"depth {args.depth}",
            f"sum {total}",
        ]
        if node_rows:
            summary.append("first " + " ".join(row.split()[1] for row in node_rows[:3]))
        if failure:
            summary.append("failure " + failure)
        prefix.with_suffix(".sum").write_text("\n".join(summary) + "\n")
        meta = [
            f"exe: {exe}",
            f"sha256: {sha}",
            f"id_name: {id_name}",
            f"fens: {fens_path}",
            f"depth: {args.depth}",
            f"switch: {args.switch}",
            f"ASAN_OPTIONS: {env.get('ASAN_OPTIONS', '')}",
            f"UBSAN_OPTIONS: {env.get('UBSAN_OPTIONS', '')}",
            "options_sent:",
            *options,
        ]
        prefix.with_suffix(".meta").write_text("\n".join(meta) + "\n")
        print("\n".join(summary))
    if failure:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except subprocess.TimeoutExpired:
        print("engine wait timed out", file=sys.stderr)
        sys.exit(1)
