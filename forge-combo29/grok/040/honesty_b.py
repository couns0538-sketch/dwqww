#!/usr/bin/env python3
"""Honesty check. One fresh engine process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    ident = subprocess.run(
        [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False
    )
    id_name = ""
    for line in ident.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    jobs = [
        ("bench11", "bench 11\nquit\n", 312866, "bench"),
        ("bench13", "bench 13\nquit\n", 862329, "bench"),
        ("bench16", "bench 16\nquit\n", 3024920, "bench"),
        ("perft5", "go perft 5\nquit\n", 4865609, "perft"),
    ]
    summary = []
    failed = False
    for name, payload, expected, kind in jobs:
        proc = subprocess.run(
            [str(exe)], input=payload, text=True, capture_output=True, timeout=180, check=False
        )
        raw = proc.stdout
        if proc.stderr:
            raw += "\n" + proc.stderr
        (out_dir / f"honesty_b_{name}.txt").write_text(raw)
        meta = "\n".join(
            [
                f"exe={exe}",
                f"sha256={digest}",
                f"id_name={id_name}",
                "options=",
                f"command={payload.strip()}",
                f"returncode={proc.returncode}",
            ]
        ) + "\n"
        (out_dir / f"honesty_b_{name}.meta").write_text(meta)
        nodes = None
        if kind == "bench":
            for line in raw.splitlines():
                if line.startswith("info string bench ") and " nodes " in line:
                    parts = line.split()
                    nodes = int(parts[parts.index("nodes") + 1])
        else:
            for line in raw.splitlines():
                if line.startswith("nodes "):
                    nodes = int(line.split()[1])
        ok = nodes == expected
        failed = failed or not ok
        summary.append(f"{name} nodes {nodes} expected {expected} {'OK' if ok else 'FAIL'}")
    text = "\n".join(summary) + "\n"
    (out_dir / "HONESTY_B.txt").write_text(text)
    sys.stdout.write(text)
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
