#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

CASES = [
    ("bench11", ["bench 11"], "312866"),
    ("bench13", ["bench 13"], "862329"),
    ("bench16", ["bench 16"], "3024920"),
    ("perft5", ["go perft 5"], "4865609"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def run_case(exe: Path, commands: list[str]) -> str:
    script = "\n".join(commands + ["quit"]) + "\n"
    proc = subprocess.run(
        [str(exe)],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout + (("\n# stderr\n" + proc.stderr) if proc.stderr else "")


def main() -> None:
    digest = sha256(EXE)
    name = id_name(EXE)
    rows = []
    for label, commands, expect in CASES:
        text = run_case(EXE, commands)
        raw = OUT / f"honesty_b_{label}.txt"
        raw.write_text(text)
        meta = OUT / f"honesty_b_{label}.meta"
        option_lines = "(none)"
        meta.write_text(
            f"exe: {EXE}\n"
            f"sha256: {digest}\n"
            f"id name: {name}\n"
            f"id name source: separate uci process of this exe\n"
            f"commands: {commands}\n"
            f"options sent:\n{option_lines}\n"
        )
        nodes = ""
        for line in text.splitlines():
            if " nodes " in line or line.startswith("nodes "):
                parts = line.replace(":", " ").split()
                if "nodes" in parts:
                    nodes = parts[parts.index("nodes") + 1]
        ok = "yes" if nodes == expect else "NO"
        rows.append((label, nodes, expect, ok, raw.name))
        print(f"{label} nodes {nodes} expect {expect} {ok}")
    summary = OUT / "HONESTY_B.txt"
    lines = [
        f"exe {EXE}",
        f"sha256 {digest}",
        f"id name {name}",
        "label nodes expect match file",
    ]
    for label, nodes, expect, ok, filename in rows:
        lines.append(f"{label} {nodes} {expect} {ok} {filename}")
    summary.write_text("\n".join(lines) + "\n")
    print(summary)


if __name__ == "__main__":
    main()
