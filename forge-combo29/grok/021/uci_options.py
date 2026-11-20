#!/usr/bin/env python3
"""Record the uci option list and require the IdeaS26 defaults."""
import hashlib
import subprocess
import sys
from pathlib import Path

REQUIRED = [
    "option name IdeaS26 type check default false",
    "option name IdeaS26_Floor type spin default 7 min 0 max 63",
    "option name IdeaS26_OrderDepth type spin default 6 min 0 max 63",
]


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    tag = sys.argv[2]
    out_dir = Path(__file__).resolve().parent
    process = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write("uci\n")
    process.stdin.flush()
    lines = []
    id_name = ""
    while True:
        line = process.stdout.readline()
        if line == "":
            raise RuntimeError("eof")
        lines.append(line)
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\r\n")
        if line.startswith("uciok"):
            break
    process.stdin.write("quit\n")
    process.stdin.flush()
    process.wait(timeout=30)
    raw = "".join(lines)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    (out_dir / f"{tag}.out").write_text(raw)
    (out_dir / f"{tag}.meta").write_text(f"exe={exe}\nsha256={digest}\nid_name={id_name}\noptions:\n")
    missing = [item for item in REQUIRED if item + "\n" not in raw and item + "\r\n" not in raw]
    if missing:
        print("MISSING", missing)
        return 1
    print("uci options OK")
    for item in REQUIRED:
        print(item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
