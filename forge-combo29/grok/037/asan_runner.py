#!/usr/bin/env python3
"""Same runner for the sanitizer build and the scratch build.

S14, then extra Name=value options. First N positions of a FEN file at a depth.
Transcript includes stdout and stderr. .meta holds nm -C | grep -c __asan_.
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


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def asan_count(exe: Path) -> int:
    proc = subprocess.run(["nm", "-C", str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    fens_path = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    limit = int(sys.argv[4])
    out_prefix = Path(sys.argv[5]).resolve()
    extra = []
    for item in sys.argv[6:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = []
    for line in fens_path.read_text().splitlines():
        fen = fen_of(line.strip())
        if fen:
            fens.append(fen)
        if len(fens) >= limit:
            break
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    transcript = []
    sent = []

    def send(cmd: str) -> None:
        sent.append(cmd)
        transcript.append(">> " + cmd + "\n")
        assert proc.stdin is not None
        try:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
        except BrokenPipeError:
            transcript.append(">> BROKEN PIPE\n")

    def read_until(pred, cap=200000):
        assert proc.stdout is not None
        got = []
        while len(got) < cap:
            line = proc.stdout.readline()
            if line == "":
                break
            transcript.append(line)
            got.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise SystemExit(f"STOP {bad}: {line.rstrip()}")
            if pred(line):
                return got
        return got

    send("uci")
    uci_lines = read_until(lambda s: s.startswith("uciok"))
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\n")
    send("isready")
    read_until(lambda s: s.startswith("readyok"))
    for name, value in S14 + extra:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until(lambda s: s.startswith("readyok"))
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s.startswith("readyok"))
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda s: s.startswith("readyok"))
        send(f"go depth {depth}")
        read_until(lambda s: s.startswith("bestmove ") or "ERROR: AddressSanitizer" in s or "runtime error:" in s)
    send("quit")
    try:
        rest = proc.communicate(timeout=20)[0]
    except subprocess.TimeoutExpired:
        proc.kill()
        rest = proc.communicate()[0]
    if rest:
        transcript.append(rest if rest.endswith("\n") else rest + "\n")
    text = "".join(transcript)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    out_prefix.with_suffix(".txt").write_text(text)
    count = asan_count(exe)
    san_lines = [line for line in text.splitlines() if "AddressSanitizer" in line or "runtime error:" in line]
    Path(str(out_prefix) + ".meta").write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha256(exe)}",
                f"id_name={id_name}",
                f"nm_asan_count={count}",
                "options_sent:",
                *[c for c in sent if c.startswith("setoption ")],
                f"depth={depth}",
                f"positions={len(fens)}",
                f"sanitizer_lines={len(san_lines)}",
                *san_lines,
                "",
            ]
        )
    )
    print(f"asan_symbols {count} sanitizer_lines {len(san_lines)} positions {len(fens)}")
    for line in san_lines[:8]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
