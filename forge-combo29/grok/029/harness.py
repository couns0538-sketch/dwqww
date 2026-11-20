#!/usr/bin/env python3
"""UCI harness for seat 029. Stops on unknown option, invalid value, invalid FEN, illegal move."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def engine_id_name(exe: Path) -> str:
    process = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"},
    )
    output, _ = process.communicate("uci\nquit\n", timeout=60)
    for line in output.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :].strip()
    raise SystemExit("no id name from " + str(exe))


class EngineClosed(SystemExit):
    def __init__(self, lines: list[str]):
        super().__init__("engine closed stdout early")
        self.lines = lines


def check_line(line: str) -> None:
    low = line.lower()
    for token in BAD:
        if token in low:
            raise SystemExit("STOP " + line)


class Engine:
    def __init__(self, exe: Path, env: dict | None = None):
        self.exe = exe
        self.options: list[str] = []
        self.process = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

    def send(self, line: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.process.stdout is not None
        lines: list[str] = []
        while True:
            line = self.process.stdout.readline()
            if line == "":
                raise EngineClosed(lines)
            line = line.rstrip("\r\n")
            lines.append(line)
            check_line(line)
            if done(line):
                return lines

    def ready(self) -> list[str]:
        self.send("isready")
        return self.read_until(lambda line: line == "readyok")

    def setoption(self, name: str, value: str) -> list[str]:
        command = f"setoption name {name} value {value}"
        self.options.append(command)
        self.send(command)
        return self.ready()

    def close(self) -> None:
        try:
            self.send("quit")
            self.process.wait(timeout=20)
        except Exception:
            self.process.kill()


def write_meta(path: Path, exe: Path, options: list[str], asan: bool = False) -> None:
    text = [
        f"exe: {exe}",
        f"sha256: {sha256_file(exe)}",
        f"id_name: {engine_id_name(exe)}",
        "options:",
    ]
    if options:
        text.extend(options)
    else:
        text.append("(none)")
    if asan:
        counted = subprocess.run(
            ["bash", "-lc", f"nm -C {exe} | grep -c __asan_ || true"],
            check=False,
            capture_output=True,
            text=True,
        )
        text.append("nm_asan_count: " + counted.stdout.strip())
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def run_honesty(exe: Path, out_dir: Path, label: str) -> None:
    jobs = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench ")),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes ")),
    ]
    summary = []
    for name, command, done in jobs:
        engine = Engine(exe)
        try:
            engine.send(command)
            lines = engine.read_until(done)
            engine.send("quit")
            engine.process.wait(timeout=30)
        finally:
            if engine.process.poll() is None:
                engine.process.kill()
        raw = out_dir / f"HONESTY_{label}_{name}.txt"
        raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
        write_meta(out_dir / f"HONESTY_{label}_{name}.meta", exe, [])
        summary.append(lines[-1] if lines else "")
        print(label, name, lines[-1] if lines else "EMPTY", flush=True)
    (out_dir / f"HONESTY_{label}.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit("bad fen line " + line)
        fens.append(" ".join(parts[:6]) if len(parts) >= 6 else line)
    return fens


def nodes_of(lines: list[str]) -> int:
    found = None
    for line in lines:
        if " nodes " not in line:
            continue
        bits = line.split()
        if "nodes" in bits:
            found = int(bits[bits.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes in\n" + "\n".join(lines[-15:]))
    return found


def run_suite(exe: Path, fen_file: Path, depth: int, out_path: Path, extra: list[tuple[str, str]], asan: bool = False) -> None:
    fens = load_fens(fen_file)
    if asan:
        os_env = dict(**os.environ)
        os_env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
        os_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    else:
        os_env = None
    engine = Engine(exe, os_env)
    transcript: list[str] = []
    try:
        transcript += engine.setoption("Hash", "16")
        transcript += engine.setoption("Threads", "1")
        for name, value in extra:
            transcript += engine.setoption(name, value)
        for index, fen in enumerate(fens):
            for name, value in S14:
                transcript += engine.setoption(name, value)
            engine.send("ucinewgame")
            transcript += engine.ready()
            engine.send("position fen " + fen)
            transcript += engine.ready()
            engine.send(f"go depth {depth}")
            lines = engine.read_until(lambda line: line.startswith("bestmove "))
            transcript += lines
            if (index + 1) % 25 == 0 or index + 1 == len(fens):
                print(f"{out_path.name} {index + 1}/{len(fens)}", flush=True)
    except EngineClosed as stopped:
        transcript.extend(stopped.lines)
        transcript.append(str(stopped))
        if not asan:
            out_path.write_text("\n".join(transcript) + "\n", encoding="utf-8")
            raise
    finally:
        engine.close()
    out_path.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    write_meta(out_path.with_suffix(out_path.suffix + ".meta"), exe, engine.options, asan=asan)
    sanitizer_lines = [
        line for line in transcript
        if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line
    ]
    if asan:
        print(f"sanitizer_lines {len(sanitizer_lines)}", flush=True)
        for line in sanitizer_lines[:8]:
            print(line, flush=True)
    print("wrote", out_path, flush=True)


def main() -> None:
    mode = sys.argv[1]
    if mode == "honesty":
        run_honesty(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
        return
    if mode == "suite" or mode == "asan":
        # suite EXE FENS DEPTH OUT [Name Value ...]
        exe = Path(sys.argv[2])
        fens = Path(sys.argv[3])
        depth = int(sys.argv[4])
        out_path = Path(sys.argv[5])
        extra = []
        rest = sys.argv[6:]
        if len(rest) % 2 != 0:
            raise SystemExit("options must be name value pairs")
        for i in range(0, len(rest), 2):
            extra.append((rest[i], rest[i + 1]))
        run_suite(exe, fens, depth, out_path, extra, asan=(mode == "asan"))
        return
    raise SystemExit("usage: harness.py honesty|suite|asan ...")


if __name__ == "__main__":
    main()
