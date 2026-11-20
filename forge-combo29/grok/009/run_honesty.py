#!/usr/bin/env python3
"""Fresh-process honesty checks. No setoption. Raw stdout saved per command."""
import hashlib
import subprocess
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 4:
        print("usage: run_honesty.py EXE OUTDIR TAG", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outdir = Path(sys.argv[2]).resolve()
    tag = sys.argv[3]
    outdir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    id_proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    id_name = ""
    for line in id_proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    commands = [
        ("bench11", "bench 11\nquit\n"),
        ("bench13", "bench 13\nquit\n"),
        ("bench16", "bench 16\nquit\n"),
        ("perft5", "go perft 5\nquit\n"),
    ]
    for name, payload in commands:
        proc = subprocess.run([str(exe)], input=payload, text=True, capture_output=True, check=False)
        raw = outdir / f"honesty_{tag}_{name}.txt"
        raw.write_text(proc.stdout)
        if proc.stderr:
            (outdir / f"honesty_{tag}_{name}.err").write_text(proc.stderr)
        meta = outdir / f"honesty_{tag}_{name}.meta"
        meta.write_text(
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id_name {id_name}\n"
            f"options_sent none\n"
            f"command {payload.strip()}\n"
            f"returncode {proc.returncode}\n"
        )
        print(f"wrote {raw}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
