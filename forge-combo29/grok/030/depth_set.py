#!/usr/bin/env python3
"""Depth search over a FEN list. S14, Threads 1, Hash 16 before every go.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the raw UCI transcript and a .meta file. Prints one nodes row per position.
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
]

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6 or "/" not in parts[0]:
        raise SystemExit(f"bad fen line: {line!r}")
    return " ".join(parts[:6])


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: depth_set.py EXE FENS DEPTH RAW [Name=value ...]")
    exe = Path(sys.argv[1]).resolve()
    fens = [fen_of(line) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
    depth = int(sys.argv[3])
    raw_path = Path(sys.argv[4]).resolve()
    extras = []
    for arg in sys.argv[5:]:
        name, value = arg.split("=", 1)
        extras.append((name, value))
    options = [("Threads", "1"), ("Hash", "16"), *S14, *extras]
    option_lines = [f"setoption name {name} value {value}" for name, value in options]

    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.stdin is not None and proc.stdout is not None
    transcript: list[str] = []

    def send(line: str) -> None:
        proc.stdin.write((line + "\n").encode())
        proc.stdin.flush()
        transcript.append(">> " + line + "\n")

    def read_until(prefixes: tuple[str, ...]) -> list[str]:
        got: list[str] = []
        while True:
            raw = proc.stdout.readline()
            if not raw:
                raw_path.write_text("".join(transcript))
                raise SystemExit("engine closed stdout early")
            text = raw.decode("utf-8", "replace")
            transcript.append(text)
            got.append(text)
            low = text.lower()
            for mark in STOP_MARKS:
                if mark in low:
                    raw_path.write_text("".join(transcript))
                    raise SystemExit("STOP " + text.strip())
            if any(text.startswith(prefix) for prefix in prefixes):
                return got

    send("uci")
    uci_lines = read_until(("uciok",))
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].strip()

    nodes: list[int] = []
    try:
        for index, fen in enumerate(fens):
            for line in option_lines:
                send(line)
                send("isready")
                read_until(("readyok",))
            send("ucinewgame")
            send("isready")
            read_until(("readyok",))
            send(f"position fen {fen}")
            send("isready")
            read_until(("readyok",))
            send(f"go depth {depth}")
            chunk = read_until(("bestmove ",))
            found = None
            for line in chunk:
                if line.startswith("info depth "):
                    parts = line.split()
                    if "nodes" in parts:
                        found = int(parts[parts.index("nodes") + 1])
            if found is None:
                raw_path.write_text("".join(transcript))
                raise SystemExit(f"no nodes for position {index}")
            nodes.append(found)
            print(f"{index} {found}", flush=True)
    finally:
        send("quit")
        proc.stdin.close()
        proc.wait(timeout=30)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("".join(transcript))
        meta = raw_path.with_suffix(raw_path.suffix + ".meta")
        meta.write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={sha256(exe)}",
                    f"id_name={id_name}",
                    "options:",
                    *option_lines,
                    f"depth={depth}",
                    f"positions={len(nodes)}",
                    f"sum={sum(nodes)}",
                    "",
                ]
            )
        )
    print(f"SUM {sum(nodes)} N {len(nodes)}")


if __name__ == "__main__":
    main()
