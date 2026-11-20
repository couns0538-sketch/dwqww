#!/usr/bin/env python3
"""Honesty check of one engine. Fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": ("bench 11", "312866"),
    "bench13": ("bench 13", "862329"),
    "bench16": ("bench 16", "3024920"),
    "perft5": ("go perft 5", "4865609"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: Path) -> tuple[str, str]:
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    raw = proc.stdout
    name = ""
    for line in raw.splitlines():
        if line.startswith("id name "):
            name = line[len("id name ") :]
            break
    return name, raw


def nodes_of(stem: str, raw: str) -> str:
    if stem.startswith("bench"):
        for line in raw.splitlines():
            if " nodes " in line and line.startswith("info string bench"):
                parts = line.split()
                return parts[parts.index("nodes") + 1]
        return "MISSING"
    last = "MISSING"
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nodes" and parts[1].isdigit():
            last = parts[1]
    return last


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_b.py EXE OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    name, uci_raw = id_name(exe)
    (out_dir / "uci_id.txt").write_text(uci_raw)
    rows = []
    for stem, (command, expected) in EXPECTED.items():
        proc = subprocess.run(
            [str(exe)],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        raw = proc.stdout
        if proc.stderr:
            raw += "\n# stderr\n" + proc.stderr
        (out_dir / f"{stem}.txt").write_text(raw)
        got = nodes_of(stem, proc.stdout)
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id_name {name}\n"
            f"command {command}\n"
            "options_sent none\n"
            f"nodes {got}\n"
            f"expected {expected}\n"
        )
        (out_dir / f"{stem}.meta").write_text(meta)
        rows.append((stem, command, got, expected, "yes" if got == expected else "NO"))
        print(f"{stem} {got} expected {expected}", flush=True)
    report = ["stem command nodes expected match"]
    for stem, command, got, expected, match in rows:
        report.append(f"{stem} {command} {got} {expected} {match}")
    (out_dir / "HONESTY_B.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    return 0 if all(match == "yes" for *_, match in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
