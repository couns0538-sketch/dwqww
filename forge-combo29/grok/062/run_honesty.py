#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption. Usage: run_honesty.py EXE STEM"""

import hashlib
import pathlib
import subprocess
import sys

CASES = [
    ("bench11", "bench 11\n", 312866),
    ("bench13", "bench 13\n", 862329),
    ("bench16", "bench 16\n", 3024920),
    ("perft5", "go perft 5\n", 4865609),
]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_once(exe: pathlib.Path, command: str) -> str:
    completed = subprocess.run(
        [str(exe)],
        input=command + "quit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = completed.stdout
    if completed.stderr:
        text += "\n---- stderr ----\n" + completed.stderr
    if completed.returncode != 0:
        text += f"\n---- exit {completed.returncode} ----\n"
    return text


def node_count(text: str, kind: str) -> int | None:
    if kind.startswith("bench"):
        for line in text.splitlines():
            if line.startswith("info string bench") and "nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    return last


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_honesty.py EXE STEM")
    exe = pathlib.Path(sys.argv[1])
    stem = sys.argv[2]
    out = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/062")
    digest = sha256(exe)
    uci = run_once(exe, "uci\n")
    (out / f"{stem}_idname.txt").write_text(uci, encoding="utf-8")
    name = "MISSING"
    for line in uci.splitlines():
        if line.startswith("id name "):
            name = line[len("id name "):]
    rows = []
    for kind, command, expected in CASES:
        raw = run_once(exe, command)
        file_stem = f"{stem}_{kind}"
        (out / f"{file_stem}.txt").write_text(raw, encoding="utf-8")
        got = node_count(raw, kind)
        status = "PASS" if got == expected else "FAIL"
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id name {name}\n"
            f"options sent none\n"
            f"command {command.strip()}\n"
            f"nodes {got}\n"
            f"expected {expected}\n"
            f"result {status}\n"
        )
        (out / f"{file_stem}.meta").write_text(meta, encoding="utf-8")
        rows.append((file_stem, got, expected, status))
    lines = [f"HONESTY {stem}", f"exe {exe}", f"sha256 {digest}", f"id name {name}"]
    for file_stem, got, expected, status in rows:
        lines.append(f"{file_stem} nodes {got} expected {expected} {status}")
    lines.append("ALL_PASS" if all(status == "PASS" for *_, status in rows) else "ALL_FAIL")
    (out / f"HONESTY_{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
