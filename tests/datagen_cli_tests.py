#!/usr/bin/env python3
"""S32 datagen v2 command line tests (standard library only, so CI can run them).

  python3 datagen_cli_tests.py <forge_datagen exe> <scratch dir>

Checks: same seed -> byte-identical files; another seed -> different data; a reused prefix is refused and
leaves the first run's files untouched; two concurrent processes (distinct prefixes) write exactly what
sequential runs write; every .pos/.hce record decodes and matches its text line (board nibbles, side to
move, score, White result); --convert of the text gives byte-identical .pos/.hce; the UCI path of the
datagen build is unchanged (bench 11 = 312866 nodes); bad command lines exit 2. Files are left in place.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

CODES = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}
FAILURES = 0


def check(ok: bool, message: str) -> None:
    global FAILURES
    print(("PASS " if ok else "FAIL ") + message, flush=True)
    if not ok:
        FAILURES += 1


def run(exe: str, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([exe, *args], input=stdin, capture_output=True, text=True, timeout=600)


def datagen(exe: str, out: Path, seed: int, games: int = 4) -> subprocess.CompletedProcess:
    return run(exe, "datagen", "--out", str(out), "--games", str(games), "--nodes", "600", "--seed", str(seed),
               "--max-ply", "120", "--positions-per-file", "150", "--text")


def files(prefix: Path) -> dict[str, bytes]:
    found = {p.name[len(prefix.name):]: p.read_bytes() for p in prefix.parent.iterdir()
             if p.name.startswith(prefix.name) and (p.name[len(prefix.name)] in "._")}
    return dict(sorted(found.items()))


def pack_fen(fen: str) -> tuple[bytes, int]:
    board = bytearray(32)
    rank, file = 7, 0
    placement, side = fen.split()[:2]
    for c in placement:
        if c == "/":
            rank, file = rank - 1, 0
        elif c.isdigit():
            file += int(c)
        else:
            s = rank * 8 + file
            board[s >> 1] |= CODES[c] << 4 if s & 1 else CODES[c]
            file += 1
    return bytes(board), 1 if side == "b" else 0


def decode(pos: bytes, hce: bytes) -> list[tuple[bytes, int, int, int]]:
    magic, version, n = struct.unpack_from("<4sIQ", pos, 0)
    hmagic, hversion, hn = struct.unpack_from("<4sIQ", hce, 0)
    assert magic == b"FPOS" and version == 1 and len(pos) == 16 + 35 * n, "bad .pos header/size"
    assert hmagic == b"FHCE" and hversion == 1 and hn == n and len(hce) == 16 + 2 * n, "bad .hce header/size"
    scores = struct.unpack_from(f"<{n}h", pos, 16 + 32 * n)
    hces = struct.unpack_from(f"<{n}h", hce, 16)
    return [(pos[16 + 32 * i:48 + 32 * i], scores[i], pos[16 + 34 * n + i], hces[i]) for i in range(n)]


def main() -> int:
    exe, base = sys.argv[1], Path(sys.argv[2])
    d = base / f"run_{time.time_ns()}_{os.getpid()}"
    d.mkdir(parents=True)

    a = datagen(exe, d / "a", 11)
    summary = json.loads(a.stdout.strip().splitlines()[-1]) if a.returncode == 0 else {}
    check(a.returncode == 0 and summary.get("games") == 4 and summary.get("positions", 0) > 0,
          f"4 games -> exit 0, summary {summary.get('games')} games / {summary.get('positions')} positions")
    fa = files(d / "a")
    check(all(k in fa for k in ("_000.pos", "_000.hce", "_000.txt", "_000.info", ".games")) and
          not any(k.endswith(".part") for k in fa), f"published shard files, no .part ({sorted(fa)})")
    b = datagen(exe, d / "b", 11)
    check(b.returncode == 0 and files(d / "b") == fa, "same seed -> byte-identical .pos/.hce/.txt/.info/.games")
    c = datagen(exe, d / "c", 12)
    fc = files(d / "c")
    check(c.returncode == 0 and fc.get("_000.pos") != fa["_000.pos"], "another seed -> different data")

    before = {k: hashlib.sha256(v).hexdigest() for k, v in fa.items()}
    again = datagen(exe, d / "a", 11)
    after = {k: hashlib.sha256(v).hexdigest() for k, v in files(d / "a").items()}
    check(again.returncode == 1 and "refusing" in again.stderr and after == before,
          "reused prefix -> exit 1, first run's files unchanged")

    p1 = subprocess.Popen([exe, "datagen", "--out", str(d / "p1"), "--games", "4", "--nodes", "600", "--seed", "11",
                           "--max-ply", "120", "--positions-per-file", "150", "--text"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen([exe, "datagen", "--out", str(d / "p2"), "--games", "4", "--nodes", "600", "--seed", "12",
                           "--max-ply", "120", "--positions-per-file", "150", "--text"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r1, r2 = p1.wait(timeout=600), p2.wait(timeout=600)
    p1.communicate()
    p2.communicate()
    check(r1 == 0 and r2 == 0 and files(d / "p1") == fa and files(d / "p2") == fc,
          "two concurrent processes in one directory == the sequential runs")

    records, text = [], []
    for shard in sorted(k for k in fa if k.endswith(".pos")):
        stem = shard[:-4]
        records += decode(fa[shard], fa[stem + ".hce"])
        text += fa[stem + ".txt"].decode("ascii").splitlines()
    ok = len(records) == len(text) == summary.get("positions")
    for (board, score, meta, hce), line in zip(records, text):
        fen, s, result = [x.strip() for x in line.split("|")]
        packed, black = pack_fen(fen)
        ok = ok and packed == board and (meta & 1) == black and int(s) == score and meta >> 1 == {"0.0": 0, "0.5": 1, "1.0": 2}[result]
        ok = ok and abs(score) <= 3000 and meta in range(6) and -32767 <= hce <= 32767
    check(ok, f"{len(records)} records decode and match their text lines (board, side to move, score, result)")
    games = [ln.split("\t") for ln in fa[".games"].decode("ascii").splitlines() if not ln.startswith("#")]
    check(len(games) == 4 and sum(int(g[5]) for g in games) == len(records) and
          all(g[3] in ("1-0", "0-1", "1/2-1/2") and len(g[6].split()) == 8 for g in games),
          "games log: 4 games, record counts add up, 8 random plies each")

    shards = sorted(k for k in fa if k.endswith(".txt"))
    conv_ok = True
    for i, shard in enumerate(shards):
        conv = run(exe, "datagen", "--out", str(d / f"conv{i}"), "--convert", str(d / ("a" + shard)))
        out = files(d / f"conv{i}")
        conv_ok = conv_ok and conv.returncode == 0 and out.get("_000.pos") == fa[shard[:-4] + ".pos"] and \
            out.get("_000.hce") == fa[shard[:-4] + ".hce"]
    check(conv_ok, f"--convert of {len(shards)} text shard(s) -> byte-identical .pos/.hce")

    uci = run(exe, stdin="uci\nisready\nbench 11\nquit\n")
    check(uci.returncode == 0 and "uciok" in uci.stdout and "bench depth 11 nodes 312866 " in uci.stdout,
          "UCI path of the datagen build unchanged: uciok, bench 11 = 312866 nodes")
    check(run(exe, "datagen").returncode == 2 and run(exe, "datagen", "--out", str(d / "x"), "--games", "1", "--nodes", "0").returncode == 2,
          "bad command lines -> exit 2")
    print("ALL PASS" if FAILURES == 0 else f"FAILURES: {FAILURES}", flush=True)
    return 0 if FAILURES == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
