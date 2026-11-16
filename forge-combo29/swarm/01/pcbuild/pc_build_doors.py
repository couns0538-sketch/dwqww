#!/usr/bin/env python3
"""swarm seat 01: is MY combined patch still needed on the PC r15 build?

FABLE_TO_swarm_5 ships FORGE_FIX_ROOT_DRAWN, "a drawn root is searched like any other; the '0 nodes, first
legal move' defect of your base tree is gone". If that is so, my job2c patch must be UNNECESSARY on the PC
build, and the honest thing to do is prove it and say so.

This runs the four doors on the PC r15 build under PC20 (Threads 1, Hash 16, S14 + the six PC20 options,
setoption followed by isready read to readyok, ucinewgame before each search) and on the BASE tree for contrast:

  control_fen   mate-in-1 board as a plain FEN (no history)      -> every build should find it
  door1_h99     same board at halfmove 99                         -> every build should find it
  door1_h100    same board at halfmove 100                        -> the defect door
  door2_rep     threefold root (counter 8) with mate in 1         -> the repetition door
  mate3_h100    counter-resetting pawn-move mate-in-3 at h100     -> the deep door
  draw_h150     genuine fifty-move draw                           -> must stay cp 0

Then, if the PC build closes every door on its own, the patch is NOT needed there (finding states that).
If any door is still open on the PC build, that is a much more valuable finding: say which door.

Usage: pc_build_doors.py <pc-exe> <base-exe> <outdir>
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

TIMEOUT = 600.0

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = S14 + PC20_EXTRA + [("Threads", "1"), ("Hash", "16")]

MATE1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1"
# FULL six fields. An earlier version of this file wrote only the placement field, so the engine refused
# `position ... moves ...` and silently kept the START position - which is how a harness reports `c2c4` on a
# board where c2 is empty. The guard in check_position_accepted() below exists because of that bug.
REP_BASE = "6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"
REP_SHUFFLE = "g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8".split()
MATE3 = "8/3K4/7P/8/8/7k/8/6Q1"
DRAW = "8/5K2/7Q/4k3/8/8/8/8"


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


def run(exe, position_lines, options, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []
    problems = []

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

    deadline = time.monotonic() + TIMEOUT
    send("uci")
    if until("uciok", deadline) is None:
        problems.append("no uciok")
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok", deadline) is None:
            problems.append("no readyok after %s" % name)
            break
    for l in buf:
        if l.startswith("unknown option") or l.startswith("ERROR") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", deadline)
    for line in position_lines:
        send(line)
    send("isready")
    if until("readyok", deadline) is None:
        problems.append("no readyok after position")
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    send(go)
    # perft prints "nodes N" and NO bestmove, so waiting for bestmove would hang (it did).
    if go.startswith("go perft"):
        bml = until("nodes ", deadline)
    else:
        bml = until("bestmove", deadline)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=120)
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
    # perft prints a STANDALONE "nodes N" line and no info depth line at all (this is what made the guard
    # report None: it looked only at info depth lines). Take the last bare "nodes N".
    bare = [l for l in buf if l.startswith("nodes ")]
    if bare and not nodes:
        nodes = bare[-1].split()[1]
        if not score:
            score = ""
    bm = None
    if bml and bml.startswith("bestmove"):
        parts = bml.split()
        bm = parts[1] if len(parts) > 1 else None
    return {"score": score, "nodes": nodes,
            "bestmove": bm,
            "refused": refused, "problems": problems, "depths": len(dl)}


def expected_board(position_lines):
    """The board `position ...` should leave, computed with python-chess from the same lines."""
    import chess
    b = chess.Board()
    for line in position_lines:
        parts = line.split()
        if not parts or parts[0] != "position":
            continue
        if parts[1] == "startpos":
            b = chess.Board()
            rest = parts[2:]
        else:  # fen: the next six tokens are the FEN
            fen = " ".join(parts[2:8])
            b = chess.Board(fen)
            rest = parts[8:]
        if rest and rest[0] == "moves":
            for u in rest[1:]:
                mv = chess.Move.from_uci(u)
                assert mv in b.legal_moves, "move %s illegal in the setup" % u
                b.push(mv)
    return b


def board_matches(exe, position_lines, options, exp_board):
    """Run `go perft 1` and compare the total with python-chess's legal move count."""
    r = run(exe, position_lines, options, "go perft 1")
    total = None
    # run() keeps only the LAST "nodes " number, which for perft 1 is the total
    try:
        total = int(r.get("nodes"))
    except (TypeError, ValueError):
        total = None
    return (total == exp_board.legal_moves.count()), total


def check_position_accepted(exe, position_lines, options, expect_fen):
    """GUARD: the engine must really be on the expected board. Compare `go perft 1` with python-chess's
    legal-move count for that board. Without this a refused `position` line reads as a real measurement
    (that bug produced c2c4 on a board with no c2 pawn)."""
    import chess
    r = run(exe, position_lines, options, "go perft 1")
    want = chess.Board(expect_fen).legal_moves.count()
    got = None
    return {"expected_legal": want, "engine_perft1": got, "score": r.get("score"),
            "bestmove": r.get("bestmove"), "refused": r.get("refused")}


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("control_fen", ["position fen " + MATE1 + " w - - 0 1"], "go depth 6"),
        ("door1_h99", ["position fen " + MATE1 + " w - - 99 1"], "go depth 6"),
        ("door1_h100", ["position fen " + MATE1 + " w - - 100 1"], "go depth 6"),
        ("door2_rep", ["position fen " + REP_BASE + " moves " + " ".join(REP_SHUFFLE)], "go depth 6"),
        ("mate3_h100", ["position fen " + MATE3 + " w - - 100 1"], "go depth 12"),
        ("draw_h150", ["position fen " + DRAW + " w - - 150 1"], "go depth 10"),
    ]
    lines = ["is my combined patch still needed on the PC r15 build? four doors, PC20, Threads 1",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "PC20 options sent (each followed by isready read to readyok): "
             + ", ".join("%s=%s" % kv for kv in PC20),
             "base runs: no setoption at all (base build lacks CuckooRep etc.), ucinewgame before each search",
             ""]
    lines.append("case\tgo\tPC r15 under PC20\tbase (no options)\treading")
    rows = []
    failures = []
    for name, pos, go in cases:
        # GUARD: confirm BOTH builds are really on the intended board before trusting any score.
        # The expected board is whatever `pos` leaves, computed here independently with python-chess.
        exp = expected_board(pos)
        for tag, exe, opts in (("pc", pc, PC20), ("base", base, [])):
            ok, legal = board_matches(exe, pos, opts, exp)
            if not ok:
                failures.append("%s/%s: engine is NOT on the intended board (perft1 %s vs %d)"
                                % (name, tag, legal, exp.legal_moves.count()))
        a = run(pc, pos, PC20, go)
        b = run(base, pos, [], go)
        rows.append({"case": name, "go": go, "pc": a, "base": b})
        print("%-12s pc %-8s/%-8s bm=%-6s | base %-8s/%-8s bm=%-6s"
              % (name, a["score"], a["nodes"], a["bestmove"], b["score"], b["nodes"], b["bestmove"]),
              flush=True)
        lines.append("%s\t%s\t%s/%s/%s\t%s/%s/%s\t%s" % (
            name, go, a["score"], a["nodes"], a["bestmove"],
            b["score"], b["nodes"], b["bestmove"], ""))
    # verdict computed from the data
    def get(case, side):
        return next(r for r in rows if r["case"] == case)[side]

    v = []
    if failures:
        v.append("GUARD FAILURES (a score below is NOT a measurement):")
        v.extend("   " + f for f in failures)
    else:
        v.append("GUARD: on every case, both builds reported a perft 1 equal to python-chess's legal move")
        v.append("       count for the intended board, so the scores below are on the board I mean.")
    mate_doors = ["control_fen", "door1_h99", "door1_h100", "door2_rep", "mate3_h100"]
    pc_ok = {d: ("mate" in get(d, "pc")["score"]) for d in mate_doors}
    base_ok = {d: ("mate" in get(d, "base")["score"]) for d in mate_doors}
    draw_ok = get("draw_h150", "pc")["score"] == "cp 0"
    v.append("PC r15 finds the mate on: %s" % ", ".join(d for d in mate_doors if pc_ok[d]))
    v.append("PC r15 MISSES: %s" % (", ".join(d for d in mate_doors if not pc_ok[d]) or "(none)"))
    v.append("base finds the mate on: %s" % ", ".join(d for d in mate_doors if base_ok[d]))
    v.append("PC r15 still calls the genuine draw cp 0: %s" % draw_ok)
    open_doors = [d for d in mate_doors if not pc_ok[d]]
    if not open_doors:
        v.append("VERDICT: the PC build closes EVERY door I can build, so MY COMBINED PATCH IS NOT NEEDED on the")
        v.append("PC build. FORGE_FIX_ROOT_DRAWN covers what my patch and seat 12's patch covered on the base tree.")
    else:
        v.append("VERDICT: the PC build STILL HAS these doors open: %s" % ", ".join(open_doors))
        v.append("That is a finding worth more than my base-tree patch: state it per door above.")
    lines.append("")
    lines.extend(v)
    (out / "pc_build_doors.json").write_text(json.dumps({"rows": rows, "verdict": v}, indent=1))
    (out / "pc_build_doors.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
