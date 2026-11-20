#!/usr/bin/env python3
"""Honesty check of an exe. One fresh process per line. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
PREFIX = sys.argv[3]
EXPECT = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}


def run_fresh(command: str) -> str:
    proc = subprocess.run([str(EXE)], input=command + "\nquit\n", text=True, capture_output=True, timeout=300, check=False)
    text = proc.stdout + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(f"exit {proc.returncode}\n{text}")
    for bad in ("unknown option", "invalid value", "invalid FEN", "illegal move"):
        if bad in text:
            raise SystemExit(f"STOP {bad}\n{text}")
    return text


def nodes_of(text: str) -> int:
    found = None
    for line in text.splitlines():
        parts = line.split()
        for i, part in enumerate(parts):
            if part == "nodes" and i + 1 < len(parts):
                found = int(parts[i + 1])
    if found is None:
        raise SystemExit(text)
    return found


def main() -> None:
    digest = hashlib.sha256(EXE.read_bytes()).hexdigest()
    name = ""
    ident = subprocess.run([str(EXE)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
    for line in ident.stdout.splitlines():
        if line.startswith("id name "):
            name = line[len("id name ") :]
    lines = []
    ok = True
    for key, (command, want) in EXPECT.items():
        text = run_fresh(command)
        (OUT / f"{PREFIX}_{key}.txt").write_text(text)
        got = nodes_of(text)
        status = "PASS" if got == want else "FAIL"
        if got != want:
            ok = False
        lines.append(f"{command} -> nodes {got} expect {want} {status}")
        (OUT / f"{PREFIX}_{key}.meta").write_text(
            f"exe={EXE}\nsha256={digest}\nid_name={name}\noption_lines_sent=\ncommand={command}\n"
        )
    report = "\n".join(lines) + ("\nALL PASS\n" if ok else "\nALL FAIL\n")
    (OUT / f"{PREFIX}_HONESTY.txt").write_text(report)
    print(report, end="")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
