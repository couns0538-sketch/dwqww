#!/usr/bin/env python3
"""Depth suite. S14, Threads 1, Hash 16, ucinewgame + isready before every go.
Usage: suite_depth.py <exe> <positions> <depth> <tag> [limit]
Writes <tag>.raw.txt, <tag>.rows.txt, <tag>.meta
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_run import Engine, id_name

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


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fen_of(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # epd may carry opcodes after the six FEN fields
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit("bad position line: " + line)
    return " ".join(parts[:6])


def last_info_nodes(lines, start):
    depth = None
    nodes = None
    score = None
    best = None
    for line in lines[start:]:
        if line.startswith("bestmove "):
            best = line.split()[1]
            break
        if not line.startswith("info ") or " nodes " not in line or " depth " not in line:
            continue
        tok = line.split()
        if "depth" in tok and "nodes" in tok:
            depth = int(tok[tok.index("depth") + 1])
            nodes = int(tok[tok.index("nodes") + 1])
        if "score" in tok:
            kind = tok[tok.index("score") + 1]
            val = tok[tok.index("score") + 2]
            score = kind + " " + val
    return depth, nodes, score, best


def main():
    exe = sys.argv[1]
    pos_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    tag = sys.argv[4]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    extra = sys.argv[6:]  # pairs already flattened? remaining are "name value" pairs
    if len(extra) % 2 != 0:
        raise SystemExit("extra options must be name value pairs")
    out = Path(__file__).resolve().parent
    fens = []
    for line in pos_path.read_text().splitlines():
        fen = fen_of(line)
        if fen:
            fens.append(fen)
    if limit:
        fens = fens[:limit]
    digest = sha256(exe)
    eng = Engine(exe)
    option_lines = []
    try:
        eng.send("uci", "uciok", 30)
        ident = id_name(eng.lines)
        setup = [("Threads", "1"), ("Hash", "16")] + S14
        for name, value in extra:
            setup.append((name, value))
        for name, value in setup:
            command = f"setoption name {name} value {value}"
            option_lines.append(command)
            eng.send(command, None, 30)
            eng.send("isready", "readyok", 30)
        rows = []
        raw_parts = []
        for index, fen in enumerate(fens):
            before = len(eng.lines)
            eng.send("ucinewgame", None, 30)
            eng.send("isready", "readyok", 60)
            eng.send("position fen " + fen, None, 30)
            eng.send("isready", "readyok", 60)
            eng.send(f"go depth {depth}", "bestmove ", 180)
            got_depth, nodes, score, best = last_info_nodes(eng.lines, before)
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append(f"{index} {nodes} {got_depth} {score} {best} {fen}")
            raw_parts.append("\n".join(eng.lines[before:]))
            if index % 25 == 0:
                print(f"{tag} {index} {nodes}", flush=True)
        text_rows = "\n".join(rows) + "\n"
        (out / f"{tag}.rows.txt").write_text(text_rows)
        (out / f"{tag}.raw.txt").write_text("\n".join(raw_parts) + "\n")
        total = sum(int(row.split()[1]) for row in rows)
        meta = (
            f"exe {exe}\nsha256 {digest}\n{ident}\n"
            + "\n".join(option_lines)
            + f"\ndepth {depth}\npositions {len(rows)}\nsum {total}\n"
        )
        (out / f"{tag}.meta").write_text(meta)
        print(f"{tag} SUM {total} n {len(rows)}", flush=True)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
