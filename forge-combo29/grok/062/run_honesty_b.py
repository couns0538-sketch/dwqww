#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""

import hashlib
import pathlib
import subprocess

EXE = pathlib.Path("/agent/repos/base/forge-combo29/build-rel/forge")
OUT = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/062")

CASES = [
    ("bench11", "bench 11\n", "honesty_b_bench11", 312866),
    ("bench13", "bench 13\n", "honesty_b_bench13", 862329),
    ("bench16", "bench 16\n", "honesty_b_bench16", 3024920),
    ("perft5", "go perft 5\n", "honesty_b_perft5", 4865609),
]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_once(command: str) -> str:
    completed = subprocess.run(
        [str(EXE)],
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


def id_name() -> str:
    text = run_once("uci\n")
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return "MISSING"


def node_count(text: str, kind: str) -> int | None:
    if kind.startswith("bench"):
        for line in text.splitlines():
            if "nodes " in line and line.startswith("info string bench"):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    return last


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    digest = sha256(EXE)
    name = id_name()
    (OUT / "honesty_b_idname.txt").write_text(run_once("uci\n"), encoding="utf-8")
    rows = []
    for kind, command, stem, expected in CASES:
        raw = run_once(command)
        (OUT / f"{stem}.txt").write_text(raw, encoding="utf-8")
        got = node_count(raw, kind)
        status = "PASS" if got == expected else "FAIL"
        meta = (
            f"exe {EXE}\n"
            f"sha256 {digest}\n"
            f"id name {name}\n"
            f"options sent none\n"
            f"command {command.strip()}\n"
            f"nodes {got}\n"
            f"expected {expected}\n"
            f"result {status}\n"
        )
        (OUT / f"{stem}.meta").write_text(meta, encoding="utf-8")
        rows.append((stem, got, expected, status))
    lines = ["HONESTY_B", f"exe {EXE}", f"sha256 {digest}", f"id name {name}"]
    for stem, got, expected, status in rows:
        lines.append(f"{stem} nodes {got} expected {expected} {status}")
    lines.append("ALL_PASS" if all(status == "PASS" for *_, status in rows) else "ALL_FAIL")
    (OUT / "HONESTY_B.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
