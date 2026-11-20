#!/usr/bin/env python3
"""Measured fixed-depth search. Stops on unknown option, invalid value, invalid FEN, illegal move."""
import argparse
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
]

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fen = line.split(";")[0].strip()
        if fen.startswith("fen "):
            fen = fen[4:].strip()
        fens.append(fen)
        if limit and len(fens) >= limit:
            break
    return fens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--option", action="append", default=[], help="Extra 'Name value' after S14")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fens = load_fens(Path(args.fens), args.limit)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()

    id_name = ""
    id_proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    for line in id_proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break

    options = [("Threads", "1"), ("Hash", "16"), *S14]
    for item in args.option:
        name, value = item.split(" ", 1)
        options.append((name, value))

    log_path = Path(str(out) + ".log")
    nodes_path = Path(str(out) + ".nodes")
    meta_path = Path(str(out) + ".meta")
    err_path = Path(str(out) + ".stderr")

    meta_lines = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"depth={args.depth}",
        f"fens={Path(args.fens).resolve()}",
        f"positions={len(fens)}",
    ]
    for name, value in options:
        meta_lines.append(f"option {name} {value}")
    meta_path.write_text("\n".join(meta_lines) + "\n")

    err_f = err_path.open("w")
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=err_f,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    log_f = log_path.open("w")
    nodes_f = nodes_path.open("w")

    def fail(message: str) -> int:
        log_f.write(f"!! {message}\n")
        log_f.flush()
        proc.kill()
        proc.wait(timeout=10)
        log_f.close()
        nodes_f.close()
        err_f.close()
        print(message, file=sys.stderr)
        return 2

    def send(line: str) -> None:
        log_f.write(f">> {line}\n")
        log_f.flush()
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker: str) -> int | None:
        while True:
            line = proc.stdout.readline()
            if line == "":
                return fail("engine closed stdout")
            line = line.rstrip("\r\n")
            log_f.write(f"<< {line}\n")
            for mark in STOP_MARKS:
                if mark in line:
                    return fail(f"STOP {mark}: {line}")
            if line.startswith(marker):
                return None

    def search_one(fen: str) -> tuple[int, int]:
        send("ucinewgame")
        send("isready")
        stopped = read_until("readyok")
        if stopped:
            return stopped, 0
        send(f"position fen {fen}")
        send("isready")
        stopped = read_until("readyok")
        if stopped:
            return stopped, 0
        send(f"go depth {args.depth}")
        nodes = None
        while True:
            line = proc.stdout.readline()
            if line == "":
                return fail("engine closed stdout during go"), 0
            line = line.rstrip("\r\n")
            log_f.write(f"<< {line}\n")
            for mark in STOP_MARKS:
                if mark in line:
                    return fail(f"STOP {mark}: {line}"), 0
            if line.startswith("info depth "):
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
            if line.startswith("bestmove "):
                if nodes is None:
                    return fail(f"no info nodes before bestmove for {fen}"), 0
                return 0, nodes

    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        stopped = read_until("readyok")
        if stopped:
            return stopped

    total = 0
    counts = []
    for index, fen in enumerate(fens, start=1):
        status, nodes = search_one(fen)
        if status:
            return status
        counts.append(nodes)
        total += nodes
        nodes_f.write(f"{nodes}\n")
        nodes_f.flush()
        if index % 25 == 0 or index == len(fens):
            print(f"progress {index}/{len(fens)} total {total}", flush=True)

    send("quit")
    proc.wait(timeout=30)
    log_f.close()
    nodes_f.close()
    err_f.close()
    first = " ".join(str(n) for n in counts[:3])
    print(f"positions {len(counts)}")
    print(f"sum {total}")
    print(f"first3 {first}")
    print(f"nodes_file {nodes_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
