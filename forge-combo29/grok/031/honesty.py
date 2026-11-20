#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption is sent."""
import hashlib
import subprocess
import sys
from pathlib import Path

def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    tag = sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    ident = subprocess.run(
        [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60, check=False
    )
    id_name = ""
    for line in ident.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    (out_dir / f"honesty_{tag}_id.txt").write_text(ident.stdout)
    commands = [
        ("bench11", "bench 11\nquit\n", "312866"),
        ("bench13", "bench 13\nquit\n", "862329"),
        ("bench16", "bench 16\nquit\n", "3024920"),
        ("perft5", "go perft 5\nquit\n", "4865609"),
    ]
    failed = 0
    for name, command, expect in commands:
        proc = subprocess.run(
            [str(exe)], input=command, text=True, capture_output=True, timeout=300, check=False
        )
        raw_path = out_dir / f"honesty_{tag}_{name}.txt"
        raw_path.write_text(proc.stdout)
        (out_dir / f"honesty_{tag}_{name}.err").write_text(proc.stderr)
        meta = (
            f"exe {exe}\n"
            f"sha256 {sha}\n"
            f"id name {id_name}\n"
            f"options\n"
            f"command {command!r}\n"
            f"exit {proc.returncode}\n"
            f"id_source separate process, uci then quit, not sent before this command\n"
        )
        (out_dir / f"honesty_{tag}_{name}.meta").write_text(meta)
        ok = False
        if name.startswith("bench"):
            for line in proc.stdout.splitlines():
                if " nodes " in line:
                    parts = line.split()
                    if "nodes" in parts and parts[parts.index("nodes") + 1] == expect:
                        ok = True
        else:
            for line in proc.stdout.splitlines():
                if line == f"nodes {expect}":
                    ok = True
        print(f"{tag} {name} {'OK' if ok else 'FAIL'} expect {expect}")
        if not ok:
            failed = 1
            print(proc.stdout[-400:])
    return failed

if __name__ == "__main__":
    sys.exit(main())
