#!/usr/bin/env python3
"""Record the uci identity and option list. No setoption is sent."""
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_prefix = Path(sys.argv[2]).resolve()
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    proc = subprocess.run(
        [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60, check=False
    )
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    (out_prefix.parent / (out_prefix.name + ".txt")).write_text(proc.stdout)
    (out_prefix.parent / (out_prefix.name + ".err")).write_text(proc.stderr)
    id_name = ""
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    meta = f"exe {exe}\nsha256 {sha}\nid name {id_name}\noptions\ncommand 'uci'\nexit {proc.returncode}\n"
    (out_prefix.parent / (out_prefix.name + ".meta")).write_text(meta)
    wanted = (
        "option name IdeaS10 type check default false",
        "option name IdeaS10_Margin type spin default 80 min 0 max 2000",
        "option name IdeaS10_Flat type spin default 40 min 0 max 500",
        "option name IdeaS10_Probe type spin default 2 min 1 max 8",
        "option name IdeaS10_Close type spin default 30 min 0 max 500",
        "option name IdeaS10_Shrink type spin default 768 min 0 max 1024",
        "option name IdeaS10_MinDepth type spin default 4 min 1 max 32",
    )
    missing = [line for line in wanted if line not in proc.stdout.splitlines()]
    print(f"id name {id_name}")
    print(f"missing {len(missing)}")
    for line in missing:
        print("MISSING " + line)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
