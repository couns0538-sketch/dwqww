#!/usr/bin/env python3
"""Record the uci option lines for the late-parent spins and the check."""
import subprocess
import sys
from pathlib import Path

WANTED = (
    "LmrLateParentRelief",
    "LmrLateParentRelief_Index",
    "LmrLateParentRelief_Replies",
)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: uci_options.py <exe> <out-prefix>")
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2])
    result = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
    text = result.stdout + result.stderr
    out.with_suffix(".raw.txt").write_text(text) if False else Path(str(out) + ".raw.txt").write_text(text)
    hits = []
    for line in text.splitlines():
        if line.startswith("option name "):
            for name in WANTED:
                if line.startswith(f"option name {name} "):
                    hits.append(line)
    Path(str(out) + ".txt").write_text("\n".join(hits) + "\n")
    print("\n".join(hits))
    missing = [name for name in WANTED if not any(f"option name {name} " in line for line in hits)]
    if missing:
        raise SystemExit("missing " + " ".join(missing))


if __name__ == "__main__":
    main()
