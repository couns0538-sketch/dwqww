#!/usr/bin/env python3
"""Honesty check for exe P. One fresh process per line. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/tmp/forge-builds/work/forge")
OUT_DIR = pathlib.Path(__file__).resolve().parent
CASES = [
    ("bench11", ["uci", "isready", "bench 11", "quit"], "312866"),
    ("bench13", ["uci", "isready", "bench 13", "quit"], "862329"),
    ("bench16", ["uci", "isready", "bench 16", "quit"], "3024920"),
    ("perft5", ["uci", "isready", "go perft 5", "quit"], "4865609"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_case(name: str, commands: list[str]) -> str:
    payload = "\n".join(commands) + "\n"
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
            raise SystemExit(f"STOP {name}: saw {mark}")
    raw_path = OUT_DIR / f"honesty_p_{name}.txt"
    raw_path.write_text(text)
    id_name = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    meta = "\n".join(
        [
            f"exe={EXE}",
            f"sha256={sha256(EXE)}",
            f"id_name={id_name}",
            "options:",
            "(none)",
            f"commands={commands}",
            f"returncode={proc.returncode}",
            "",
        ]
    )
    (OUT_DIR / f"honesty_p_{name}.txt.meta").write_text(meta)
    return id_name


def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing exe {EXE}")
    digest = sha256(EXE)
    id_name = ""
    lines = [f"exe={EXE}", f"sha256={digest}"]
    expected = {
        "bench11": "312866",
        "bench13": "862329",
        "bench16": "3024920",
        "perft5": "4865609",
    }
    for name, commands, _want in CASES:
        found = run_case(name, commands)
        if found:
            id_name = found
        text = (OUT_DIR / f"honesty_p_{name}.txt").read_text()
        nodes = ""
        for line in text.splitlines():
            parts = line.split()
            if "nodes" in parts:
                nodes = parts[parts.index("nodes") + 1]
        ok = nodes == expected[name]
        lines.append(f"{name} nodes {nodes} expected {expected[name]} {'OK' if ok else 'FAIL'}")
        print(lines[-1], flush=True)
        if not ok:
            raise SystemExit(f"honesty failed {name}")
    lines.insert(2, f"id_name={id_name}")
    lines.append("no setoption sent")
    (OUT_DIR / "HONESTY_P.txt").write_text("\n".join(lines) + "\n")
    print("HONESTY_P ok", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.TimeoutExpired as exc:
        print(f"TIMEOUT {exc}", file=sys.stderr)
        raise
