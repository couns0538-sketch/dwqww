#!/usr/bin/env python3
"""Same runner for the sanitizer proof and the deliberate heap-overflow check.

Usage:
  asan_runner.py EXE OUTPREFIX FENFILE DEPTH [LIMIT] [setoption lines...]
Writes OUTPREFIX.txt, .raw, .meta. The meta includes the __asan_ symbol count.
A sanitizer line is kept in the raw file. Exit 0 when the engine finishes and
no sanitizer line was seen. Exit 3 when a sanitizer line was seen. Exit 2 on
any other protocol failure.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    out_prefix = Path(sys.argv[2])
    fen_file = Path(sys.argv[3])
    depth = int(sys.argv[4])
    rest = sys.argv[5:]
    limit = None
    if rest and rest[0].lstrip("-").isdigit():
        limit = int(rest[0])
        rest = rest[1:]
    extra = rest
    fens = []
    for line in fen_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line.split(";")[0].strip())
    if limit is not None:
        fens = fens[:limit]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    raw: list[str] = []
    rows: list[str] = []
    id_name = ""
    sanitizer: list[str] = []
    failure = ""

    def send(line: str) -> None:
        if proc.stdin is None:
            return
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def take() -> str:
        if proc.stdout is None:
            return ""
        line = proc.stdout.readline()
        if line == "":
            return ""
        line = line.rstrip("\n")
        raw.append(line)
        if any(s in line for s in SAN):
            sanitizer.append(line)
        return line

    def until(marker: str) -> bool:
        nonlocal failure
        while True:
            line = take()
            if line == "":
                failure = "engine closed while waiting for " + marker
                return False
            low = line.lower()
            if any(b.lower() in low for b in BAD):
                failure = "STOP " + line
                return False
            if sanitizer:
                failure = "sanitizer"
                return False
            if marker in line:
                return True

    send("uci")
    if not until("uciok"):
        pass
    else:
        for line in raw:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
                break
        options = S14 + extra
        ok = True
        for opt in options:
            send(opt)
            send("isready")
            if not until("readyok"):
                ok = False
                break
        if ok:
            for index, fen in enumerate(fens, start=1):
                send("ucinewgame")
                send("isready")
                if not until("readyok"):
                    break
                send("position fen " + fen)
                send("isready")
                if not until("readyok"):
                    break
                send(f"go depth {depth}")
                nodes = None
                while True:
                    line = take()
                    if line == "":
                        failure = "engine closed during go"
                        break
                    if any(s in line for s in SAN):
                        failure = "sanitizer"
                        break
                    if " nodes " in line and "nodes" in line.split():
                        parts = line.split()
                        nodes = int(parts[parts.index("nodes") + 1])
                    if line.startswith("bestmove"):
                        break
                if failure:
                    break
                if nodes is None:
                    failure = f"no nodes for position {index}"
                    break
                rows.append(f"{index} {nodes}")
            if not failure:
                send("quit")
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
    if proc.poll() is None:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    # Drain anything the sanitizer wrote after abort.
    if proc.stdout is not None:
        rest_out = proc.stdout.read()
        if rest_out:
            for line in rest_out.splitlines():
                raw.append(line)
                if any(s in line for s in SAN):
                    sanitizer.append(line)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    stem = out_prefix.parent / out_prefix.name
    stem.with_suffix(".txt").write_text(("\n".join(rows) + "\n") if rows else "")
    stem.with_suffix(".raw").write_text(("\n".join(raw) + "\n") if raw else "")
    meta = [
        f"exe {exe}",
        f"sha256 {sha}",
        f"id name {id_name}",
        f"nm_asan_count {asan_count}",
        "ASAN_OPTIONS detect_leaks=0:halt_on_error=1:abort_on_error=1",
        "UBSAN_OPTIONS halt_on_error=1:abort_on_error=1:print_stacktrace=1",
        "options:",
    ]
    meta.extend(S14 + extra)
    meta.append(f"depth {depth}")
    meta.append(f"positions {len(fens)}")
    meta.append(f"fenfile {fen_file.resolve()}")
    if failure:
        meta.append("failure " + failure)
    meta.append(f"sanitizer_lines {len(sanitizer)}")
    stem.with_suffix(".meta").write_text("\n".join(meta) + "\n")
    print(f"asan_symbols {asan_count} positions_done {len(rows)} sanitizer_lines {len(sanitizer)} failure {failure or 'none'}")
    if sanitizer:
        print(sanitizer[0])
        sys.exit(3)
    if failure:
        sys.exit(2)


if __name__ == "__main__":
    main()
