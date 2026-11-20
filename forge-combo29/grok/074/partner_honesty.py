#!/usr/bin/env python3
"""Honesty check on the partner build. Fresh process per line. No setoption."""

import sys
from pathlib import Path

from uci_session import Session, UciError, sha256_file, write_meta

EXE = "/agent/repos/partner-024/forge-combo29/build/forge"
OUT = Path(__file__).resolve().parent

EXPECTED = {
    "bench11": ("bench 11", "312866"),
    "bench13": ("bench 13", "862329"),
    "bench16": ("bench 16", "3024920"),
    "perft5": ("go perft 5", "4865609"),
}


def nodes_from(name, lines):
    if name.startswith("bench"):
        for line in lines:
            if line.startswith("info string bench depth") and " nodes " in line:
                parts = line.split()
                return parts[parts.index("nodes") + 1]
        return "MISSING"
    for line in reversed(lines):
        if line.startswith("nodes "):
            return line.split()[1]
    return "MISSING"


def main():
    failed = False
    lines_out = []
    for name, (command, expected) in EXPECTED.items():
        session = Session(EXE)
        try:
            session.send("uci")
            session.read_until(lambda line: line == "uciok", 30)
            id_name = "MISSING"
            for line in session.lines:
                if line.startswith("id name "):
                    id_name = line[len("id name ") :]
            session.send(command)
            if command.startswith("bench"):
                session.read_until(lambda line: line.startswith("info string bench depth"), 180)
            else:
                session.read_until(lambda line: line.startswith("nodes "), 180)
            got = nodes_from(name, session.lines)
            (OUT / f"partner_honesty_{name}.txt").write_text("\n".join(session.lines) + "\n", encoding="utf-8")
            write_meta(OUT / f"partner_honesty_{name}.meta", EXE, sha256_file(EXE), id_name, [])
        except UciError as exc:
            got = f"ERROR {exc}"
            failed = True
        finally:
            session.close()
        ok = got == expected
        if not ok:
            failed = True
        line = f"{command} nodes {got} expected {expected} {'OK' if ok else 'FAIL'}"
        lines_out.append(line)
        print(line, flush=True)
    (OUT / "partner_honesty.txt").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
