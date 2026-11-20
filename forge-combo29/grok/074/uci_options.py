#!/usr/bin/env python3
"""Record the uci option list from exe P. No setoption."""

import sys
from pathlib import Path

from uci_session import Session, UciError, sha256_file, write_meta

EXE = "/agent/repos/work/forge-combo29/build/forge"
OUT = Path(__file__).resolve().parent


def main():
    session = Session(EXE)
    try:
        session.send("uci")
        session.read_until(lambda line: line == "uciok", 30)
    except UciError as exc:
        print(f"STOP {exc}")
        sys.exit(1)
    finally:
        session.close()
    id_name = "MISSING"
    options = []
    for line in session.lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        if line.startswith("option name "):
            options.append(line)
    (OUT / "uci_p.txt").write_text("\n".join(session.lines) + "\n", encoding="utf-8")
    write_meta(OUT / "uci_p.meta", EXE, sha256_file(EXE), id_name, [])
    wanted = [line for line in options if "IdeaS32" in line]
    print(f"option_lines {len(options)}")
    for line in wanted:
        print(line)
    if len(wanted) < 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
