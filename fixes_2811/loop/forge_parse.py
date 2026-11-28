"""Reading of .plain training data for the Forge trainer, in parallel slices.

A .plain file is a list of records (fen / move / score / ply / result / "e"). Parsing one with Python and
checking every position for check is the slow part of a Forge training stage (131 s for 5.0 million
records in one process). This module cuts a file into byte ranges that end on a record boundary and parses
each range in its own process, each with its own run of hce_dump. The ranges are joined in file order,
so the result is the same as from one pass over the file.

Imported by forge_train.py; also run by it as a script, once per slice:
    python forge_parse.py <plain file> <start> <end> <hce_dump.exe> <skip_noisy 0|1> <skip_check 0|1> <out.npz>
It imports only numpy and python-chess, so a slice process starts fast and stays small.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np

VALUE_NONE = 32002
PIECES = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}  # 1..6 white PNBRQK, 7..12 black
END = b"\ne\n"


def fen_codes(board_field: str) -> bytes:
    """64 piece codes, square 0 = a1 ... 63 = h8 (the engine's numbering)."""
    out = bytearray(64)
    rank = 7
    file = 0
    for ch in board_field:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            out[rank * 8 + file] = PIECES[ch]
            file += 1
    return bytes(out)


def is_noisy(codes: bytes, move: str) -> bool:
    """Best move is a capture, en passant or promotion."""
    if len(move) > 4:
        return True
    to = (ord(move[2]) - 97) + (ord(move[3]) - 49) * 8
    if codes[to] != 0:
        return True
    frm = (ord(move[0]) - 97) + (ord(move[1]) - 49) * 8
    return codes[frm] in (1, 7) and move[0] != move[2]  # pawn moving diagonally to an empty square


def slices(path: str, parts: int) -> list[tuple[int, int]]:
    """Byte ranges [start, end) covering the file, each ending right after a record's "e" line."""
    size = os.path.getsize(path)
    if parts <= 1 or size < (1 << 20):
        return [(0, size)]
    cuts = [0]
    with open(path, "rb") as fh:
        for i in range(1, parts):
            pos = size * i // parts
            if pos <= cuts[-1]:
                continue
            fh.seek(pos)
            k = fh.read(1 << 16).find(END)
            if k < 0:
                continue
            cut = pos + k + len(END)
            if cuts[-1] < cut < size:
                cuts.append(cut)
    cuts.append(size)
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]


def parse_slice(path: str, start: int, end: int, hce_exe: str, skip_noisy: bool, skip_check: bool) -> dict:
    """Parse the records in bytes [start, end): drop marked/noisy/in-check positions, add the hand-written eval."""
    import chess

    with open(path, "rb") as fh:
        fh.seek(start)
        text = fh.read(end - start).decode("ascii", errors="replace")
    boards, stm, score, res, fens = [], [], [], [], []
    n_all = n_marked = n_noisy = n_check = 0
    fen = move = ""
    sc = rs = 0
    for line in text.split("\n"):
        c = line[:1]
        if c == "f":
            fen = line[4:].rstrip("\r\n")
        elif c == "m":
            move = line[5:].rstrip("\r\n")
        elif c == "s":
            sc = int(float(line[6:]))
        elif c == "r":
            rs = int(line[7:])
        elif c == "e":
            n_all += 1
            if sc == VALUE_NONE:
                n_marked += 1
                continue
            parts = fen.split(" ")
            codes = fen_codes(parts[0])
            if skip_noisy and is_noisy(codes, move):
                n_noisy += 1
                continue
            if skip_check and chess.Board(fen).is_check():
                n_check += 1
                continue
            boards.append(codes)
            stm.append(0 if parts[1] == "w" else 1)
            score.append(max(-32000, min(32000, sc)))
            res.append(rs)
            fens.append(fen)
    n = len(boards)
    hce = np.zeros(0, np.float32)
    if n:
        p = subprocess.run([hce_exe], input="\n".join(fens) + "\n", capture_output=True, text=True)
        vals = p.stdout.split()
        if p.returncode != 0 or len(vals) != n or "bad" in vals:
            raise SystemExit(f"hce_dump failed on {path} [{start}:{end}]: exit {p.returncode}, "
                             f"{len(vals)} values for {n} positions, {vals.count('bad')} bad")
        hce = np.array([int(v) for v in vals], dtype=np.float32)
    return {
        "codes": np.frombuffer(b"".join(boards), np.uint8).reshape(n, 64).copy(),
        "stm": np.array(stm, dtype=np.uint8),
        "score": np.array(score, dtype=np.float32),
        "res": np.array(res, dtype=np.float32),   # side to move: -1, 0, 1
        "hce": hce,
        "counts": np.array([n_all, n_marked, n_noisy, n_check], dtype=np.int64),
    }


def parse_file(path: str, hce_exe: str, skip_noisy: bool, skip_check: bool, procs: int) -> dict:
    """Whole file, in up to `procs` slice processes. Same arrays, same order, as one pass."""
    parts = slices(path, procs)
    if len(parts) == 1:
        return parse_slice(path, parts[0][0], parts[0][1], hce_exe, skip_noisy, skip_check)
    tmp_dir = Path(path).parent
    outs = [tmp_dir / f".parse_{os.getpid()}_{i:02d}.npz" for i in range(len(parts))]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    running = []
    try:
        for (s, e), out in zip(parts, outs):
            cmd = [sys.executable, str(Path(__file__).resolve()), str(path), str(s), str(e), str(hce_exe),
                   str(int(skip_noisy)), str(int(skip_check)), str(out)]
            running.append(subprocess.Popen(cmd, creationflags=flags))
        codes = [p.wait() for p in running]
        if any(codes):
            raise SystemExit(f"slice parser failed for {path}: exit codes {codes}")
        loaded = [np.load(o, allow_pickle=False) for o in outs]
        d = {k: np.concatenate([z[k] for z in loaded]) for k in ("codes", "stm", "score", "res", "hce")}
        d["counts"] = sum(z["counts"] for z in loaded)
        for z in loaded:
            z.close()
        return d
    finally:
        for p in running:
            if p.poll() is None:
                p.kill()
        for o in outs:
            try:
                o.unlink()
            except OSError:
                pass


def main() -> int:
    path, start, end, hce_exe, noisy, check, out = sys.argv[1:8]
    d = parse_slice(path, int(start), int(end), hce_exe, noisy == "1", check == "1")
    tmp = out + ".tmp.npz"
    np.savez(tmp, **d)
    os.replace(tmp, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
