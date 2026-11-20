#!/usr/bin/env python3
"""Depth-12 node run over first200.fens.

Usage: orun.py <exe> <fens> <out_prefix> <switch>
  switch is "-" (do not send), "false", or "true" (IdeaB1).

Sends Threads 1, Hash 16, then S14 in the brief's order, then the switch.
ucinewgame + isready, position + isready, go depth 12, for every FEN.
Raw engine stdout goes to <out_prefix>.txt and the option record to .meta.
"""
import hashlib
import pathlib
import sys

from engine_io import Session

S14 = (
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
)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def setoption(session: Session, name: str, value: str) -> str:
    line = f"setoption name {name} value {value}"
    session.send(line)
    session.send("isready")
    session.read_until(lambda got: got.strip() == "readyok", 30)
    return line


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit("usage: orun.py <exe> <fens> <out_prefix> <switch>")
    exe = str(pathlib.Path(sys.argv[1]).resolve())
    fens = [line.strip() for line in open(sys.argv[2], encoding="utf-8") if line.strip()]
    prefix = pathlib.Path(sys.argv[3])
    switch = sys.argv[4]
    if switch not in ("-", "false", "true"):
        sys.exit("switch must be -, false, or true")
    if len(fens) != 200:
        sys.exit(f"expected 200 fens, got {len(fens)}")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    sent: list[str] = []
    session = Session(exe)
    bestmoves = 0
    try:
        session.send("uci")
        session.read_until(lambda line: line.strip() == "uciok", 30)
        sent.append(setoption(session, "Threads", "1"))
        sent.append(setoption(session, "Hash", "16"))
        for name, value in S14:
            sent.append(setoption(session, name, value))
        if switch != "-":
            sent.append(setoption(session, "IdeaB1", switch))
        for index, fen in enumerate(fens, start=1):
            session.send("ucinewgame")
            session.send("isready")
            session.read_until(lambda line: line.strip() == "readyok", 30)
            session.send(f"position fen {fen}")
            session.send("isready")
            session.read_until(lambda line: line.strip() == "readyok", 30)
            session.send("go depth 12")
            session.read_until(lambda line: line.startswith("bestmove "), 180)
            bestmoves += 1
            if index % 25 == 0:
                print(f"{prefix.name} {index}/200", flush=True)
    finally:
        session.close()
        prefix.with_suffix(".txt").write_text("".join(session.lines), encoding="utf-8")
        ident = ""
        for line in session.lines:
            if line.startswith("id name "):
                ident = line[len("id name "):].rstrip("\n")
                break
        meta = [
            f"exe={exe}",
            f"sha256={sha256_file(exe)}",
            f"id_name={ident}",
            f"fens={pathlib.Path(sys.argv[2]).resolve()}",
            f"switch={switch}",
            f"bestmoves={bestmoves}",
            "options:",
            *sent,
            "",
        ]
        prefix.with_suffix(".meta").write_text("\n".join(meta), encoding="utf-8")
    if bestmoves != 200:
        sys.exit(f"STOP: bestmoves {bestmoves}")
    print(f"{prefix.name} done bestmoves {bestmoves}")


if __name__ == "__main__":
    main()
