#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name_from(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def nodes_from(command: str, text: str) -> int | None:
    if command.startswith("bench"):
        prefix = "info string bench depth "
        for line in text.splitlines():
            if line.startswith(prefix) and " nodes " in line:
                parts = line.split()
                # info string bench depth D nodes N time ...
                try:
                    return int(parts[parts.index("nodes") + 1])
                except (ValueError, IndexError):
                    return None
        return None
    # perft prints a final "nodes N"
    found = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                found = int(parts[1])
    return found


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_b.py EXE OUT_DIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    chunks = []
    failures = 0
    for command, expected in EXPECTED.items():
        script = "uci\nisready\n" + command + "\nquit\n"
        proc = subprocess.run(
            [str(exe)],
            input=script,
            text=True,
            capture_output=True,
            timeout=300,
        )
        raw = proc.stdout
        if proc.stderr:
            raw += proc.stderr
        got = nodes_from(command, proc.stdout)
        ok = got == expected and proc.returncode == 0
        if not ok:
            failures += 1
        name = command.replace(" ", "_")
        (out_dir / f"honesty_b_{name}.txt").write_text(raw)
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id_name {id_name_from(proc.stdout)}\n"
            f"options\n"
            f"commands\n"
            f"uci\n"
            f"isready\n"
            f"{command}\n"
            f"quit\n"
            f"returncode {proc.returncode}\n"
            f"nodes {got}\n"
            f"expected {expected}\n"
            f"match {ok}\n"
        )
        (out_dir / f"honesty_b_{name}.meta").write_text(meta)
        chunks.append(f"===== {command} =====\n{raw}")
        print(f"{command} nodes {got} expected {expected} match {ok}")
    (out_dir / "HONESTY_B.txt").write_text("".join(chunks))
    summary = "\n".join(
        [
            f"exe {exe}",
            f"sha256 {digest}",
            "options",
            "commands uci / isready / one of bench 11, bench 13, bench 16, go perft 5 / quit",
            f"failures {failures}",
        ]
    )
    (out_dir / "HONESTY_B.meta").write_text(summary + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
