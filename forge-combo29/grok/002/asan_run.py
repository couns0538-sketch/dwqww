#!/usr/bin/env python3
"""Run depth searches under a sanitizer build. Same runner for the real build and the scratch build.

Usage:
  asan_run.py <exe> <fenfile> <depth> <outbase> <maxpositions> [extra setoption ...]

S14, Threads 1 and Hash 16 are sent. Extra options follow, in the order given.
The process output is kept if the engine dies. Lines that look like a sanitizer
report are copied to <outbase>.sanitizer.txt.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

from uci_io import Engine

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
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    return text.split(";")[0].strip()


def sanitizer_lines(lines: list[str]) -> list[str]:
    hits = []
    for line in lines:
        if (
            "AddressSanitizer" in line
            or "UndefinedBehaviorSanitizer" in line
            or "runtime error:" in line
            or line.startswith("SUMMARY:")
        ):
            hits.append(line)
    return hits


def main() -> int:
    if len(sys.argv) < 6:
        print(
            "usage: asan_run.py <exe> <fenfile> <depth> <outbase> <maxpositions> [extra setoption ...]",
            file=sys.stderr,
        )
        return 2
    exe = Path(sys.argv[1]).resolve()
    fenfile = Path(sys.argv[2])
    depth = int(sys.argv[3])
    outbase = Path(sys.argv[4])
    limit = int(sys.argv[5])
    extras = sys.argv[6:]
    fens = [fen for fen in (fen_of(line) for line in fenfile.read_text(encoding="utf-8").splitlines()) if fen]
    fens = fens[:limit]
    nm = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    engine = Engine(exe)
    id_name = ""
    error = ""
    done = 0
    try:
        engine.send("uci")
        ident = engine.read_until(lambda line: line == "uciok", 60)
        for line in ident:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        setup = ["setoption name Threads value 1", "setoption name Hash value 16", *S14, *extras]
        for option in setup:
            engine.send(option)
            engine.ready()
        for fen in fens:
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
            done += 1
    except (RuntimeError, TimeoutError, EOFError) as exc:
        error = str(exc)
    finally:
        engine.close()
    hits = sanitizer_lines(engine.lines)
    Path(str(outbase) + ".raw.txt").write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
    Path(str(outbase) + ".sanitizer.txt").write_text("\n".join(hits) + ("\n" if hits else ""), encoding="utf-8")
    Path(str(outbase) + ".meta").write_text(
        f"exe {exe}\n"
        f"sha256 {sha256(exe)}\n"
        f"id name {id_name}\n"
        f"fenfile {fenfile.resolve()}\n"
        f"depth {depth}\n"
        f"maxpositions {limit}\n"
        f"started {done}\n"
        f"nm -C {exe} | grep -c __asan_\n"
        f"asan_symbol_count {asan_count}\n"
        f"sanitizer_lines {len(hits)}\n"
        f"error {error}\n"
        "setoption lines:\n"
        + "\n".join(["setoption name Threads value 1", "setoption name Hash value 16", *S14, *extras])
        + "\n",
        encoding="utf-8",
    )
    print(f"asan_symbol_count {asan_count}")
    print(f"positions_finished {done}")
    print(f"sanitizer_lines {len(hits)}")
    if error:
        print(f"error {error}")
    for line in hits[:8]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
