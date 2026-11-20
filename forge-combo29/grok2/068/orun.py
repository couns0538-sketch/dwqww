#!/usr/bin/env python3
"""orun.py <exe> <fens> <raw.txt> [IdeaK4 true|false]

S14 in the brief's order, then Threads 1 and Hash 16 were sent first.
If a fourth argument is given it is setoption name IdeaK4 value <true|false>
after S14. ucinewgame + isready before every position. go depth 12.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    fens_path = sys.argv[2]
    raw_path = sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) > 4 else None
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    options: list[str] = []
    id_name = ""

    def send(cmd: str) -> None:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def take_line() -> str:
        line = proc.stdout.readline()
        if line == "":
            sys.exit("STOP: engine closed stdout")
        raw.write(line)
        raw.flush()
        for token in STOPS:
            if token in line:
                sys.exit(f"STOP: {line.strip()}")
        return line

    def read_until(marker: str) -> None:
        while True:
            line = take_line()
            if marker in line:
                return

    with open(raw_path, "w", encoding="utf-8") as raw:
        globals()["raw"] = raw
        send("uci")
        while True:
            line = take_line()
            if line.startswith("id name "):
                id_name = line[len("id name ") :].rstrip("\r\n")
            if line.startswith("uciok"):
                break
        for name, value in S14:
            cmd = f"setoption name {name} value {value}"
            options.append(cmd)
            send(cmd)
            send("isready")
            read_until("readyok")
        if switch is not None:
            cmd = f"setoption name IdeaK4 value {switch}"
            options.append(cmd)
            send(cmd)
            send("isready")
            read_until("readyok")
        for index, fen in enumerate(fens, 1):
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok")
            send("go depth 12")
            last_nodes = None
            while True:
                line = take_line()
                if line.startswith("info ") and " nodes " in line:
                    parts = line.split()
                    last_nodes = parts[parts.index("nodes") + 1]
                if line.startswith("bestmove "):
                    break
            if last_nodes is None:
                sys.exit(f"STOP: no nodes before bestmove at position {index}")
            print(f"{index} {last_nodes}", flush=True)
        send("quit")
    proc.wait(timeout=30)
    meta_path = raw_path + ".meta" if not raw_path.endswith(".txt") else raw_path[:-4] + ".meta"
    if raw_path.endswith(".txt"):
        meta_path = raw_path[:-4] + ".meta"
    else:
        meta_path = raw_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {sha}\n")
        meta.write(f"id name {id_name}\n")
        for cmd in options:
            meta.write(cmd + "\n")
    print(f"positions {len(fens)} raw {raw_path}", flush=True)


if __name__ == "__main__":
    main()
