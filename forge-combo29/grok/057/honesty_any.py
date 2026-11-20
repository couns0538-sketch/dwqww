#!/usr/bin/env python3
"""Honesty check of one exe. No setoption. Usage: honesty_any.py <exe> <prefix>"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_run import Engine, id_name

EXE = sys.argv[1]
PREFIX = sys.argv[2]
OUT = Path(__file__).resolve().parent


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def once(steps, timeout):
    eng = Engine(EXE)
    try:
        for command, marker in steps:
            eng.send(command, marker, timeout)
        return "\n".join(eng.lines) + "\n", id_name(eng.lines)
    finally:
        eng.close()


def main():
    digest = sha256(EXE)
    jobs = [
        ("bench11", [("uci", "uciok"), ("bench 11", "info string bench depth 11 ")], 60),
        ("bench13", [("uci", "uciok"), ("bench 13", "info string bench depth 13 ")], 60),
        ("bench16", [("uci", "uciok"), ("bench 16", "info string bench depth 16 ")], 60),
        ("perft5", [("uci", "uciok"), ("position startpos", None), ("isready", "readyok"), ("go perft 5", "nodes ")], 60),
    ]
    parts = [f"exe {EXE}\nsha256 {digest}\n"]
    for name, steps, timeout in jobs:
        raw, ident = once(steps, timeout)
        (OUT / f"{PREFIX}_{name}.txt").write_text(raw)
        (OUT / f"{PREFIX}_{name}.meta").write_text(
            f"exe {EXE}\nsha256 {digest}\n{ident}\noptions (none)\ncommands {[s[0] for s in steps]}\n"
        )
        parts.append(f"===== {name} =====\n{raw}")
        print(name, "OK", flush=True)
    (OUT / f"{PREFIX}.txt").write_text("\n".join(parts))
    print("wrote", PREFIX, flush=True)


if __name__ == "__main__":
    main()
