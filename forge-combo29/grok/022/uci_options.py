#!/usr/bin/env python3
"""Record the uci option list. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    exe = Path(sys.argv[1])
    out = Path(sys.argv[2])
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
    text = proc.stdout
    if proc.stderr:
        text += "\n[stderr]\n" + proc.stderr
    out.write_text(text)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    ident = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            ident = line[len("id name ") :]
    out.with_suffix(out.suffix + ".meta").write_text(f"exe {exe}\nsha256 {digest}\nid_name {ident}\noptions\n")
    for needle in ("option name IdeaS27 type check default false", "option name IdeaS27_DeadZone type spin default 64"):
        print(("FOUND " if needle in text else "MISSING ") + needle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
