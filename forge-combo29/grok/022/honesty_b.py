#!/usr/bin/env python3
"""Honesty check of exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/tmp/forge-b/forge")
OUT_DIR = Path(__file__).resolve().parent
CASES = [
    ("bench11", ["bench", "11"], 312866, "bench"),
    ("bench13", ["bench", "13"], 862329, "bench"),
    ("bench16", ["bench", "16"], 3024920, "bench"),
    ("perft5", ["go", "perft", "5"], 4865609, "perft"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_case(args: list[str]) -> str:
    # Measurement command first. uci afterwards only to record id name.
    script = " ".join(args) + "\nuci\nquit\n"
    proc = subprocess.run(
        [str(EXE)],
        input=script,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.returncode != 0:
        text += f"\n[exit {proc.returncode}]\n"
    if proc.stderr:
        text += "\n[stderr]\n" + proc.stderr
    return text


def parse_nodes(text: str, kind: str) -> int | None:
    if kind == "bench":
        for line in text.splitlines():
            if "info string bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    digest = sha256(EXE)
    summary = []
    failed = False
    for name, args, expected, kind in CASES:
        raw = run_case(args)
        raw_path = OUT_DIR / f"honesty_b_{name}.txt"
        raw_path.write_text(raw)
        got = parse_nodes(raw, kind)
        ok = got == expected
        if not ok:
            failed = True
        ident = id_name(raw)
        meta = (
            f"exe {EXE}\n"
            f"sha256 {digest}\n"
            f"id_name {ident}\n"
            f"options\n"
            f"command {' '.join(args)}\n"
            f"nodes {got}\n"
            f"expected {expected}\n"
            f"match {str(ok).lower()}\n"
        )
        (OUT_DIR / f"honesty_b_{name}.txt.meta").write_text(meta)
        summary.append(f"{name} nodes {got} expected {expected} match {str(ok).lower()}")
        print(summary[-1], flush=True)
    report = [
        f"exe {EXE}",
        f"sha256 {digest}",
        *summary,
        "FAIL" if failed else "PASS",
        "",
    ]
    (OUT_DIR / "HONESTY_B.txt").write_text("\n".join(report))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
