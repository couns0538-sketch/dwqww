#!/usr/bin/env python3
"""Same runner for the sanitizer build and for the deliberate-error scratch build.

S14, then the extra setoption lines, then the first N FENs at the given depth.
The .meta contains the exe, its sha256, id name, every option line, and
`nm -C <exe> | grep -c __asan_`. ASAN_OPTIONS turns leak detection off so a
shutdown leak is not counted; a heap or undefined-behavior report still is.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search_set  # noqa: E402


def asan_count(exe: Path) -> int:
    listed = subprocess.run(["nm", "-C", str(exe)], check=False, capture_output=True, text=True)
    return sum(1 for line in listed.stdout.splitlines() if "__asan_" in line)


def sanitizer_lines(text: str):
    hits = []
    for line in text.splitlines():
        if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line:
            hits.append(line)
    return hits


def main() -> int:
    if len(sys.argv) < 6:
        print("usage: sanitizer_run.py EXE FENS DEPTH OUT_PREFIX N [setoption ...]", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fen_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4])
    limit = int(sys.argv[5])
    extras = sys.argv[6:]
    fens = [search_set.fen_of(line.strip()) for line in fen_path.read_text().splitlines() if line.strip()]
    fens = fens[:limit]
    digest = search_set.sha256_file(exe)
    nm_hits = asan_count(exe)
    os.environ["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
    os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    engine = search_set.Engine(exe)
    option_lines = []
    id_name = ""
    rows = []
    try:
        engine.send("uci")
        prelude = engine.wait_for(lambda line: line.strip() == "uciok", 60)
        for line in prelude:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
        for name, value in (("Threads", "1"), ("Hash", "16")):
            sent = f"setoption name {name} value {value}"
            engine.send(sent)
            option_lines.append(sent)
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
        for name, value in search_set.S14:
            sent = f"setoption name {name} value {value}"
            engine.send(sent)
            option_lines.append(sent)
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
        for extra in extras:
            engine.send(extra)
            option_lines.append(extra)
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
            engine.send(f"go depth {depth}")
            body = engine.wait_for(lambda line: line.startswith("bestmove "), 180)
            rows.append(search_set.nodes_of(body))
            print(f"{index}/{len(fens)} nodes {rows[-1]}", flush=True)
    finally:
        raw = "".join(engine.transcript)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        prefix.with_suffix(".txt").write_text(raw)
        hits = sanitizer_lines(raw)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={id_name}\n"
            f"depth={depth}\n"
            f"positions={len(fens)}\n"
            f"fen_file={fen_path.resolve()}\n"
            f"nm -C {exe} | grep -c __asan_ = {nm_hits}\n"
            f"sanitizer_lines={len(hits)}\n"
            "options:\n" + "".join(line + "\n" for line in option_lines)
        )
        Path(str(prefix) + ".meta").write_text(meta)
        Path(str(prefix) + ".asan").write_text("\n".join(hits) + ("\n" if hits else ""))
        print(f"nm_asan={nm_hits} sanitizer_lines={len(hits)} positions_done={len(rows)}", flush=True)
        engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
