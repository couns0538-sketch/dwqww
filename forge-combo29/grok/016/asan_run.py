#!/usr/bin/env python3
"""Run S14 plus extra options under a sanitizer build. Saves every engine line.

The same script runs the real suite and the deliberate-error exe.
ASAN_OPTIONS disables leak detection so a heap overflow is the signal.
"""
import hashlib
import os
import select
import subprocess
import sys
from pathlib import Path

S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asan_count(exe: Path) -> int:
    proc = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=True)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: asan_run.py EXE FENS DEPTH OUT_PREFIX [Name=value ...]")
    exe = Path(sys.argv[1]).resolve()
    fens = [fen_of(line.strip()) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4])
    extras = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extras.append((name, value))
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        env=env,
    )
    log: list[str] = []
    pending = b""

    def send(line: str) -> None:
        assert proc.stdin is not None
        os.write(proc.stdin.fileno(), (line + "\n").encode())

    def read_until(done) -> list[str]:
        nonlocal pending
        assert proc.stdout is not None
        got: list[str] = []
        while True:
            if b"\n" not in pending:
                ready, _, _ = select.select([proc.stdout.fileno()], [], [], 90)
                if not ready:
                    note = "[runner] timeout waiting for the engine\n"
                    log.append(note)
                    got.append(note)
                    return got
                chunk = os.read(proc.stdout.fileno(), 1 << 16)
                if chunk == b"":
                    note = "[runner] engine stdout closed\n"
                    log.append(note)
                    got.append(note)
                    return got
                pending += chunk
            raw_line, pending = pending.split(b"\n", 1)
            line = raw_line.decode("utf-8", "replace") + "\n"
            log.append(line)
            got.append(line)
            stripped = line.strip()
            for mark in STOP_MARKS:
                if mark in stripped:
                    raise SystemExit(f"STOP {stripped}")
            if "ERROR: AddressSanitizer" in line or "runtime error:" in line or "SUMMARY: AddressSanitizer" in line:
                continue
            if done(stripped):
                return got

    id_name = ""
    died = False
    options: list[str] = []
    done_positions = 0
    try:
        send("uci")
        for line in read_until(lambda s: s == "uciok" or s.startswith("[runner]")):
            if line.startswith("id name "):
                id_name = line.strip()
            if line.startswith("[runner]"):
                died = True
        options = ["setoption name Hash value 16", "setoption name Threads value 1"]
        options += [f"setoption name {name} value {value}" for name, value in S14]
        options += [f"setoption name {name} value {value}" for name, value in extras]
        if not died:
            for option in options:
                send(option)
                send("isready")
                chunk = read_until(lambda s: s == "readyok" or s.startswith("[runner]"))
                if any(line.startswith("[runner]") for line in chunk):
                    died = True
                    break
        if not died:
            for fen in fens:
                send("ucinewgame")
                send("isready")
                if any(line.startswith("[runner]") for line in read_until(lambda s: s == "readyok" or s.startswith("[runner]"))):
                    died = True
                    break
                send(f"position fen {fen}")
                send("isready")
                if any(line.startswith("[runner]") for line in read_until(lambda s: s == "readyok" or s.startswith("[runner]"))):
                    died = True
                    break
                send(f"go depth {depth}")
                chunk = read_until(lambda s: s.startswith("bestmove ") or s.startswith("[runner]"))
                done_positions += 1
                print(f"pos {done_positions}/{len(fens)}", flush=True)
                if any(line.startswith("[runner]") for line in chunk):
                    died = True
                    break
        if proc.stdin is not None and proc.poll() is None:
            try:
                send("quit")
            except BrokenPipeError:
                pass
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
    raw = "".join(log)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".txt").write_text(raw)
    symbols = asan_count(exe)
    sanitizer_lines = [
        line.strip()
        for line in raw.splitlines()
        if "AddressSanitizer" in line or "runtime error:" in line or "SUMMARY:" in line
    ]
    meta = (
        f"exe {exe}\n"
        f"sha256 {sha256_file(exe)}\n"
        f"{id_name}\n"
        + "".join(f"option {line}\n" for line in options)
        + f"depth {depth}\n"
        f"positions_requested {len(fens)}\n"
        f"positions_finished {done_positions}\n"
        f"engine_died {died}\n"
        f"nm_asan_symbols {symbols}\n"
        f"sanitizer_lines {len(sanitizer_lines)}\n"
    )
    prefix.with_suffix(".meta").write_text(meta)
    print(f"nm_asan_symbols {symbols}")
    print(f"sanitizer_lines {len(sanitizer_lines)}")
    print(f"positions_finished {done_positions} of {len(fens)} died {died}")
    for line in sanitizer_lines:
        print(line)


if __name__ == "__main__":
    main()
