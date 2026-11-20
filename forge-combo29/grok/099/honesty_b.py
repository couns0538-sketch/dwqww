#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/tmp/forge-B/forge")
OUT = Path(__file__).resolve().parent
LINES = [
    ("bench11", ["bench", "11"], 312866),
    ("bench13", ["bench", "13"], 862329),
    ("bench16", ["bench", "16"], 3024920),
    ("perft5", ["go", "perft", "5"], 4865609),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_line(args: list[str]) -> str:
    # uci is not setoption; it only prints the id. The measured command follows.
    script = "uci\n" + " ".join(args) + "\nquit\n"
    proc = subprocess.run(
        [str(EXE)],
        input=script,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    return text


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def nodes_of(text: str, kind: str) -> int | None:
    found = None
    for line in text.splitlines():
        if kind.startswith("bench") and line.startswith("info string bench depth "):
            parts = line.split()
            if "nodes" in parts:
                found = int(parts[parts.index("nodes") + 1])
        if kind == "perft5" and line.startswith("nodes "):
            found = int(line.split()[1])
    return found


def main() -> int:
    digest = sha256(EXE)
    chunks = []
    ok = True
    for name, args, expected in LINES:
        text = run_line(args)
        raw = OUT / f"honesty_b_{name}.txt"
        raw.write_text(text)
        ident = id_name(text)
        meta = OUT / f"honesty_b_{name}.txt.meta"
        meta.write_text(
            "\n".join(
                [
                    f"exe: {EXE}",
                    f"sha256: {digest}",
                    f"id name: {ident}",
                    "options sent:",
                    "(none)",
                    f"commands: uci / {' '.join(args)} / quit",
                    "",
                ]
            )
        )
        got = nodes_of(text, name)
        flag = "OK" if got == expected else "MISS"
        if got != expected:
            ok = False
        chunks.append(f"===== {name} expected {expected} got {got} {flag} =====\n{text}")
        print(f"{name} {got} {flag}", flush=True)
    (OUT / "HONESTY_B.txt").write_text("\n".join(chunks))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
