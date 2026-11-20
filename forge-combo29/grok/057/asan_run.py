#!/usr/bin/env python3
"""Same runner for the sanitizer proof and the deliberate-error scratch.
Usage: asan_run.py <exe> <positions> <depth> <tag> [limit] [Name Value ...]
Writes <tag>.rows.txt <tag>.raw.txt <tag>.stderr.txt <tag>.meta
A sanitizer abort is recorded; it does not hide the stderr.
"""
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_run import Engine, id_name
import suite_depth

os.environ["ASAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:detect_leaks=0"
os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nm_asan(exe):
    import subprocess
    out = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in out.stdout.splitlines() if "__asan_" in line)


def main():
    exe = sys.argv[1]
    pos_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    tag = sys.argv[4]
    rest = sys.argv[5:]
    limit = 0
    if rest and rest[0].isdigit():
        limit = int(rest[0])
        rest = rest[1:]
    extra = list(zip(rest[0::2], rest[1::2]))
    out = Path(__file__).resolve().parent
    fens = []
    for line in pos_path.read_text().splitlines():
        fen = suite_depth.fen_of(line)
        if fen:
            fens.append(fen)
    if limit:
        fens = fens[:limit]
    digest = sha256(exe)
    asan_count = nm_asan(exe)
    eng = Engine(exe)
    option_lines = []
    rows = []
    note = "completed"
    ident = "id name MISSING"
    try:
        eng.send("uci", "uciok", 60)
        ident = id_name(eng.lines)
        setup = [("Threads", "1"), ("Hash", "16")] + suite_depth.S14 + extra
        for name, value in setup:
            command = f"setoption name {name} value {value}"
            option_lines.append(command)
            eng.send(command, None, 60)
            eng.send("isready", "readyok", 60)
        for index, fen in enumerate(fens):
            before = len(eng.lines)
            eng.send("ucinewgame", None, 60)
            eng.send("isready", "readyok", 90)
            eng.send("position fen " + fen, None, 60)
            eng.send("isready", "readyok", 90)
            eng.send(f"go depth {depth}", "bestmove ", 300)
            got_depth, nodes, score, best = suite_depth.last_info_nodes(eng.lines, before)
            rows.append(f"{index} {nodes} {got_depth} {score} {best} {fen}")
            print(f"{tag} {index} {nodes}", flush=True)
    except (SystemExit, OSError, BrokenPipeError) as exc:
        note = "stopped " + str(exc).splitlines()[0]
        print(note, flush=True)
        ident = id_name(eng.lines)
    finally:
        eng.close()
        err_text = eng.stderr.decode("utf-8", "replace")
        if ("runtime error:" in err_text or "AddressSanitizer" in err_text
                or "UndefinedBehaviorSanitizer" in err_text):
            note = "sanitizer reported"
    (out / f"{tag}.rows.txt").write_text(("\n".join(rows) + "\n") if rows else "")
    (out / f"{tag}.raw.txt").write_text("\n".join(eng.lines) + "\n")
    (out / f"{tag}.stderr.txt").write_text(err_text)
    meta = (
        f"exe {exe}\nsha256 {digest}\n{ident}\n"
        f"nm_asan_count {asan_count}\n"
        + "\n".join(option_lines)
        + f"\ndepth {depth}\npositions_finished {len(rows)}\nnote {note}\n"
    )
    (out / f"{tag}.meta").write_text(meta)
    print(f"{tag} asan_symbols {asan_count} finished {len(rows)} note {note}", flush=True)


if __name__ == "__main__":
    main()
