#!/usr/bin/env python3
"""Record the uci option list of one engine."""
import hashlib
import subprocess
import sys
from pathlib import Path

def main() -> None:
    exe = Path(sys.argv[1])
    out = Path(sys.argv[2])
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    completed = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    text = completed.stdout
    out.write_text(text)
    name = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            name = line[len("id name "):]
    meta = out.with_suffix(".meta")
    meta.write_text(f"exe={exe}\nsha256={digest}\nid_name={name}\noptions=\n")
    for line in text.splitlines():
        if "IdeaS15" in line:
            print(line)
    print(f"WROTE {out}")

if __name__ == "__main__":
    main()
