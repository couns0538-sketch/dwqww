#!/usr/bin/env python3
"""Fresh-process honesty check. No setoption. One process per command."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()

id_proc = subprocess.run(
    [str(exe)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=60,
)
id_name = ""
for line in id_proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break

commands = [
    ("bench11", "bench 11\nquit\n"),
    ("bench13", "bench 13\nquit\n"),
    ("bench16", "bench 16\nquit\n"),
    ("perft5", "go perft 5\nquit\n"),
]

summary = []
for name, payload in commands:
    proc = subprocess.run(
        [str(exe)],
        input=payload,
        text=True,
        capture_output=True,
        timeout=300,
    )
    raw_path = out_dir / f"honesty_B_{name}.txt"
    raw_path.write_text(proc.stdout)
    meta = (
        f"exe={exe}\n"
        f"sha256={sha}\n"
        f"id_name={id_name}\n"
        f"options_sent=none\n"
        f"stdin={payload!r}\n"
        f"returncode={proc.returncode}\n"
    )
    if proc.stderr:
        meta += "stderr_begin\n" + proc.stderr + "stderr_end\n"
    (out_dir / f"honesty_B_{name}.meta").write_text(meta)
    last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    summary.append(f"{name} rc={proc.returncode} {last}")
    print(summary[-1], flush=True)

(out_dir / "HONESTY_B.txt").write_text(
    f"exe={exe}\nsha256={sha}\nid_name={id_name}\n" + "\n".join(summary) + "\n"
)
print("WROTE", out_dir / "HONESTY_B.txt")
