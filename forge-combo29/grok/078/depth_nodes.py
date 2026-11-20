#!/usr/bin/env python3
"""Search every FEN at a fixed depth and save the raw engine output.

S14 is sent in the brief's order, then Threads 1, then Hash 16.
Each position is ucinewgame, isready, position, isready, go.
"""
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
    ("Threads", "1"),
    ("Hash", "16"),
]

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
    return fens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True, help="prefix for .raw .meta")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[], help="Name=value sent after S14")
    args = parser.parse_args()

    exe = Path(args.exe)
    fens = load_fens(Path(args.fens))
    if args.limit:
        fens = fens[: args.limit]
    out = Path(args.out)
    digest = sha256(exe)
    options = list(S14)
    for item in args.extra:
        name, value = item.split("=", 1)
        options.append((name, value))

    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    raw: list[str] = []
    id_name = ""

    def send(line: str) -> None:
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(prefix: str) -> None:
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit("STOP eof waiting for " + prefix)
            raw.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    out.with_suffix(".raw").write_text("".join(raw))
                    raise SystemExit("STOP " + line.strip())
            if line.startswith(prefix):
                return

    send("uci")
    while True:
        line = proc.stdout.readline()
        if line == "":
            raise SystemExit("STOP eof during uci")
        raw.append(line)
        if line.startswith("id name "):
            id_name = line.strip()
        if line.startswith("uciok"):
            break
    send("isready")
    read_until("readyok")
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until("readyok")

    for index, fen in enumerate(fens):
        raw.append(f"# POS {index}\n")
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send(f"go depth {args.depth}")
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit(f"STOP eof during go at position {index}")
            raw.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    out.with_suffix(".raw").write_text("".join(raw))
                    raise SystemExit("STOP " + line.strip())
            if line.startswith("bestmove "):
                break
        if index < 3 or index + 1 == len(fens) or (index + 1) % 50 == 0:
            print(f"done {index + 1}/{len(fens)}", flush=True)

    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)
    err = proc.stderr.read() if proc.stderr is not None else ""
    text = "".join(raw)
    raw_path = Path(str(out) + ".raw")
    raw_path.write_text(text)
    if err:
        Path(str(out) + ".err").write_text(err)
    option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    meta = (
        f"exe: {exe}\n"
        f"sha256: {digest}\n"
        f"id_name: {id_name}\n"
        f"fens: {args.fens}\n"
        f"depth: {args.depth}\n"
        f"count: {len(fens)}\n"
        "options:\n"
        f"{option_lines}\n"
    )
    Path(str(out) + ".meta").write_text(meta)
    print(f"wrote {raw_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
