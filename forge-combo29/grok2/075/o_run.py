#!/usr/bin/env python3
"""o_run.py: one depth-12 pass over a FEN file.

Usage:
  python3 o_run.py EXE SWITCH FENS RAW ROWS META

SWITCH is omit, false, or true.
omit does not send the switch option (exe B).
false and true send setoption name IdeaS10 value <word>.
S14, Threads 1 and Hash 16 are sent once, in that order, before the positions.
Each setoption and each position is followed by isready, and every line is
read up to readyok. The run stops on unknown option, invalid value,
invalid FEN, or illegal move.
"""
import hashlib
import subprocess
import sys

SWITCH_NAME = "IdeaS10"
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


def main() -> None:
    if len(sys.argv) != 7:
        sys.exit("usage: o_run.py EXE SWITCH FENS RAW ROWS META")
    exe, switch, fens_path, raw_path, rows_path, meta_path = sys.argv[1:]
    if switch not in ("omit", "false", "true"):
        sys.exit(f"STOP: switch must be omit, false, or true, got {switch}")
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    sent: list[str] = []
    raw_lines: list[str] = []
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def stop(why: str) -> None:
        proc.kill()
        open(raw_path, "w", encoding="utf-8").write("".join(raw_lines))
        sys.exit(why)

    def send(line: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker: str) -> str:
        assert proc.stdout is not None
        while True:
            line = proc.stdout.readline()
            if line == "":
                stop("STOP: engine closed stdout before " + marker)
            raw_lines.append(line)
            low = line.lower()
            if (
                "unknown option" in low
                or "invalid value" in low
                or "invalid fen" in low
                or "illegal move" in low
            ):
                stop("STOP: " + line.rstrip("\n"))
            if line.startswith(marker):
                return line

    send("uci")
    id_name = ""
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline()
        if line == "":
            stop("STOP: engine closed stdout before uciok")
        raw_lines.append(line)
        if line.startswith("id name ") and not id_name:
            id_name = line[len("id name ") :].rstrip("\n")
        low = line.lower()
        if (
            "unknown option" in low
            or "invalid value" in low
            or "invalid fen" in low
            or "illegal move" in low
        ):
            stop("STOP: " + line.rstrip("\n"))
        if line.startswith("uciok"):
            break

    def setoption(name: str, value: str) -> None:
        line = f"setoption name {name} value {value}"
        sent.append(line)
        send(line)
        send("isready")
        read_until("readyok")

    setoption("Threads", "1")
    setoption("Hash", "16")
    for name, value in S14:
        setoption(name, value)
    if switch != "omit":
        setoption(SWITCH_NAME, switch)

    rows: list[str] = []
    for number, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send("go depth 12")
        last_nodes = None
        while True:
            assert proc.stdout is not None
            line = proc.stdout.readline()
            if line == "":
                stop(f"STOP: engine closed stdout during position {number}")
            raw_lines.append(line)
            low = line.lower()
            if (
                "unknown option" in low
                or "invalid value" in low
                or "invalid fen" in low
                or "illegal move" in low
            ):
                stop("STOP: " + line.rstrip("\n"))
            if " nodes " in line and line.startswith("info "):
                parts = line.split()
                try:
                    last_nodes = int(parts[parts.index("nodes") + 1])
                except (ValueError, IndexError):
                    stop("STOP: unreadable nodes on position " + str(number) + ": " + line.rstrip("\n"))
            if line.startswith("bestmove"):
                break
        if last_nodes is None:
            stop(f"STOP: no info nodes line before bestmove on position {number}")
        rows.append(f"{number}\t{last_nodes}\n")
        if number % 50 == 0:
            print(f"{number}/{len(fens)}", file=sys.stderr, flush=True)

    send("quit")
    proc.wait(timeout=10)
    open(raw_path, "w", encoding="utf-8").write("".join(raw_lines))
    open(rows_path, "w", encoding="utf-8").write("".join(rows))
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    meta = [
        f"exe: {exe}",
        f"sha256: {sha}",
        f"id_name: {id_name}",
        "options:",
        *sent,
        "",
    ]
    open(meta_path, "w", encoding="utf-8").write("\n".join(meta))
    print(f"positions {len(rows)} -> {rows_path}")


if __name__ == "__main__":
    main()
