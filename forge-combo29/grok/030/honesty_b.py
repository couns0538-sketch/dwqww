#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}

COMMANDS = {
    "bench11": "bench 11\nuci\nquit\n",
    "bench13": "bench 13\nuci\nquit\n",
    "bench16": "bench 16\nuci\nquit\n",
    "perft5": "go perft 5\nuci\nquit\n",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def nodes_of(name: str, text: str) -> int:
    if name.startswith("bench"):
        for line in text.splitlines():
            if line.startswith("info string bench "):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit(f"no bench line in {name}")
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit(f"no perft nodes in {name}")


def main() -> None:
    digest = sha256(EXE)
    failures = []
    for name, commands in COMMANDS.items():
        proc = subprocess.run(
            [str(EXE)],
            input=commands.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=300,
        )
        text = proc.stdout.decode("utf-8", "replace")
        raw = OUT / f"honesty_B_{name}.txt"
        raw.write_text(text)
        got = nodes_of(name, text)
        meta = OUT / f"honesty_B_{name}.meta"
        meta.write_text(
            "\n".join(
                [
                    f"exe={EXE}",
                    f"sha256={digest}",
                    f"id_name={id_name(text)}",
                    "options=",
                    f"command={commands.strip()}",
                    f"nodes={got}",
                    f"expected={EXPECTED[name]}",
                    f"exit={proc.returncode}",
                    "",
                ]
            )
        )
        ok = got == EXPECTED[name]
        print(f"{name} nodes {got} expected {EXPECTED[name]} {'OK' if ok else 'MISS'}")
        if not ok:
            failures.append(name)
    summary = OUT / "HONESTY_B.txt"
    lines = [f"exe={EXE}", f"sha256={digest}"]
    for name in COMMANDS:
        meta = (OUT / f"honesty_B_{name}.meta").read_text().splitlines()
        nodes = next(line for line in meta if line.startswith("nodes="))
        expected = next(line for line in meta if line.startswith("expected="))
        lines.append(f"{name} {nodes} {expected}")
    lines.append("result=" + ("OK" if not failures else "MISS " + " ".join(failures)))
    summary.write_text("\n".join(lines) + "\n")
    print(summary.read_text())
    if failures:
        raise SystemExit("MISS " + " ".join(failures))


if __name__ == "__main__":
    main()
