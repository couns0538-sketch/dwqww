#!/usr/bin/env python3
"""Honesty lines. A fresh process for each line. No setoption."""
import sys
from pathlib import Path

from uci_session import Session, UciError

LINES = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]


def expect_nodes(tag, command, text, want):
    if command.startswith("bench"):
        for line in text.splitlines():
            if line.startswith("info string bench depth"):
                parts = line.split()
                # info string bench depth D nodes N ...
                nodes = parts[parts.index("nodes") + 1]
                return nodes == want, nodes
        return False, "missing"
    for line in text.splitlines():
        if line.startswith("nodes "):
            nodes = line.split()[1]
            return nodes == want, nodes
    return False, "missing"


def main():
    exe = sys.argv[1]
    out_dir = Path(sys.argv[2])
    prefix = sys.argv[3]  # B or P
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    failed = False
    for tag, command, want in LINES:
        session = Session(exe)
        try:
            session.send(command)
            if command.startswith("bench"):
                session.read_until(lambda line: line.startswith("info string bench depth"), 300)
            else:
                session.read_until(lambda line: line.startswith("nodes "), 300)
            session.uci()
        except UciError as err:
            raw = "".join(session.log)
            (out_dir / f"honesty_{prefix}_{tag}.txt").write_text(raw)
            (out_dir / f"honesty_{prefix}_{tag}.txt.meta").write_text(session.meta(command))
            print(f"FAIL {tag} {err}")
            session.close()
            return 1
        raw = "".join(session.log)
        (out_dir / f"honesty_{prefix}_{tag}.txt").write_text(raw)
        (out_dir / f"honesty_{prefix}_{tag}.txt.meta").write_text(session.meta(command))
        session.close()
        ok, got = expect_nodes(tag, command, raw, want)
        summary.append(f"{command} nodes {got} expected {want} {'OK' if ok else 'FAIL'}")
        print(summary[-1])
        if not ok:
            failed = True
    text = "\n".join(summary) + "\n"
    (out_dir / f"HONESTY_{prefix}.txt").write_text(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
