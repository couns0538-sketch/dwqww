#!/usr/bin/env python3
"""S14 depth search. ucinewgame and isready before every go. One raw log."""
import sys
from pathlib import Path

from uci_session import Session, UciError

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


def load_fens(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6:
            rows.append(" ".join(parts[:6]))
        elif len(parts) >= 4:
            rows.append(" ".join(parts[:4]) + " 0 1")
        else:
            raise SystemExit(f"bad fen line: {line}")
    return rows


def nodes_of(lines):
    found = None
    for line in lines:
        if line.startswith("info ") and " nodes " in line and "string" not in line.split()[:3]:
            parts = line.split()
            found = parts[parts.index("nodes") + 1]
    if found is None:
        raise UciError("no nodes on info line")
    return found


def main():
    exe = sys.argv[1]
    fen_path = sys.argv[2]
    depth = int(sys.argv[3])
    out_dir = Path(sys.argv[4])
    stem = sys.argv[5]
    switch = sys.argv[6]  # omit, true, false
    start = int(sys.argv[7]) if len(sys.argv) > 7 else 0
    stop = int(sys.argv[8]) if len(sys.argv) > 8 else None
    fens = load_fens(fen_path)
    if stop is None:
        stop = len(fens)
    fens = fens[start:stop]
    out_dir.mkdir(parents=True, exist_ok=True)
    session = Session(exe)
    try:
        session.uci()
        for name, value in S14:
            session.setoption(name, value)
        session.setoption("Threads", "1")
        session.setoption("Hash", "16")
        if switch != "omit":
            session.setoption("IdeaS44", switch)
        node_rows = []
        for offset, fen in enumerate(fens):
            index = start + offset
            session.send("ucinewgame")
            session.ready()
            session.send(f"position fen {fen}")
            session.ready()
            session.send(f"go depth {depth}")
            block = session.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes = nodes_of(block)
            node_rows.append(f"{index} {nodes}")
            print(f"{index} {nodes}", flush=True)
    except UciError as err:
        (out_dir / f"{stem}.txt").write_text("".join(session.log))
        (out_dir / f"{stem}.txt.meta").write_text(session.meta(f"go depth {depth} switch {switch}"))
        print(f"STOP {err}", file=sys.stderr)
        session.close()
        return 1
    (out_dir / f"{stem}.txt").write_text("".join(session.log))
    (out_dir / f"{stem}.txt.meta").write_text(session.meta(f"go depth {depth} switch {switch}"))
    (out_dir / f"{stem}.nodes").write_text("\n".join(node_rows) + "\n")
    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
