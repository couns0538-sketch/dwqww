#!/usr/bin/env python3
"""Same runner for the sanitizer proof and the deliberate heap over-read.
Raw lines, including a sanitizer report, are written even if the process dies.
"""
import hashlib
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
    ("Threads", "1"),
    ("Hash", "16"),
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        fen = " ".join(parts[:6]) if len(parts) >= 6 else line
        fens.append(fen)
        if len(fens) >= limit:
            break
    return fens


def main() -> int:
    if len(sys.argv) != 7:
        print("usage: san_run.py EXE FENS DEPTH LIMIT STEM EXTRA", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    depth = int(sys.argv[3])
    limit = int(sys.argv[4])
    stem = Path(sys.argv[5])
    extra: list[tuple[str, str]] = []
    if sys.argv[6] != "-":
        for item in sys.argv[6].split(","):
            name, value = item.split("=", 1)
            extra.append((name, value))
    options = S14 + extra
    fens = load_fens(Path(sys.argv[2]), limit)
    log: list[str] = []
    id_name = ""
    error = ""
    done_n = 0
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def send(line: str) -> None:
        assert proc.stdin is not None
        log.append("> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done) -> list[str]:
        assert proc.stdout is not None
        got: list[str] = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                log.append("< EOF")
                raise RuntimeError("engine closed stdout")
            line = line.rstrip("\r\n")
            log.append("< " + line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line)
            if done(line):
                return got

    try:
        send("uci")
        uci_lines = read_until(lambda line: line == "uciok")
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        send("isready")
        read_until(lambda line: line == "readyok")
        for fen in fens:
            for name, value in options:
                send(f"setoption name {name} value {value}")
                send("isready")
                read_until(lambda line: line == "readyok")
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line == "readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda line: line == "readyok")
            send(f"go depth {depth}")
            read_until(lambda line: line.startswith("bestmove "))
            done_n += 1
            print(f"done {done_n}", flush=True)
    except Exception as exc:  # noqa: BLE001 - the runner must keep the raw log
        error = str(exc)
        print(f"RUNNER_ERROR {error}", flush=True)
    finally:
        if proc.poll() is None:
            try:
                send("quit")
            except (BrokenPipeError, OSError):
                pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".txt").write_text("\n".join(log) + "\n")
    asan_lines = [line for line in log if "ERROR: AddressSanitizer" in line or "ERROR: UndefinedBehaviorSanitizer" in line or "runtime error:" in line]
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {id_name}",
        "options",
    ]
    meta.extend(f"setoption name {name} value {value}" for name, value in options)
    meta.append(f"depth {depth}")
    meta.append(f"limit {limit}")
    meta.append(f"positions_finished {done_n}")
    meta.append(f"returncode {proc.returncode}")
    meta.append(f"runner_error {error}")
    meta.append(f"sanitizer_lines {len(asan_lines)}")
    for line in asan_lines:
        meta.append("sanitizer " + line)
    stem.with_suffix(".meta").write_text("\n".join(meta) + "\n")
    print(f"sanitizer_lines {len(asan_lines)} returncode {proc.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
