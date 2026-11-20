#!/usr/bin/env python3
"""Save the uci option list for one exe, plus a meta file."""
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: show_options.py EXE RAW META", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    raw = Path(sys.argv[2])
    meta = Path(sys.argv[3])
    result = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    text = result.stdout + result.stderr
    raw.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    name = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            name = line[len("id name ") :]
            break
    interesting = [line for line in text.splitlines() if "IdeaA2" in line]
    meta.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={digest}",
                f"id_name={name}",
                "options:",
                "(none)",
                "matched:",
                *interesting,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("\n".join(interesting))
    return 0 if len(interesting) == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
