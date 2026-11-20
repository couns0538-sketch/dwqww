#!/usr/bin/env python3
"""Record the uci answer and the lines for the new options."""
import subprocess
import sys
from pathlib import Path


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    proc = subprocess.run(
        [str(exe)],
        input="uci\nisready\nquit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    text = proc.stdout
    out.write_text(text)
    want = (
        "option name IdeaA6 type check default false",
        "option name IdeaA6_TtBeta type spin default -2 min -8 max 2",
        "option name IdeaA6_Cut type spin default -1 min -8 max 2",
    )
    print("option\tpresent")
    for line in want:
        print(f"{line}\t{'yes' if line in text else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
