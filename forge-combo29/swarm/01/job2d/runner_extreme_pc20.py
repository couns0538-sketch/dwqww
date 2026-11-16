#!/usr/bin/env python3
"""swarm seat 01, job 2: extreme numbers in the FEN fields, ASan + UBSan.

Cases are written to cases.tsv by this script (so the list is in the repo, not in my head), then each case
runs in its own fresh engine process:
    position fen <FEN>
    isready            (read to readyok; every line kept)
    go depth 4         (read to bestmove; every line kept)
    position fen <FEN again>
    isready
    go perft 2         (read to nodes N)
python-chess perft 2 is computed for every FEN python-chess accepts, and both are compared.

Usage: runner_extreme.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 60.0


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            chunk = os.read(self.fd, 65536)
            if not chunk:
                self.eof = True
                return None
            self.buf += chunk
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
        ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
OPTIONS = []


def apply_options(proc, rd):
    """Send every option, each followed by isready read to readyok."""
    for name, value in OPTIONS:
        proc.stdin.write(("setoption name %s value %s\n" % (name, value)).encode())
        proc.stdin.write(b"isready\n")
        proc.stdin.flush()
        deadline = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(deadline)
            if l is None or l.startswith("readyok"):
                break


def run_case(exe, fen):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(proc.stdout.fileno())
    buf = []

    def until(prefixes):
        deadline = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            for p in prefixes:
                if l.startswith(p):
                    return l

    def send(s):
        proc.stdin.write((s + "\n").encode())
        proc.stdin.flush()

    apply_options(proc, rd)
    send("position fen " + fen)
    send("isready")
    ready = until(("readyok",))
    refused = any(l.startswith("info string invalid FEN") for l in buf)
    refusal = [l for l in buf if l.startswith("info string invalid FEN")]
    depth4_lines = []
    bestmove = None
    if ready is not None:
        send("go depth 4")
        bm = until(("bestmove",))
        if bm is not None:
            bestmove = bm.split()[1] if len(bm.split()) > 1 else ""
        depth4_lines = buf[:]

    # perft 2 in a FRESH process so the depth-4 search cannot affect it
    proc2 = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd2 = R(proc2.stdout.fileno())
    buf2 = []

    def until2(prefixes):
        deadline = time.monotonic() + TIMEOUT
        while True:
            l = rd2.line(deadline)
            if l is None:
                return None
            buf2.append(l)
            for p in prefixes:
                if l.startswith(p):
                    return l

    apply_options(proc2, rd2)
    proc2.stdin.write(("position fen " + fen + "\n").encode())
    proc2.stdin.write(b"isready\n")
    proc2.stdin.flush()
    ready2 = until2(("readyok",))
    perft2 = None
    if ready2 is not None and not any(l.startswith("info string invalid FEN") for l in buf2):
        proc2.stdin.write(b"go perft 2\n")
        proc2.stdin.flush()
        if until2(("nodes ",)) is not None:
            for l in buf2:
                if l.startswith("nodes "):
                    perft2 = int(l.split()[1])
    for p in (proc, proc2):
        try:
            p.stdin.write(b"quit\n")
            p.stdin.flush()
            p.wait(timeout=20)
        except Exception:
            p.kill()

    san = [l for l in buf + buf2 if ("AddressSanitizer" in l or "runtime error" in l
                                     or "SUMMARY:" in l or "UndefinedBehaviorSanitizer" in l)]
    return {
        "fen": fen,
        "refused": refused,
        "refusal": refusal,
        "bestmove": bestmove,
        "perft2_engine": perft2,
        "depth4_lines": depth4_lines[-14:],
        "perft_lines": buf2[-8:],
        "sanitizer": san,
        "crashed": (ready is None),
    }


def py_perft2(fen):
    try:
        b = chess.Board(fen)
    except Exception:  # noqa: BLE001
        return None
    if not b.is_valid():
        return None

    def perft(board, d):
        if d == 0:
            return 1
        n = 0
        for m in board.legal_moves:
            board.push(m)
            n += perft(board, d - 1)
            board.pop()
        return n

    return perft(b, 2)


def build_cases():
    start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    mid = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R"
    cases = []

    def add(name, group, fen):
        cases.append((name, group, fen))

    for hm in ("0", "99", "100", "150", "9999", "-1", "65535", "65536", "100000"):
        add("halfmove_%s" % hm, "halfmove", start + " w KQkq - %s 1" % hm)
    for fm in ("0", "1", "1000000000", "-1", "65536"):
        add("fullmove_%s" % fm, "fullmove", start + " w KQkq - 0 %s" % fm)
    # ep square on a rank the side to move cannot have just created
    add("ep_wrong_rank_w", "ep_rank", mid + " w KQkq e3 0 1")
    add("ep_wrong_rank_b", "ep_rank", mid + " b KQkq e6 0 1")
    # ep square with no pawn that could have double-pushed behind it
    add("ep_no_pawn_w", "ep_nopawn", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1")
    add("ep_no_pawn_b", "ep_nopawn", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq e3 0 1")
    # two kings of one colour, and none of a colour
    add("two_white_kings", "kings", "4k3/8/8/8/8/8/8/K3K3 w - - 0 1")
    add("two_black_kings", "kings", "k3k3/8/8/8/8/8/8/K7 w - - 0 1")
    add("no_white_king", "kings", "4k3/8/8/8/8/8/8/8 w - - 0 1")
    add("no_black_king", "kings", "8/8/8/8/8/8/8/K7 w - - 0 1")
    # pawns on the promotion ranks
    add("white_pawn_rank8", "pawn_rank", "4k3/4P3/8/8/8/8/8/4K3 w - - 0 1")
    add("black_pawn_rank1", "pawn_rank", "4k3/8/8/8/8/8/8/4p1K1 b - - 0 1")
    add("white_pawn_rank1", "pawn_rank", "4k3/8/8/8/8/8/8/4P1K1 w - - 0 1")
    # a legal mid-game board for reference (so a refusal can never be blamed on the board)
    add("reference_midgame", "reference", mid + " w KQkq - 0 1")
    add("reference_start", "reference", start + " w KQkq - 0 1")
    # halfmove + big fullmove together
    add("halfmove_100_fullmove_1e9", "combined", start + " w KQkq - 100 1000000000")
    add("halfmove_65536_fullmove_65536", "combined", start + " w KQkq - 65536 65536")
    return cases


def main():
    global OPTIONS
    exe = sys.argv[1]
    outdir = Path(sys.argv[2])
    if "--pc20" in sys.argv:
        OPTIONS = PC20
    outdir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    with open(outdir / "cases.tsv", "w") as fh:
        fh.write("case\tgroup\tfen\n")
        for name, group, fen in cases:
            fh.write("%s\t%s\t%s\n" % (name, group, fen))

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    meta = [
        "exe_started: %s" % exe,
        "sha256: %s" % sha,
        "nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l),
        "nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l),
        "option lines sent: %s" % ("; ".join("%s=%s" % kv for kv in OPTIONS) if OPTIONS else "NONE"),
        "each case is a fresh engine process twice: once for position+isready+go depth 4,",
        "and once more for position+isready+go perft 2, so the search cannot affect the perft.",
        "after every position and every setoption an isready is sent and read to readyok",
        "timeout per answer: %g s" % TIMEOUT,
    ]
    (outdir / "meta.txt").write_text("\n".join(meta) + "\n")

    results = []
    for name, group, fen in cases:
        rec = run_case(exe, fen)
        rec["case"] = name
        rec["group"] = group
        rec["py_perft2"] = py_perft2(fen)
        rec["perft_match"] = (rec["perft2_engine"] is not None and rec["py_perft2"] is not None
                              and rec["perft2_engine"] == rec["py_perft2"])
        results.append(rec)
        print("%-28s refused=%-5s bestmove=%s perft2=%s py=%s"
              % (name, rec["refused"], rec["bestmove"], rec["perft2_engine"], rec["py_perft2"]),
              flush=True)
    with open(outdir / "results.json", "w") as fh:
        json.dump(results, fh, indent=1)
    print("cases %d" % len(results))


if __name__ == "__main__":
    main()
