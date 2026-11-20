#!/usr/bin/env python3
"""Honesty check of exe P. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/work/build/forge")
OUT = Path(__file__).resolve().parent
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


def id_name(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return "MISSING"


def run_one(exe: Path, command: str) -> str:
    proc = subprocess.run(
        [exe],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    return text


def nodes_of(command: str, text: str) -> int:
    if command.startswith("bench"):
        for line in text.splitlines():
            if "nodes " in line and line.startswith("info string bench"):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit("no bench nodes line:\n" + text)
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit("no perft nodes line:\n" + text)


def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing exe {EXE}")
    digest = sha256(EXE)
    name = id_name(EXE)
    summary = []
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "_")
        text = run_one(EXE, command)
        raw = OUT / f"honesty_p_{slug}.txt"
        raw.write_text(text)
        got = nodes_of(command, text)
        meta = OUT / f"honesty_p_{slug}.meta"
        meta.write_text(
            "\n".join(
                [
                    f"exe={EXE}",
                    f"sha256={digest}",
                    f"id_name={name}",
                    "options=",
                    f"command={command}",
                    f"nodes={got}",
                    f"expected={expected}",
                    f"match={str(got == expected).lower()}",
                    "",
                ]
            )
        )
        status = "OK" if got == expected else "FAIL"
        summary.append(f"{command} nodes {got} expected {expected} {status}")
        print(summary[-1])
    report = OUT / "HONESTY_P.txt"
    report.write_text(
        "\n".join(
            [
                f"exe={EXE}",
                f"sha256={digest}",
                f"id_name={name}",
                "setoption=none",
                *summary,
                "",
            ]
        )
    )
    if any(line.endswith("FAIL") for line in summary):
        sys.exit(1)


if __name__ == "__main__":
    main()
