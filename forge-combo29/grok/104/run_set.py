#!/usr/bin/env python3
"""Measured fixed-depth set. S14, Threads 1, Hash 16.

switch: omit | false | true
omit does not send IdeaS35 (exe B). false and true send it.
Stops on unknown option, invalid value, invalid FEN, illegal move.
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

def die(msg):
    print(msg, file=sys.stderr, flush=True)
    sys.exit(2)

def load_fens(path):
    fens = []
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6 and "/" in parts[0]:
            fens.append(" ".join(parts[:6]))
        else:
            fens.append(line)
    return fens

def main():
    if len(sys.argv) != 7:
        die("usage: run_set.py EXE FENS DEPTH SWITCH OUT_PREFIX LIMIT")
    exe = str(Path(sys.argv[1]).resolve())
    fens = load_fens(sys.argv[2])
    depth = int(sys.argv[3])
    switch = sys.argv[4]
    prefix = Path(sys.argv[5])
    limit = int(sys.argv[6])
    if switch not in ("omit", "false", "true"):
        die("switch must be omit, false, or true")
    if limit > 0:
        fens = fens[:limit]
    prefix.parent.mkdir(parents=True, exist_ok=True)
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch != "omit":
        options.append(("IdeaS35", switch))
    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw_parts = []
    option_lines = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(predicate, timeout_lines=100000):
        got = []
        for _ in range(timeout_lines):
            line = proc.stdout.readline()
            if line == "":
                die("engine closed stdout early")
            raw_parts.append(line)
            got.append(line)
            low = line.lower()
            if "unknown option" in low or "invalid value" in low or "invalid fen" in low or "illegal move" in low:
                prefix.with_suffix(".raw.txt").write_text("".join(raw_parts))
                die("STOP " + line.strip())
            if predicate(line):
                return got
        die("too many lines without the expected reply")

    send("uci")
    uci = read_until(lambda line: line.strip() == "uciok")
    id_name = ""
    for line in uci:
        if line.startswith("id name "):
            id_name = line[len("id name "):].strip()
    send("isready")
    read_until(lambda line: line.strip() == "readyok")
    for name, value in options:
        sent = f"setoption name {name} value {value}"
        option_lines.append(sent)
        send(sent)
        send("isready")
        read_until(lambda line: line.strip() == "readyok")

    rows = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line.strip() == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line.strip() == "readyok")
        send(f"go depth {depth}")
        info = read_until(lambda line: line.startswith("bestmove "))
        nodes = None
        score = ""
        for line in info:
            if " nodes " in line and line.startswith("info "):
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
                if "score" in parts:
                    si = parts.index("score")
                    score = " ".join(parts[si:si + 3]) if si + 2 < len(parts) and parts[si + 1] == "cp" else " ".join(parts[si:si + 2])
        best = info[-1].strip()
        if nodes is None:
            prefix.with_suffix(".raw.txt").write_text("".join(raw_parts))
            die(f"no nodes for position {index}")
        rows.append((index, nodes, best, score, fen))
        if index % 25 == 0:
            print(f"progress {index}/{len(fens)} last_nodes={nodes}", flush=True)

    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    text = "".join(raw_parts)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(prefix) + ".raw.txt")
    tsv_path = Path(str(prefix) + ".tsv")
    meta_path = Path(str(prefix) + ".meta")
    raw_path.write_text(text)
    tsv = ["index\tnodes\tbest\tscore\tfen"]
    total = 0
    for index, nodes, best, score, fen in rows:
        total += nodes
        tsv.append(f"{index}\t{nodes}\t{best}\t{score}\t{fen}")
    tsv.append(f"SUM\t{total}\t\t\t")
    tsv_path.write_text("\n".join(tsv) + "\n")
    meta = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={id_name}",
        f"depth={depth}",
        f"switch={switch}",
        f"positions={len(rows)}",
        f"sum={total}",
        "options:",
        *option_lines,
        "",
    ]
    meta_path.write_text("\n".join(meta))
    print(f"SUM {total} positions {len(rows)}", flush=True)
    if rows:
        head = " ".join(str(rows[i][1]) for i in range(min(3, len(rows))))
        print(f"FIRST3 {head}", flush=True)

if __name__ == "__main__":
    main()
