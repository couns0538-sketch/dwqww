#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption.

usage: honesty_check.py EXE PREFIX
PREFIX honesty_p writes honesty_p_bench11.txt and HONESTY_P.txt
"""
import hashlib
import subprocess
import sys
from pathlib import Path

CASES = [
    ("bench11", ["bench", "11"], 312866, "bench"),
    ("bench13", ["bench", "13"], 862329, "bench"),
    ("bench16", ["bench", "16"], 3024920, "bench"),
    ("perft5", ["go", "perft", "5"], 4865609, "perft"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_nodes(text: str, kind: str):
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


def main() -> int:
    exe = Path(sys.argv[1])
    prefix = sys.argv[2]
    out_dir = Path(__file__).resolve().parent
    digest = sha256(exe)
    summary = []
    failed = False
    for name, args, expected, kind in CASES:
        script = " ".join(args) + "\nuci\nquit\n"
        proc = subprocess.run([str(exe)], input=script, text=True, capture_output=True, timeout=180, check=False)
        text = proc.stdout
        if proc.returncode != 0:
            text += f"\n[exit {proc.returncode}]\n"
        if proc.stderr:
            text += "\n[stderr]\n" + proc.stderr
        raw_path = out_dir / f"{prefix}_{name}.txt"
        raw_path.write_text(text)
        got = parse_nodes(text, kind)
        ok = got == expected
        failed = failed or not ok
        ident = ""
        for line in text.splitlines():
            if line.startswith("id name "):
                ident = line[len("id name ") :]
                break
        meta = (
            f"exe {exe}\nsha256 {digest}\nid_name {ident}\noptions\n"
            f"command {' '.join(args)}\nnodes {got}\nexpected {expected}\nmatch {str(ok).lower()}\n"
        )
        raw_path.with_suffix(raw_path.suffix + ".meta").write_text(meta)
        summary.append(f"{name} nodes {got} expected {expected} match {str(ok).lower()}")
        print(summary[-1], flush=True)
    label = prefix[len("honesty_") :].upper() if prefix.startswith("honesty_") else prefix.upper()
    report = [f"exe {exe}", f"sha256 {digest}", *summary, "FAIL" if failed else "PASS", ""]
    (out_dir / f"HONESTY_{label}.txt").write_text("\n".join(report))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
