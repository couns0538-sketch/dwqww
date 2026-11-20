#!/usr/bin/env python3
"""Honesty check. Fresh process per line. No setoption. argv: exe prefix"""
import hashlib
import pathlib
import re
import subprocess
import sys

EXE = pathlib.Path(sys.argv[1]).resolve()
PREFIX = sys.argv[2]
REPO = pathlib.Path(pathlib.Path.home().joinpath("grok_repo.txt").read_text().strip())
SEAT = pathlib.Path.home().joinpath("grok_seat.txt").read_text().strip()
OUT = REPO / "forge-combo29" / "grok" / SEAT

JOBS = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_job(command: str) -> tuple[str, str]:
    stdin = f"uci\nisready\n{command}\nquit\n"
    proc = subprocess.run([str(EXE)], input=stdin, text=True, capture_output=True, timeout=300, check=False)
    return proc.stdout, proc.stderr


def id_name(stdout: str) -> str:
    match = re.search(r"^id name (.+)$", stdout, re.M)
    return match.group(1).strip() if match else "MISSING"


def nodes_of(name: str, stdout: str) -> str:
    if name.startswith("bench"):
        depth = name.replace("bench", "")
        match = re.search(rf"bench depth {depth} nodes (\d+)", stdout)
        return match.group(1) if match else "MISSING"
    found = re.findall(r"^nodes (\d+)$", stdout, re.M)
    return found[-1] if found else "MISSING"


def main() -> int:
    digest = sha256(EXE)
    rows = []
    for name, command, expected in JOBS:
        stdout, stderr = run_job(command)
        raw = OUT / f"{PREFIX}_{name}.txt"
        err = OUT / f"{PREFIX}_{name}.err"
        meta = OUT / f"{PREFIX}_{name}.meta"
        raw.write_text(stdout)
        if stderr:
            err.write_text(stderr)
        elif err.exists():
            err.unlink()
        got = nodes_of(name, stdout)
        meta.write_text(
            "\n".join(
                [
                    f"exe={EXE}",
                    f"sha256={digest}",
                    f"id_name={id_name(stdout)}",
                    "options_sent=none",
                    f"stdin=uci / isready / {command} / quit",
                    f"nodes={got}",
                    f"expected={expected}",
                    f"stderr={'yes' if stderr else 'no'}",
                    "",
                ]
            )
        )
        rows.append((command, got, expected, "yes" if got == expected else "NO"))
        print(f"{command} nodes {got} expected {expected} match {rows[-1][3]}", flush=True)
    lines = ["command\tnodes\texpected\tmatch"]
    for name, command, expected in JOBS:
        text = (OUT / f"{PREFIX}_{name}.txt").read_text()
        got = nodes_of(name, text)
        lines.append(f"{command}\t{got}\t{expected}\t{'yes' if got == expected else 'NO'}")
    (OUT / f"{PREFIX}.txt").write_text("\n".join(lines) + "\n")
    print((OUT / f"{PREFIX}.txt").read_text(), end="")
    return 0 if all(row[3] == "yes" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
