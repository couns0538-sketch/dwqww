#!/usr/bin/env python3
"""Run a fixed-depth set under a sanitizer build and count sanitizer lines.

Same runner for the real build and for the scratch build that reads past a
heap array on one chosen FEN. Stderr is read on a side thread so a sanitizer
report cannot fill the pipe.
"""
import hashlib
import os
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_search  # noqa: E402

SAN_MARKS = (
    "AddressSanitizer",
    "UndefinedBehaviorSanitizer",
    "runtime error:",
    "SUMMARY:",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def asan_count(exe: Path) -> int:
    proc = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=False)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    fens = Path(sys.argv[2])
    label = sys.argv[3]
    out = Path(sys.argv[4])
    depth = int(sys.argv[5])
    idea = sys.argv[6]
    limit = int(sys.argv[7]) if len(sys.argv) > 7 else 0
    out.mkdir(parents=True, exist_ok=True)
    positions = run_search.load_fens(fens)
    if limit:
        positions = positions[:limit]
    stderr_parts: list[bytes] = []

    def drain(pipe) -> None:
        while True:
            chunk = pipe.read(1 << 16)
            if not chunk:
                return
            stderr_parts.append(chunk)

    engine = run_search.Engine(str(exe))
    assert engine.proc.stderr is not None
    os.set_blocking(engine.proc.stderr.fileno(), True)
    thread = threading.Thread(target=drain, args=(engine.proc.stderr,), daemon=True)
    thread.start()
    options: list[str] = []
    id_name = ""
    status = "ok"
    try:
        engine.send("uci")
        engine.until("uciok", 60)
        for line in engine.log:
            if line.startswith("<< id name "):
                id_name = line[len("<< id name ") :]
        for name, value in run_search.S14:
            sent = f"setoption name {name} value {value}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 60)
        for name, value in (("Hash", "16"), ("Threads", "1")):
            sent = f"setoption name {name} value {value}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 60)
        if idea != "omit":
            sent = f"setoption name IdeaS44 value {idea}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 60)
        for index, fen in enumerate(positions, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.until("readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.until("readyok", 60)
            engine.send(f"go depth {depth}")
            while True:
                line = engine.read_line(180)
                if line.startswith("bestmove "):
                    break
            print(f"{label} {index} done", flush=True)
    except Exception as exc:
        status = f"stopped {exc}"
        print(f"FAIL {exc}", file=sys.stderr)
    finally:
        try:
            engine.send("quit")
        except Exception:
            pass
        try:
            engine.proc.wait(timeout=10)
        except Exception:
            engine.proc.kill()
        thread.join(timeout=5)
        (out / f"{label}.txt").write_text("\n".join(engine.log) + "\n", encoding="utf-8")
        stderr = b"".join(stderr_parts).decode("utf-8", "replace")
        (out / f"{label}.stderr").write_text(stderr, encoding="utf-8")
        marks = [line for line in stderr.splitlines() if any(mark in line for mark in SAN_MARKS)]
        (out / f"{label}.sanlines").write_text("".join(line + "\n" for line in marks), encoding="utf-8")
        count = asan_count(exe)
        meta = (
            f"exe_started={exe}\n"
            f"sha256={sha256(exe)}\n"
            f"id_name={id_name}\n"
            f"depth={depth}\n"
            f"positions={len(positions)}\n"
            f"status={status}\n"
            f"nm_asan_symbols={count}\n"
            f"sanitizer_lines={len(marks)}\n"
            "options_sent:\n"
            + "".join(f"  {line}\n" for line in options)
        )
        (out / f"{label}.meta").write_text(meta, encoding="utf-8")
        print(f"nm_asan_symbols={count} sanitizer_lines={len(marks)} status={status}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
