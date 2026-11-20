#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. Stops on a bad engine line."""
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

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def fen_of(line: str) -> str:
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    parts = line.split()
    if len(parts) < 4:
        raise SystemExit(f"bad position line: {line}")
    # EPD/FEN: six fields when a full FEN, four when a short EPD. Keep the
    # board fields only when the fifth token is not a halfmove clock.
    if len(parts) >= 6 and parts[4].isdigit():
        return " ".join(parts[:6])
    return " ".join(parts[:4]) if len(parts) > 4 else line


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: measure_depth.py EXE POSITIONS DEPTH OUT_PREFIX [LIMIT]")
    exe = str(Path(sys.argv[1]).resolve())
    positions = Path(sys.argv[2])
    depth = int(sys.argv[3])
    out_prefix = Path(sys.argv[4])
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    fens = []
    for raw in positions.read_text().splitlines():
        fen = fen_of(raw)
        if fen:
            fens.append(fen)
    if limit:
        fens = fens[:limit]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    raw_path = Path(str(out_prefix) + ".raw.txt")
    rows_path = Path(str(out_prefix) + ".rows.tsv")
    meta_path = Path(str(out_prefix) + ".raw.txt.meta")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin and proc.stdout
    log = raw_path.open("w")
    id_name = ""
    options_sent = []

    def fail(msg: str) -> None:
        log.write("HARNESS_STOP " + msg + "\n")
        log.flush()
        proc.kill()
        raise SystemExit(msg)

    def send(line: str) -> None:
        log.write(">> " + line + "\n")
        log.flush()
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(kind: str):
        lines = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail(f"engine closed during {kind}")
            line = line.rstrip("\n")
            log.write("<< " + line + "\n")
            log.flush()
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    fail(f"{bad}: {line}")
            lines.append(line)
            if kind == "ready" and line == "readyok":
                return lines
            if kind == "uci" and line == "uciok":
                return lines
            if kind == "best" and line.startswith("bestmove "):
                return lines

    send("uci")
    for line in read_until("uci"):
        if line.startswith("id name "):
            id_name = line
    for name, value in S14:
        sent = f"setoption name {name} value {value}"
        options_sent.append(sent)
        send(sent)
        send("isready")
        read_until("ready")
    rows = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("ready")
        send(f"position fen {fen}")
        send("isready")
        read_until("ready")
        send(f"go depth {depth}")
        answered = read_until("best")
        nodes = None
        for line in answered:
            parts = line.split()
            if "nodes" in parts:
                i = parts.index("nodes")
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    nodes = int(parts[i + 1])
        if nodes is None:
            fail(f"no nodes for position {index}")
        best = answered[-1].split()[1]
        rows.append((index, nodes, best, fen))
        if index % 25 == 0:
            print(f"{index} {nodes}", flush=True)
    send("quit")
    proc.wait(timeout=10)
    log.close()
    with rows_path.open("w") as handle:
        handle.write("index\tnodes\tbestmove\tfen\n")
        for index, nodes, best, fen in rows:
            handle.write(f"{index}\t{nodes}\t{best}\t{fen}\n")
    meta = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"positions={positions.resolve()}",
        f"depth={depth}",
        f"count={len(rows)}",
        "options_sent:",
        *options_sent,
    ]
    meta_path.write_text("\n".join(meta) + "\n")
    total = sum(nodes for _, nodes, _, _ in rows)
    print(f"positions {len(rows)} sum {total}")
    if len(rows) >= 3:
        print("first3 " + " / ".join(str(rows[i][1]) for i in range(3)))


if __name__ == "__main__":
    main()
