#!/usr/bin/env python3
"""Honesty check for exe B. Fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/tmp/forge-b/forge")
OUT = Path(__file__).resolve().parent
CASES = [
    ("bench11", ["bench 11"], 312866, "bench"),
    ("bench13", ["bench 13"], 862329, "bench"),
    ("bench16", ["bench 16"], 3024920, "bench"),
    ("perft5", ["go perft 5"], 4865609, "perft"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_nodes(text: str, kind: str) -> int:
    if kind == "bench":
        for line in text.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit("no bench nodes line")
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit("no perft nodes line")


def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing exe {EXE}")
    digest = sha256(EXE)
    rows = []
    for name, commands, expected, kind in CASES:
        payload = "uci\n" + "".join(f"{command}\n" for command in commands) + "quit\n"
        proc = subprocess.run(
            [str(EXE)],
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
        )
        text = proc.stdout
        for mark in STOP_MARKS:
            if mark in text:
                raise SystemExit(f"STOP {mark} in {name}")
        raw = OUT / f"honesty_b_{name}.txt"
        meta = OUT / f"honesty_b_{name}.meta"
        raw.write_text(text)
        id_name = ""
        for line in text.splitlines():
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
                break
        meta.write_text(
            f"exe: {EXE}\nsha256: {digest}\nid name: {id_name}\noptions:\n"
        )
        got = parse_nodes(text, kind)
        rows.append((name, got, expected, "ok" if got == expected else "MISS"))
        print(f"{name} nodes {got} expected {expected} {'ok' if got == expected else 'MISS'}", flush=True)
    summary = OUT / "HONESTY_B.txt"
    lines = ["case nodes expected status"]
    for name, got, expected, status in rows:
        lines.append(f"{name} {got} {expected} {status}")
    summary.write_text("\n".join(lines) + "\n")
    print(summary.read_text(), end="")
    if any(status != "ok" for *_, status in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
