#!/usr/bin/env python3
"""Save the uci option list. No setoption."""
import sys
from pathlib import Path

from uci_session import Session, UciError

def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    session = Session(exe)
    try:
        lines = session.uci()
    except UciError as err:
        out.write_text("".join(session.log))
        out.with_suffix(out.suffix + ".meta").write_text(session.meta("uci"))
        print(f"STOP {err}")
        session.close()
        return 1
    out.write_text("".join(session.log))
    out.with_suffix(out.suffix + ".meta").write_text(session.meta("uci"))
    session.close()
    for line in lines:
        if "IdeaS44" in line:
            print(line.rstrip("\n"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
