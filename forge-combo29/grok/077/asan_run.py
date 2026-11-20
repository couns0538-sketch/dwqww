#!/usr/bin/env python3
"""Same runner for the sanitizer search and the deliberate-error copy."""
import os
import subprocess
import sys
from pathlib import Path

from uci_session import Session, UciError
from search_set import S14, load_fens, nodes_of

def asan_count(exe):
    out = subprocess.run(["nm", "-C", exe], check=False, capture_output=True, text=True)
    return sum(1 for line in out.stdout.splitlines() if "__asan_" in line)


def main():
    exe = sys.argv[1]
    fen_path = sys.argv[2]
    depth = int(sys.argv[3])
    out_dir = Path(sys.argv[4])
    stem = sys.argv[5]
    switch = sys.argv[6]
    os.environ["ASAN_OPTIONS"] = "detect_leaks=0"
    os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    count = asan_count(exe)
    fens = load_fens(fen_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    session = Session(exe)
    node_rows = []
    error = ""
    try:
        session.uci()
        for name, value in S14:
            session.setoption(name, value)
        session.setoption("Threads", "1")
        session.setoption("Hash", "16")
        if switch != "omit":
            session.setoption("IdeaS44", switch)
        for index, fen in enumerate(fens):
            session.send("ucinewgame")
            session.ready()
            session.send(f"position fen {fen}")
            session.ready()
            session.send(f"go depth {depth}")
            block = session.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes = nodes_of(block)
            node_rows.append(f"{index} {nodes}")
            print(f"{index} {nodes}", flush=True)
    except UciError as err:
        error = str(err)
        print(f"STOP {err}", file=sys.stderr)
    raw = "".join(session.log)
    (out_dir / f"{stem}.txt").write_text(raw)
    asan_lines = [line.rstrip("\n") for line in raw.splitlines() if "AddressSanitizer" in line or "runtime error:" in line]
    meta = session.meta(f"go depth {depth} switch {switch}")
    meta += f"nm_asan_count={count}\n"
    meta += f"ASAN_OPTIONS={os.environ['ASAN_OPTIONS']}\n"
    meta += f"asan_or_ubsan_lines={len(asan_lines)}\n"
    if error:
        meta += f"runner_error={error}\n"
    (out_dir / f"{stem}.txt.meta").write_text(meta)
    if node_rows:
        (out_dir / f"{stem}.nodes").write_text("\n".join(node_rows) + "\n")
    (out_dir / f"{stem}.san").write_text("\n".join(asan_lines) + ("\n" if asan_lines else ""))
    session.close()
    print(f"nm_asan_count {count} sanitizer_lines {len(asan_lines)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
