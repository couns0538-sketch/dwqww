#!/usr/bin/env python3
"""Fresh-process honesty check of exe B. No setoption. Writes raw output and HONESTY_B.txt."""
import hashlib
import subprocess
import sys
from pathlib import Path

OUT = Path("/agent/repos/dwqww/forge-combo29/grok/008")
EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/agent/repos/base/forge-combo29/build/forge")
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "honesty_b"
REPORT = sys.argv[3] if len(sys.argv) > 3 else "HONESTY_B.txt"
EXPECT = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = {
    "bench11": "bench 11\nquit\n",
    "bench13": "bench 13\nquit\n",
    "bench16": "bench 16\nquit\n",
    "perft5": "position startpos\ngo perft 5\nquit\n",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    return "MISSING"


def parse_nodes(name: str, text: str) -> int:
    if name.startswith("bench"):
        for line in text.splitlines():
            if "nodes" in line and line.startswith("info string bench"):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit(f"no bench nodes in {name}")
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit(f"no perft nodes in {name}")


def main() -> None:
    digest = sha256(EXE)
    name = id_name(EXE)
    lines = []
    failed = False
    for key, command in COMMANDS.items():
        proc = subprocess.run(
            [str(EXE)],
            input=command,
            text=True,
            capture_output=True,
            check=False,
        )
        raw = proc.stdout
        if proc.stderr:
            raw = raw + "\n# stderr\n" + proc.stderr
        (OUT / f"{PREFIX}_{key}.txt").write_text(raw)
        nodes = parse_nodes(key, proc.stdout)
        ok = nodes == EXPECT[key]
        if not ok:
            failed = True
        lines.append(f"{key} nodes {nodes} expected {EXPECT[key]} {'OK' if ok else 'FAIL'}")
        meta = (
            f"exe={EXE}\n"
            f"sha256={digest}\n"
            f"id_name={name}\n"
            f"options=\n"
            f"command={command!r}\n"
            f"returncode={proc.returncode}\n"
        )
        (OUT / f"{PREFIX}_{key}.meta").write_text(meta)
    report = "\n".join(lines) + "\n"
    (OUT / REPORT).write_text(report)
    sys.stdout.write(report)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
