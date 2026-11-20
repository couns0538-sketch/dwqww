#!/usr/bin/env python3
"""Honesty check on exe B. One fresh process per line. No setoption."""

import sys
from pathlib import Path

from uci_session import Session, UciError, sha256_file, write_meta

EXE = "/agent/repos/base/forge-combo29/build/forge"
OUT = Path(__file__).resolve().parent

EXPECTED = {
    "bench11": ("bench 11", "312866"),
    "bench13": ("bench 13", "862329"),
    "bench16": ("bench 16", "3024920"),
    "perft5": ("go perft 5", "4865609"),
}


def id_name_from(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name ") :]
    return "MISSING"


def nodes_from(kind, lines):
    if kind.startswith("bench"):
        for line in lines:
            if line.startswith("info string bench depth"):
                parts = line.split()
                if "nodes" in parts:
                    return parts[parts.index("nodes") + 1]
        return "MISSING"
    for line in reversed(lines):
        if line.startswith("nodes "):
            return line.split()[1]
    return "MISSING"


def run_case(name, command):
    raw_path = OUT / f"honesty_b_{name}.txt"
    meta_path = OUT / f"honesty_b_{name}.meta"
    session = Session(EXE)
    try:
        session.send("uci")
        session.read_until(lambda line: line == "uciok", 30)
        id_name = id_name_from(session.lines)
        session.send(command)
        if command.startswith("bench"):
            session.read_until(lambda line: line.startswith("info string bench depth"), 180)
        else:
            session.read_until(lambda line: line.startswith("nodes "), 180)
        digest = sha256_file(EXE)
        raw_path.write_text("\n".join(session.lines) + "\n", encoding="utf-8")
        write_meta(meta_path, EXE, digest, id_name, [])
        got = nodes_from(name, session.lines)
        return got
    finally:
        session.close()


def main():
    summary = []
    failed = False
    for name, (command, expected) in EXPECTED.items():
        try:
            got = run_case(name, command)
        except UciError as exc:
            got = f"ERROR {exc}"
            failed = True
        ok = got == expected
        if not ok:
            failed = True
        line = f"{command} nodes {got} expected {expected} {'OK' if ok else 'FAIL'}"
        summary.append(line)
        print(line, flush=True)
    text = "\n".join(summary) + "\n"
    (OUT / "HONESTY_B.txt").write_text(text, encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
