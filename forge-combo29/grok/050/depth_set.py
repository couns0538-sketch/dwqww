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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def load_fens(path):
    fens = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            die(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]) if len(parts) >= 6 else line)
    return fens


def main():
    if len(sys.argv) < 5:
        die("usage: depth_set.py EXE FENS DEPTH OUT_PREFIX [extra setoption lines...]")
    exe = str(Path(sys.argv[1]).resolve())
    fen_path = str(Path(sys.argv[2]).resolve())
    depth = int(sys.argv[3])
    out_prefix = Path(sys.argv[4])
    extras = sys.argv[5:]
    fens = load_fens(fen_path)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw_lines = []

    def send(line):
        raw_lines.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred, limit=200000):
        got = []
        for _ in range(limit):
            line = proc.stdout.readline()
            if line == "":
                die("engine closed early, last lines:\n" + "\n".join(raw_lines[-20:]))
            line = line.rstrip("\n")
            raw_lines.append(line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    die(f"STOP {bad}: {line}")
            if pred(line):
                return got
        die("read limit")

    send("uci")
    id_lines = read_until(lambda s: s == "uciok")
    id_name = ""
    for line in id_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]

    options = [("Threads", "1"), ("Hash", "16")] + S14
    for extra in extras:
        # "Name value" with the value as the last token. Names have no digits-only tail.
        bits = extra.split()
        if len(bits) < 2:
            die(f"bad extra option: {extra}")
        options.append((" ".join(bits[:-1]), bits[-1]))

    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until(lambda s: s == "readyok")

    rows = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda s: s == "readyok")
        send(f"go depth {depth}")
        info = read_until(lambda s: s.startswith("bestmove "))
        nodes = None
        shown_depth = None
        for line in info:
            if " nodes " in line and line.startswith("info "):
                parts = line.split()
                if "nodes" in parts:
                    i = parts.index("nodes")
                    nodes = int(parts[i + 1])
                if "depth" in parts:
                    i = parts.index("depth")
                    shown_depth = int(parts[i + 1])
        if nodes is None:
            die(f"no nodes for position {index}")
        rows.append((index, nodes, shown_depth, fen))
        if index % 50 == 0:
            print(f"progress {index}/{len(fens)}", file=sys.stderr, flush=True)

    send("quit")
    proc.wait(timeout=30)

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(out_prefix) + ".txt")
    rows_path = Path(str(out_prefix) + ".rows")
    meta_path = Path(str(out_prefix) + ".meta")
    raw_path.write_text("\n".join(raw_lines) + "\n")
    with rows_path.open("w") as handle:
        total = 0
        for index, nodes, shown_depth, fen in rows:
            total += nodes
            handle.write(f"{index} {nodes} {shown_depth}\n")
        handle.write(f"sum {total}\n")
        if rows:
            handle.write(
                "first3 "
                + " ".join(str(rows[i][1]) for i in range(min(3, len(rows))))
                + "\n"
            )
    option_text = "\n".join(f"option {name} {value}" for name, value in options)
    meta_path.write_text(
        f"exe {exe}\nsha256 {sha}\nid name {id_name}\n"
        f"fens {fen_path}\ndepth {depth}\ncount {len(fens)}\n"
        f"{option_text}\n"
    )
    print(raw_path)
    print(f"sum {sum(r[1] for r in rows)} n {len(rows)}")


if __name__ == "__main__":
    main()
