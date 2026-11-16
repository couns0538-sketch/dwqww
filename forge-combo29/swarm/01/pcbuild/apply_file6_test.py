#!/usr/bin/env python3
"""swarm seat 01: apply FABLE_TO_swarm_6's PRESCRIBED TEST to my own fifty-move findings.

File 6 says: "a draw by repetition or by the fifty-move rule scored 0 is NOT a defect ... A cp 0 at a high
counter is a defect ONLY when a forced mate exists that ends no later than the 100th half-move. Test for
it: the same board with counter 0, `go depth 20` or more, read `mate N`; it is a defect only if
2N - 1 <= 100 - counter and the board with the real counter still scores cp 0 at that depth."

That test can VINDICATE the base tree on boards where I claimed a fault. I must apply it to my own claims
rather than defend them:

  A  mate-in-1 at halfmove 100  (my S-F5, S-F17)   "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"
     mate N = 1 at counter 0, so 2N-1 = 1 and 100 - 100 = 0.  1 <= 0 is FALSE -> by file 6 this is
     NOT a defect: the mate would land on the 101st half-move, past the point where the match program
     ends the game. The counter must therefore still be reported, and my claim withdrawn if the engine
     answers cp 0 at depth 20+.

  B  counter-RESETTING mate-in-3 at halfmove 100 (my S-F22)  "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"
     Here the first mating move is a PAWN move (h6h7), which resets the counter to 0 -- the fifty-move
     clock does not advance, so the 100th-half-move cut-off is never reached by the mating line. This is
     the case where cp 0 WOULD be a defect even under file 6.

  C  mate-in-3, all quiet, at halfmove 99 (my S-F23)  "8/8/8/8/2K4Q/8/8/1k6 w - - 99 1"
     2N-1 = 5 > 100-99 = 1, so NOT a defect under file 6 (the mate is too far away).

For each board: measure `mate N` at counter 0 with `go depth 20`+, compute the inequality, then measure the
real-counter board at the same depth. The verdict is the inequality AND the observed score, both printed.

Also measures whether the mating line's first move is a capture or pawn move, because that is what decides
whether the counter advances at all.

Usage: apply_file6_test.py <pc-exe> <base-exe> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 1800.0

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]


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


def run(exe, options, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    d = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", d)
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    send("go depth %d" % depth)
    bml = until("bestmove", d)
    time.sleep(0.2)
    send("quit")
    try:
        p.wait(timeout=180)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    scored = [l for l in dl if " score " in l]
    score = nodes = pv = ""
    maxdepth = 0
    if scored:
        f = scored[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
        if "pv" in f:
            pv = " ".join(f[f.index("pv") + 1:])
        if "depth" in f:
            maxdepth = int(f[f.index("depth") + 1])
    return {"score": score, "nodes": nodes, "pv": pv, "reached_depth": maxdepth,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def mate_n(score):
    m = re.match(r"mate (-?\d+)$", score.strip())
    return int(m.group(1)) if m else None


def first_move_resets(board_fen, mate_score):
    """Does the mating side's FIRST move capture or push a pawn (so the fifty-move counter resets)?"""
    b = chess.Board(board_fen)
    resets = []
    for m in b.legal_moves:
        is_reset = b.is_capture(m) or b.piece_at(m.from_square).piece_type == chess.PAWN
        b.push(m)
        # crude: does this move keep a forced mate? just record whether it resets and mates soon
        mates_now = b.is_checkmate()
        b.pop()
        if is_reset:
            resets.append((m.uci(), mates_now))
    return resets


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        ("A_mate1_h100_quiet", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1",
         "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 100, "my S-F5 / S-F17"),
        ("A2_mate1_h99_control", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1",
         "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 99, "control: one half-move left"),
        ("B_mate3_pawnmove_h100", "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1",
         "8/3K4/7P/8/8/7k/8/6Q1 w - - 0 1", 100, "my S-F22, counter-resetting line"),
        ("C_mate3_quiet_h99", "8/8/8/8/2K4Q/8/8/1k6 w - - 99 1",
         "8/8/8/8/2K4Q/8/8/1k6 w - - 0 1", 99, "my S-F23"),
    ]
    lines = ["applying FABLE_TO_swarm_6's prescribed test to MY OWN fifty-move findings",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "PC20 + Threads 1 + Hash 16 on the PC build; base build no setoption; go depth 20 everywhere",
             "file 6 rule: defect ONLY if 2N-1 <= 100-counter AND the real-counter board still scores cp 0",
             ""]
    lines.append("board\tmy claim\tmate N at counter 0\t2N-1\t100-counter\tinequality holds\t"
                 "real-counter base\treal-counter PC\tfile-6 verdict")
    rows = []
    for name, real_fen, zero_fen, counter, claim in boards:
        # the counters must line up: same board, counter 0
        z = run(pc, PC20, zero_fen, 20)
        rb = run(base, [], real_fen, 20)
        rp = run(pc, PC20, real_fen, 20)
        n = mate_n(z["score"])
        lhs = (2 * abs(n) - 1) if n is not None and n > 0 else None
        rhs = 100 - counter
        holds = (lhs is not None and lhs <= rhs)
        base_zero = (rb["score"] == "cp 0")
        resets = first_move_resets(zero_fen, n)
        if n is None:
            verdict = "NO MATE FOUND at counter 0 depth 20 -> not a defect by file 6"
        elif not holds:
            verdict = ("2N-1 = %d > 100-counter = %d -> NOT a defect by file 6 (the mate lands past the "
                       "cut-off)" % (lhs, rhs))
        elif base_zero:
            verdict = "DEFECT by file 6: inequality holds AND base scores cp 0 at the real counter"
        else:
            verdict = "inequality holds but the base does not score cp 0 -> not this defect"
        rows.append({"board": name, "claim": claim, "real_fen": real_fen, "counter": counter,
                     "counter0": z, "mate_n": n, "lhs": lhs, "rhs": rhs, "holds": holds,
                     "base_real": rb, "pc_real": rp, "base_cp0": base_zero,
                     "reset_moves": resets, "verdict": verdict})
        print("%-24s mate=%s  2N-1=%s 100-c=%d holds=%-5s base=%s pc=%s"
              % (name, n, lhs, rhs, holds, rb["score"], rp["score"]), flush=True)
        lines.append("%s\t%s\t%s\t%s\t%d\t%s\t%s (%s nodes)\t%s (%s nodes)\t%s"
                     % (name, claim, z["score"], lhs, rhs, holds, rb["score"], rb["nodes"],
                        rp["score"], rp["nodes"], verdict))

    v = []
    v.append("")
    v.append("WHAT THIS DOES TO MY OWN CLAIMS:")
    a = next(r for r in rows if r["board"] == "A_mate1_h100_quiet")
    b = next(r for r in rows if r["board"] == "B_mate3_pawnmove_h100")
    v.append("  A (my S-F5/S-F17, mate-in-1 at halfmove 100): %s" % a["verdict"])
    v.append("  B (my S-F22, counter-resetting pawn-move mate at halfmove 100): %s" % b["verdict"])
    (out / "apply_file6_test.json").write_text(json.dumps(
        {"boards": rows, "verdict": v}, indent=1))
    (out / "apply_file6_test.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
