#!/usr/bin/env python3
"""One fresh engine process, no setoption. Saves raw output and a .meta file.

Usage: harness_honesty.py EXE OUTPREFIX COMMAND...
COMMAND is the engine line, for example: bench 11
or: go perft 5
"""
import hashlib
import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: harness_honesty.py EXE OUTPREFIX COMMAND...", file=sys.stderr)
        return 2
    exe = sys.argv[1]
    out_prefix = sys.argv[2]
    command = " ".join(sys.argv[3:])
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    script = "uci\n" + command + "\nquit\n"
    proc = subprocess.run(
        [exe],
        input=script,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=480,
        check=False,
    )
    raw = proc.stdout
    id_name = ""
    for line in raw.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    bad = ("unknown option", "invalid value", "invalid FEN", "illegal move")
    hit = [line for line in raw.splitlines() if any(b in line for b in bad)]
    open(out_prefix + ".txt", "w", encoding="utf-8").write(raw)
    meta = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={id_name}",
        "options=none",
        f"command={command}",
        f"exit={proc.returncode}",
    ]
    if hit:
        meta.append("STOPPED=" + hit[0])
    open(out_prefix + ".meta", "w", encoding="utf-8").write("\n".join(meta) + "\n")
    if hit or proc.returncode != 0:
        print("HONESTY FAIL", out_prefix, file=sys.stderr)
        return 1
    print(out_prefix, "bytes", len(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
