#!/usr/bin/env python3
"""Record the uci answer and whether named options appear with a default."""
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    exe = Path(sys.argv[1])
    out = Path(sys.argv[2])
    wanted = sys.argv[3:]
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30)
    text = proc.stdout + (proc.stderr or "")
    out.write_text(text)
    ident = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            ident = line[len("id name ") :].strip()
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    Path(str(out) + ".meta").write_text(
        "\n".join(
            [
                f"exe: {exe}",
                f"sha256: {digest}",
                f"id name: {ident}",
                "options sent:",
                "(none)",
                "commands: uci / quit",
                "",
            ]
        )
    )
    for name in wanted:
        hits = [line for line in text.splitlines() if line.startswith(f"option name {name} ")]
        print(f"{name} {hits[0] if hits else 'MISSING'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
