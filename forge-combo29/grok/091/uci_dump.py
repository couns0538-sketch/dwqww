#!/usr/bin/env python3
"""Save the uci option list. No setoption."""
import pathlib
import subprocess
import sys

def main():
    exe = sys.argv[1]
    out = pathlib.Path(sys.argv[2])
    proc = subprocess.run([exe], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
    out.write_text(proc.stdout)
    for line in proc.stdout.splitlines():
        if "IdeaK2" in line:
            print(line)
    return 0

if __name__ == "__main__":
    sys.exit(main())
