#!/usr/bin/env python3
"""Search a FEN list at a fixed depth under S14.

One engine process. After every setoption and every position this sends
isready and reads every line up to readyok. It stops on unknown option,
invalid value, invalid FEN, or illegal move. ucinewgame and isready come
before every go.
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
]

STOP_BITS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    if len(sys.argv) < 5:
        die("usage: measure_set.py EXE POSITIONS OUT_PREFIX DEPTH [extra-options]")
    exe = Path(sys.argv[1]).resolve()
    positions = Path(sys.argv[2]).resolve()
    out_prefix = Path(sys.argv[3]).resolve()
    depth = int(sys.argv[4])
    extra = []
    if len(sys.argv) > 5:
        for line in Path(sys.argv[5]).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, value = line.split(None, 1)
            extra.append((name, value))
    fens = [line.strip() for line in positions.read_text().splitlines() if line.strip()]
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    sent: list[str] = []
    raw: list[str] = []

    def send(line: str) -> None:
        sent.append(line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done) -> None:
        while True:
            line = proc.stdout.readline()
            if line == "":
                err = proc.stderr.read() if proc.stderr is not None else ""
                die("engine closed stdout\n" + err)
            line = line.rstrip("\r\n")
            raw.append(line)
            low = line.lower()
            for bit in STOP_BITS:
                if bit in low:
                    proc.kill()
                    out_prefix.parent.mkdir(parents=True, exist_ok=True)
                    (out_prefix.parent / (out_prefix.name + ".txt")).write_text("\n".join(raw) + "\n")
                    die("STOP " + line)
            if done(line):
                return

    def ready() -> None:
        send("isready")
        read_until(lambda line: line == "readyok")

    send("uci")
    read_until(lambda line: line == "uciok")
    id_name = ""
    for line in raw:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    options = [("Threads", "1"), ("Hash", "16"), *S14, *extra]
    for name, value in options:
        send(f"setoption name {name} value {value}")
        ready()
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        ready()
        send(f"position fen {fen}")
        ready()
        send(f"go depth {depth}")
        read_until(lambda line: line.startswith("bestmove "))
        if index % 50 == 0:
            print(f"{out_prefix.name} {index}/{len(fens)}", flush=True)
    send("quit")
    proc.stdin.close()
    proc.wait(timeout=30)
    err = proc.stderr.read() if proc.stderr is not None else ""
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    (out_prefix.parent / (out_prefix.name + ".txt")).write_text("\n".join(raw) + "\n")
    (out_prefix.parent / (out_prefix.name + ".err")).write_text(err)
    (out_prefix.parent / (out_prefix.name + ".sent")).write_text("\n".join(sent) + "\n")
    meta = [f"exe {exe}", f"sha256 {sha}", f"id name {id_name}", "options"]
    meta.extend(f"setoption name {name} value {value}" for name, value in options)
    meta.append(f"positions {positions}")
    meta.append(f"count {len(fens)}")
    meta.append(f"depth {depth}")
    meta.append(f"exit {proc.returncode}")
    (out_prefix.parent / (out_prefix.name + ".meta")).write_text("\n".join(meta) + "\n")
    print(f"wrote {out_prefix.name} positions {len(fens)} exit {proc.returncode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
