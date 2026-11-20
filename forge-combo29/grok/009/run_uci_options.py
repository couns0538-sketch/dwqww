#!/usr/bin/env python3
"""Save the uci option list. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run_uci_options.py EXE OUTPREFIX", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outprefix = Path(sys.argv[2])
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    text = proc.stdout
    outprefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(outprefix) + ".txt").write_text(text)
    id_name = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    Path(str(outprefix) + ".meta").write_text(
        f"exe {exe}\nsha256 {digest}\nid_name {id_name}\noptions_sent none\ncommand uci\nreturncode {proc.returncode}\n"
    )
    for line in text.splitlines():
        if "IdeaS23_" in line or line.startswith("option name AspCappedReopen "):
            print(line)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
