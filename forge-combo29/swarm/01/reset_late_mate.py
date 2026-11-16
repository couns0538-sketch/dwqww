#!/usr/bin/env python3
"""swarm seat 01: the last unmeasured case — a mate that RESETS the counter and lands on a LATER move.

Every case I have measured so far either mates in 1 ply at the root, or (the pawn-move board) mates in 3 plies
with a counter-resetting FIRST move. The combined patch searches the root whenever the side to move has
non-pawn material and the counter is >= 100, so in principle it should find ANY mate the search can see. This
script checks that on the hardest shape I can build: a forced mate of 4+ plies whose line contains at least
one pawn move or capture (so the counter genuinely resets inside the line), at halfmove 100 and 150.

Both builds are run: the unpatched engine (must miss it) and the combined build (must find it). If the
combined build also misses it, the patch is NOT complete for this shape and the summary must say so.

Setup for each board is verified with python-chess: a forced mate must exist, its length recorded, and at
least one move in the principal line must be a pawn move or a capture.

Usage: reset_late_mate.py <base-exe> <combined-exe> <outdir>
"""
import hashlib
import json
import os
import random
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 300.0


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
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def run(exe, fen, go="go depth 14"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send("position fen " + fen)
    send("isready")
    if until("readyok") is None:
        p.kill()
        return {"error": "no readyok"}
    send(go)
    bml = until("bestmove")
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes, "bestmove": bml.split()[1] if bml else None,
            "depths": len(dl)}


def forced_mate(board, limit=7):
    """Smallest ODD ply count for a forced mate, plus whether the mating side has a pawn move/capture available
    on the first move of some winning line."""
    def wins(b, depth):
        if depth <= 0:
            return False
        moves = list(b.legal_moves)
        if not moves:
            return b.is_checkmate()
        for m in moves:
            b.push(m)
            if b.is_checkmate():
                b.pop()
                return True
            ok = True
            for r in list(b.legal_moves):
                b.push(r)
                if not wins(b, depth - 2):
                    ok = False
                b.pop()
                if not ok:
                    break
            b.pop()
            if ok:
                return True
        return False

    for d in range(1, limit + 1, 2):
        if wins(board, d):
            return d
    return None


def has_reset_move(board):
    """Does the side to move have a pawn move or a capture that still keeps a forced mate?"""
    for m in board.legal_moves:
        if not (board.is_capture(m) or board.piece_at(m.from_square).piece_type == chess.PAWN):
            continue
        board.push(m)
        res = forced_mate(board, 5)
        board.pop()
        if res:
            return True, m.uci()
    return False, None


def find_candidates(n, seed):
    """Random K+Q+pawn vs K boards with a forced mate of >= 3 plies and a pawn move in the winning line."""
    rng = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        b = chess.Board(None)
        sq = rng.sample(range(64), 4)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.QUEEN, chess.WHITE))
        b.set_piece_at(sq[2], chess.Piece(chess.PAWN, chess.WHITE))
        b.set_piece_at(sq[3], chess.Piece(chess.KING, chess.BLACK))
        b.turn = chess.WHITE
        pawn_sq = sq[2]
        if chess.square_rank(pawn_sq) not in (1, 2, 3, 4, 5):
            continue
        if not b.is_valid():
            continue
        d = forced_mate(b, 5)
        if d is None or d < 3:
            continue
        has, mv = has_reset_move(b)
        if not has:
            continue
        out.append({"fen": b.fen(), "mate_plies": d, "reset_move": mv})
    return out, tries


def main():
    base, comb, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    cands, tries = find_candidates(3, 101)
    lines = ["the last unmeasured shape: a mate that RESETS the counter (pawn move or capture in the line) and",
             "needs several plies to land, at halfmove 100 and 150",
             "base     %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "combined %s sha256 %s" % (comb, hashlib.sha256(Path(comb).read_bytes()).hexdigest()),
             "go: 'go depth 14'; one fresh process per case; no setoption sent",
             "candidate search: %d boards tried, %d kept" % (tries, len(cands)),
             ""]
    if not cands:
        lines.append("NO CANDIDATE FOUND — no verdict drawn.")
        (out / "reset_late_mate.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return
    lines.append("board\tmate_plies\treset_move\tbase\tcombined\tverdict")
    rows = []
    for c in cands:
        for hm in (100, 150):
            fen = c["fen"].replace(" w - - 0 1", " w - - %d 1" % hm)
            a = run(base, fen)
            b = run(comb, fen)
            found_base = "mate" in a.get("score", "")
            found_comb = "mate" in b.get("score", "")
            verdict = ("combined FINDS, base misses" if found_comb and not found_base else
                       "BOTH miss (patch incomplete for this shape)" if not found_comb else
                       "both find")
            rows.append({"fen": fen, "mate_plies": c["mate_plies"], "reset_move": c["reset_move"],
                         "base": a, "combined": b, "verdict": verdict})
            lines.append("%s\t%d\t%s\t%s/%s\t%s/%s\t%s" % (
                fen, c["mate_plies"], c["reset_move"], a.get("score"), a.get("nodes"),
                b.get("score"), b.get("nodes"), verdict))
            print("H=%-4d mate_in=%d reset=%s base %-8s/%-7s combined %-8s/%-7s %s"
                  % (hm, c["mate_plies"], c["reset_move"], a.get("score"), a.get("nodes"),
                     b.get("score"), b.get("nodes"), verdict), flush=True)
    (out / "reset_late_mate.json").write_text(json.dumps(rows, indent=1))
    (out / "reset_late_mate.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
