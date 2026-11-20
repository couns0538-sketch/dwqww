#!/usr/bin/env python3
"""Honesty check for exe P. One fresh process per line. No setoption."""
import hashlib
import subprocess
from pathlib import Path

EXE = Path("/agent/repos/work/build/forge")
OUT = Path("/agent/repos/dwqww/forge-combo29/grok/042")

CASES = [
    ("bench11", ["uci", "bench 11", "quit"]),
    ("bench13", ["uci", "bench 13", "quit"]),
    ("bench16", ["uci", "bench 16", "quit"]),
    ("perft5", ["uci", "position startpos", "go perft 5", "quit"]),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    digest = sha256(EXE)
    lines = []
    for name, commands in CASES:
        proc = subprocess.run(
            [str(EXE)],
            input="\n".join(commands) + "\n",
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        raw = proc.stdout
        (OUT / f"honesty_p_{name}.txt").write_text(raw)
        if proc.stderr:
            (OUT / f"honesty_p_{name}.err").write_text(proc.stderr)
        id_name = ""
        for line in raw.splitlines():
            if line.startswith("id name "):
                id_name = line
                break
        meta = [
            f"exe {EXE}",
            f"sha256 {digest}",
            f"id_name {id_name}",
            "options",
            f"commands {' | '.join(commands)}",
            f"returncode {proc.returncode}",
            "",
        ]
        (OUT / f"honesty_p_{name}.meta").write_text("\n".join(meta))
        kept = [line for line in raw.splitlines() if "nodes" in line]
        lines.append(f"{name} rc={proc.returncode}")
        lines.extend(kept[-3:])
        lines.append("")
    (OUT / "HONESTY_P.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
