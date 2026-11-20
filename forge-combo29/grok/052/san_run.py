#!/usr/bin/env python3
"""Same runner for the sanitizer search and the deliberate heap-overflow canary."""
import hashlib
import os
import pathlib
import re
import subprocess
import time

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
    ("IdeaS28", "true"),
]
STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN_RE = re.compile(r"AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer|heap-buffer-overflow|stack-buffer-overflow")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.strip().split()
    if not parts or parts[0].startswith("#"):
        return ""
    if len(parts) >= 6 and parts[1] in ("w", "b") and parts[4].isdigit() and parts[5].isdigit():
        return " ".join(parts[:6])
    if len(parts) >= 4 and parts[1] in ("w", "b"):
        return " ".join(parts[:4]) + " 0 1"
    return line.strip()


def asan_count(exe: pathlib.Path) -> int:
    proc = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=False)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    repo = pathlib.Path(pathlib.Path.home().joinpath("grok_repo.txt").read_text().strip())
    seat = pathlib.Path.home().joinpath("grok_seat.txt").read_text().strip()
    out_dir = repo / "forge-combo29" / "grok" / seat
    exe = pathlib.Path(args.exe).resolve()
    fens = [fen_of(line) for line in pathlib.Path(args.fens).read_text().splitlines()]
    fens = [fen for fen in fens if fen]
    if args.limit:
        fens = fens[: args.limit]

    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=1"
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    log: list[str] = []

    def send(line: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        log.append(">> " + line + "\n")

    def read_until(done, timeout: float) -> bool:
        assert proc.stdout is not None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if line == "":
                log.append("<< EOF\n")
                return False
            log.append(line)
            low = line.lower()
            for phrase in STOP_PHRASES:
                if phrase.lower() in low:
                    raise SystemExit(f"STOP {phrase}: {line}")
            if done(line):
                return True
        raise SystemExit("timeout")

    id_name = "MISSING"
    finished = 0
    crashed = False
    try:
        send("uci")
        if not read_until(lambda line: line.startswith("uciok"), 60):
            crashed = True
        else:
            match = re.search(r"^id name (.+)$", "".join(log), re.M)
            id_name = match.group(1).strip() if match else "MISSING"
            send("isready")
            if not read_until(lambda line: line.startswith("readyok"), 60):
                crashed = True
        sent = [f"setoption name {name} value {value}" for name, value in S14]
        if not crashed:
            for line in sent:
                send(line)
                send("isready")
                if not read_until(lambda item: item.startswith("readyok"), 60):
                    crashed = True
                    break
        if not crashed:
            for index, fen in enumerate(fens, start=1):
                send("ucinewgame")
                send("isready")
                if not read_until(lambda line: line.startswith("readyok"), 60):
                    crashed = True
                    break
                send("position fen " + fen)
                send("isready")
                if not read_until(lambda line: line.startswith("readyok"), 60):
                    crashed = True
                    break
                send(f"go depth {args.depth}")
                if not read_until(lambda line: line.startswith("bestmove"), 180):
                    crashed = True
                    break
                finished = index
                print(f"san {index}", flush=True)
        else:
            sent = [f"setoption name {name} value {value}" for name, value in S14]
    finally:
        try:
            if proc.poll() is None:
                send("quit")
        except BrokenPipeError:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        err = ""
        if proc.stderr is not None:
            err = proc.stderr.read()
        (out_dir / f"{args.out}.txt").write_text("".join(log))
        (out_dir / f"{args.out}.err").write_text(err)
        san_lines = [line for line in err.splitlines() if SAN_RE.search(line)]
        nm_count = asan_count(exe)
        meta = [
            f"exe={exe}",
            f"sha256={sha256(exe)}",
            f"id_name={id_name}",
            f"nm_asan={nm_count}",
            "options_sent:",
            *sent,
            f"depth={args.depth}",
            f"positions_requested={len(fens)}",
            f"positions_finished={finished}",
            f"crashed={'yes' if crashed or proc.returncode not in (0, None) else 'no'}",
            f"sanitizer_lines={len(san_lines)}",
            "ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1",
            "UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1",
            "",
        ]
        (out_dir / f"{args.out}.meta").write_text("\n".join(meta))
        print(f"nm_asan {nm_count} sanitizer_lines {len(san_lines)} finished {finished} crashed {crashed}", flush=True)
        if san_lines:
            print(san_lines[0], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
