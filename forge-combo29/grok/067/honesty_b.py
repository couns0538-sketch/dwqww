#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/forge-base/forge")
TAG = sys.argv[2] if len(sys.argv) > 2 else "B"
EXPECT = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def run(args_line: str) -> str:
    completed = subprocess.run(
        [str(EXE)],
        input=args_line + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    return completed.stdout + (("\n" + completed.stderr) if completed.stderr else "")

def id_name() -> str:
    text = run("uci")
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""

def nodes_of(key: str, text: str) -> int:
    if key.startswith("bench"):
        for line in text.splitlines():
            if "nodes " in line and line.startswith("info string bench"):
                return int(line.split("nodes ", 1)[1].split()[0])
        raise SystemExit(f"no bench nodes in {key}")
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        raise SystemExit(f"no perft nodes in {key}")
    return last

def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing {EXE}")
    digest = sha256(EXE)
    name = id_name()
    rows = []
    failed = False
    for key, (command, expected) in EXPECT.items():
        text = run(command)
        (OUT / f"{TAG}_{key}.txt").write_text(text)
        meta = (
            f"exe={EXE}\n"
            f"sha256={digest}\n"
            f"id_name={name}\n"
            f"command={command}\n"
            "options=\n"
        )
        (OUT / f"{TAG}_{key}.meta").write_text(meta)
        got = nodes_of(key, text)
        ok = got == expected
        failed = failed or not ok
        rows.append((command, expected, got, "ok" if ok else "MISMATCH"))
    lines = [f"honesty exe {TAG}", f"exe={EXE}", f"sha256={digest}", f"id_name={name}", "setoption=none"]
    for command, expected, got, status in rows:
        lines.append(f"{command} expected {expected} got {got} {status}")
    lines.append("FAIL" if failed else "PASS")
    text = "\n".join(lines) + "\n"
    (OUT / f"HONESTY_{TAG}.txt").write_text(text)
    sys.stdout.write(text)
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
