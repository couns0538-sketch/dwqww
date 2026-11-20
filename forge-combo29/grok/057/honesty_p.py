#!/usr/bin/env python3
"""Honesty check of exe P. One fresh process per command. No setoption."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_run import Engine, id_name

EXE = "/agent/repos/work/forge-combo29/build/forge"
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
        text = "\n".join(eng.lines) + "\n"
        name = id_name(eng.lines)
    finally:
        eng.close()
    return text, name


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
        (OUT / f"honesty_p_{name}.txt").write_text(raw)
        meta = (
            f"exe {EXE}\nsha256 {digest}\n{ident}\noptions (none)\n"
            f"commands {[s[0] for s in steps]}\n"
        )
        (OUT / f"honesty_p_{name}.meta").write_text(meta)
        parts.append(f"===== {name} =====\n{raw}")
        print(name, "OK", ident, flush=True)
    (OUT / "HONESTY_P.txt").write_text("\n".join(parts))
    print("wrote HONESTY_P.txt", flush=True)


if __name__ == "__main__":
    main()
