#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path


def nodes_of(text: str) -> str:
    found = ""
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            index = parts.index("nodes")
            if index + 1 < len(parts):
                found = parts[index + 1]
    return found


def id_name_of(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    checks = [
        ("bench11", "bench 11", "312866"),
        ("bench13", "bench 13", "862329"),
        ("bench16", "bench 16", "3024920"),
        ("perft5", "go perft 5", "4865609"),
    ]
    rows = []
    failed = False
    for tag, command, expected in checks:
        payload = command + "\nuci\nquit\n"
        proc = subprocess.run(
            [str(exe)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        raw_path = out_dir / f"HONESTY_B_{tag}.txt"
        raw_path.write_text(proc.stdout)
        if proc.stderr:
            (out_dir / f"HONESTY_B_{tag}.err").write_text(proc.stderr)
        name = id_name_of(proc.stdout)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={name}\n"
            f"options_sent=\n"
            f"command={command}\n"
            f"returncode={proc.returncode}\n"
        )
        (out_dir / f"HONESTY_B_{tag}.meta").write_text(meta)
        got = nodes_of(proc.stdout)
        ok = got == expected and proc.returncode == 0 and name != ""
        failed = failed or not ok
        rows.append(f"{tag} nodes {got} expected {expected} ok {str(ok).lower()}")
    summary = "\n".join(rows) + "\n"
    (out_dir / "HONESTY_B.txt").write_text(summary)
    sys.stdout.write(summary)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
