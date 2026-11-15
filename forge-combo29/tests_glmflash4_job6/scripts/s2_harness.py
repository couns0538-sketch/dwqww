#!/usr/bin/env python3
"""Job 6 step 2: show the seven Syzygy-gap faults by hand, bit off vs on.

usage: s2_harness.py <engine> <syzygy_dir> <outdir> <fixtures_dir> <which>
UCI is driven directly; python-chess + the same table folder is the oracle.
G1 uses the branch's own zz2roots.fens rows (4-men rows are oracle-checkable
with the reachable 3-4-man subset). The other faults use constructed cases in
covered materials because the branch's own fixtures are 5-6 men (the reachable
subset answers only up to 4); each case carries the mechanism the branch
describes.
"""
import os
import re
import subprocess
import sys

import chess
import chess.syzygy

ENGINE, SYZ, OUTDIR, FIX = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
WHICH = sys.argv[5] if len(sys.argv) > 5 else "all"

info_re = re.compile(r"score (cp|mate) (-?\d+)")
nodes_re = re.compile(r" nodes (\d+)")
best_re = re.compile(r"bestmove (\S+)")

oracle = chess.syzygy.open_tablebase(SYZ)


class Engine:
    def __init__(self, setup=None):
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, bufsize=1)
        for cmd in (setup or []):
            self.p.stdin.write(cmd + "\n")

    def search(self, fen: str, go: str, new: bool = True):
        """position + go; returns (score, nodes, bestmove). With new=True an
        ucinewgame is sent first (clears the TT); with new=False the previous
        search's TT state is kept on purpose (the G7/G8 scenarios)."""
        if new:
            self.p.stdin.write("ucinewgame\n")
        self.p.stdin.write(f"position fen {fen}\n")
        self.p.stdin.write(go + "\n")
        score = nodes = None
        best = None
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("engine died")
            m = info_re.search(line)
            if m:
                score = f"{m.group(1)} {m.group(2)}"
                nm = nodes_re.search(line)
                if nm:
                    nodes = int(nm.group(1))
            b = best_re.search(line)
            if b:
                best = b.group(1)
                break
        return score, nodes, best

    def raw(self, cmd: str):
        self.p.stdin.write(cmd + "\n")

    def quit(self):
        self.raw("quit")
        try:
            self.p.stdin.close()
        except Exception:
            pass
        self.p.wait()


def out(name, text):
    with open(os.path.join(OUTDIR, name), "w") as f:
        f.write(text)
    print(f"== {name}: " + text.splitlines()[0])


def tb_class(board: chess.Board):
    """Oracle class at this clock: win/cursed/draw/blessed/loss/boundary-*."""
    try:
        wdl = oracle.probe_wdl(board)
        dtz = oracle.probe_dtz(board)
    except Exception:
        return None
    c = board.halfmove_clock
    if wdl == 0:
        return "draw"
    if wdl == 2:
        if dtz > 0 and dtz + c <= 99:
            return "win"
        if dtz > 0 and dtz + c == 100:
            return "boundary-win"
        if dtz > 0 and dtz + c > 100:
            return "cursed"
        return "win/odd-dtz"
    if wdl == -2:
        if dtz < 0 and -dtz + c <= 99:
            return "loss"
        if dtz < 0 and -dtz + c == 100:
            return "boundary-loss"
        if dtz < 0 and -dtz + c > 100:
            return "blessed"
        return "loss/odd-dtz"
    return f"wdl{wdl}"


def engine_class(score: str):
    if score is None:
        return None
    if score.startswith("cp"):
        v = int(score.split()[1])
        if abs(v) >= 31743:
            return "tbwin" if v > 0 else "tbloss"
        if v == 2:
            return "cursed"
        if v == -2:
            return "blessed"
        if v == 0:
            return "draw"
        return "search"
    if score.startswith("mate"):
        return "mate"
    return score


def set_with_clock(fen: str, clock: int) -> str:
    parts = fen.split(" ")
    return " ".join(parts[:4]) + f" {clock} 1"


# ------------------------------------------------------------------ G8 toggle
def g8(bit_on: bool):
    setup = ["setoption name SyzygyPath value " + SYZ,
             "setoption name SyzygyRule50 value " + ("2" if bit_on else "0")]
    e = Engine(setup)
    # clock-dependent cases: with the rule ON these are cursed wins / blessed
    # losses (score +-2); with the rule OFF they are full TB wins / losses. A
    # stale entry stored under the other rule therefore shows the wrong class.
    rows = ["8/8/8/3k4/8/8/5Q2/6K1 w - - 90 1", "8/8/8/3k4/8/8/5R2/6K1 w - - 90 1",
            "8/8/8/3k4/8/8/5R2/6K1 b - - 90 1", "8/8/8/3k4/8/8/5Q2/6K1 b - - 92 1",
            "8/8/8/2k5/8/8/5R2/6K1 w - - 94 1"]
    diffs = 0
    lines = []
    for fen in rows:
        s1, n1, b1 = e.search(fen, "go depth 12")            # rule true (default)
        e.raw("setoption name Syzygy50MoveRule value false")  # toggle, no clear
        s2, n2, b2 = e.search(fen, "go depth 12", new=False)  # post-toggle, warm histories
        # reference: the branch compares against a manual Clear Hash (TT only,
        # histories stay warm) - NOT against ucinewgame
        e.raw("setoption name Clear Hash")
        s3, n3, b3 = e.search(fen, "go depth 12", new=False)
        e.raw("setoption name Syzygy50MoveRule value true")
        same = (n2 == n3 and s2 == s3 and b2 == b3)
        if not same:
            diffs += 1
        lines.append(f"{fen} | rule-true {s1}/{n1} | after-toggle {s2}/{n2} | fresh-false {s3}/{n3} | same={same}")
    e.quit()
    return diffs, len(rows), lines


# --------------------------------------------------------------- G7 stale TT
def g7(bit_on: bool):
    setup = ["setoption name SyzygyPath value " + SYZ,
             "setoption name SyzygyRule50 value " + ("1" if bit_on else "0")]
    e = Engine(setup)
    cases = []
    for fen0 in ["8/8/8/3k4/8/8/5Q2/6K1 w - - 0 1", "8/8/8/3k4/8/8/5R2/6K1 w - - 0 1"]:
        b = chess.Board(fen0)
        dtz = oracle.probe_dtz(b)
        clock = 100 - dtz + 12  # stored win (dtz plies) cannot complete: dtz+clock > 100
        late = set_with_clock(fen0, clock)
        truth_late = tb_class(chess.Board(late))
        s_w, n_w, b_w = e.search(fen0, "go depth 16")      # warm: probes store TB scores
        s_s, n_s, b_s = e.search(late, "go depth 16", new=False)  # SAME TT, clock raised
        # reference: manual Clear Hash (TT only), histories stay warm
        e.raw("setoption name Clear Hash")
        s_f, n_f, b_f = e.search(late, "go depth 16", new=False)
        cases.append(f"{fen0} dtz={dtz} -> late {late} | oracle-late {truth_late} | "
                     f"warm {s_w}/{n_w} | staleTT {s_s}/{n_s}/{b_s} | fresh {s_f}/{n_f}/{b_f}")
    e.quit()
    return cases


# --------------------------------------------------------------- G6 wdl only
def g6(bit_on: bool):
    wdl_dir = "/tmp/syzygy_wdl_only"
    os.makedirs(wdl_dir, exist_ok=True)
    for f in os.listdir(SYZ):
        if f.endswith(".rtbw") and not os.path.exists(os.path.join(wdl_dir, f)):
            os.link(os.path.join(SYZ, f), os.path.join(wdl_dir, f))
    setup = ["setoption name SyzygyPath value " + wdl_dir,
             "setoption name SyzygyRootExact value " + ("1" if bit_on else "0")]
    e = Engine(setup)
    rows = ["8/8/8/3k4/8/8/5Q2/6K1 w - - 40 1", "8/8/8/3k4/8/8/5Q2/6K1 w - - 84 1",
            "8/8/8/3k4/8/8/5R2/6K1 w - - 60 1", "8/8/8/3k4/8/8/5R2/6K1 w - - 72 1",
            "8/8/8/8/8/5k2/6r1/6K1 b - - 30 1", "8/8/8/8/8/5k2/6r1/6K1 b - - 75 1"]
    lines = []
    claims = wrong = 0
    for fen in rows:
        b = chess.Board(fen)
        truth = tb_class(b)
        s, n, mv = e.search(fen, "go depth 12")
        cls = engine_class(s)
        band = cls in ("tbwin", "tbloss")
        claims += band
        is_wrong = band and truth not in ("win", "loss")
        wrong += is_wrong
        lines.append(f"{fen} | oracle {truth} | engine {s} ({cls}) | move {mv} | wrong={is_wrong}")
    e.quit()
    return claims, wrong, lines


# -------------------------------------------------------------- G5 boundary
def g5(bit_on: bool):
    setup = ["setoption name SyzygyPath value " + SYZ,
             "setoption name SyzygyRootExact value " + ("3" if bit_on else "0")]
    e = Engine(setup)
    lines = []
    for fen0 in ["8/8/8/3k4/8/8/5Q2/6K1 w - - 0 1", "8/8/8/3k4/8/8/5R2/6K1 w - - 0 1",
                 "8/8/4k3/8/8/8/4N3/6K1 w - - 0 1"]:
        dtz = oracle.probe_dtz(chess.Board(fen0))
        clock = 100 - dtz
        fen_b = set_with_clock(fen0, clock)
        truth = tb_class(chess.Board(fen_b))
        s, n, mv = e.search(fen_b, "go depth 12")
        lines.append(f"{fen_b} | dtz {dtz} | oracle {truth} | engine {s} ({engine_class(s)}) | move {mv}")
    e.quit()
    return lines


# ------------------------------------------------------------- G2 prune scan
def g2(bit_on: bool):
    setup = ["setoption name SyzygyPath value " + SYZ,
             "setoption name SyzygyTbBounds value " + ("1" if bit_on else "0")]
    e = Engine(setup)
    import random
    random.seed(8110)
    piece_of = {"Q": chess.QUEEN, "R": chess.ROOK, "B": chess.BISHOP,
                "N": chess.KNIGHT, "P": chess.PAWN}
    mats = ["KPvKP", "KNvKP", "KBvKP", "KRvKP", "KQvKP", "KPvKN", "KPvKB",
            "KRvKN", "KQvKN", "KNvKN", "KBvKB", "KNvKB", "KPvKQ", "KPvKR"]
    boards = []
    for mat in mats:
        w, bl = mat.split("v")
        for _ in range(40):
            board = chess.Board(None)
            squares = random.sample(range(64), len(w) + len(bl))
            it = iter(squares)
            board.set_piece_at(next(it), chess.Piece(chess.KING, chess.WHITE))
            for ch in w[1:]:
                board.set_piece_at(next(it), chess.Piece(piece_of[ch], chess.WHITE))
            board.set_piece_at(next(it), chess.Piece(chess.KING, chess.BLACK))
            for ch in bl[1:]:
                board.set_piece_at(next(it), chess.Piece(piece_of[ch], chess.BLACK))
            if board.is_valid() and not board.is_insufficient_material():
                boards.append(board)
    wrong = checked = 0
    lines = []
    for b in boards:
        if checked >= 250:
            break
        s, n, mv = e.search(b.fen(), "go depth 10")
        truth = tb_class(b)
        if truth is None or s is None:
            continue
        checked += 1
        cls = engine_class(s)
        ok = True
        if truth == "draw" and cls in ("tbwin", "tbloss"):
            ok = False
        if truth == "win" and cls in ("tbloss", "blessed"):
            ok = False
        if truth == "loss" and cls in ("tbwin", "cursed"):
            ok = False
        if truth == "cursed" and cls in ("tbwin", "tbloss", "draw"):
            ok = False
        if truth == "blessed" and cls in ("tbwin", "tbloss", "draw"):
            ok = False
        if truth == "boundary-win" and cls in ("tbloss", "blessed"):
            ok = False
        if truth == "boundary-loss" and cls in ("tbwin", "cursed"):
            ok = False
        if not ok:
            wrong += 1
            lines.append(f"{b.fen()} | engine {s} ({cls}) | oracle {truth} | move {mv}")
    e.quit()
    return wrong, checked, lines


# ---------------------------------------------------------------- G1 zugzwang
def g1(bit_on: bool):
    setup = ["setoption name SyzygyPath value " + SYZ,
             "setoption name SyzygyTbBounds value " + ("7" if bit_on else "3")]
    e = Engine(setup)
    rows = []
    for line in open(f"{FIX}/zz2roots.fens"):
        fen = line.strip()
        if fen and chess.popcount(chess.Board(fen).occupied) <= 4:
            rows.append(fen)
    rows = rows[:60]
    lines = []
    for fen in rows:
        b = chess.Board(fen)
        truth = tb_class(b)
        s, n, mv = e.search(fen, "go depth 14")
        lines.append(f"{fen} | engine {s} ({engine_class(s)}) | move {mv} | oracle {truth}")
    e.quit()
    return len(rows), lines


# ---------------------------------------------------------------- G3 activity
def g3():
    setup = ["setoption name SyzygyPath value " + SYZ]
    e = Engine(setup)
    rows = ["8/8/8/3k4/8/8/5Q2/6K1 w - - 0 1", "8/8/8/3k4/8/8/5R2/6K1 w - - 0 1",
            "8/8/4k3/8/8/8/4N3/6K1 w - - 0 1", "8/8/8/3p4/8/8/5P2/6K1 w - - 0 1"]
    lines = []
    diffs = 0
    for fen in rows:
        e.raw("setoption name SyzygyTbBounds value 0")
        s0, n0, _ = e.search(fen, "go depth 14")
        e.raw("setoption name SyzygyTbBounds value 2")
        s2, n2, _ = e.search(fen, "go depth 14")
        if n0 != n2 or s0 != s2:
            diffs += 1
        lines.append(f"{fen} | bit2off {s0}/{n0} | bit2on {s2}/{n2}")
    e.quit()
    return diffs, len(rows), lines


if __name__ == "__main__":
    if WHICH in ("all", "g8off"):
        d, n, lines = g8(False)
        out("P_step2_G8_bit2off.txt", f"rows {n}, toggle-vs-fresh differences {d}\n" + "\n".join(lines))
    if WHICH in ("all", "g8on"):
        d, n, lines = g8(True)
        out("P_step2_G8_bit2on.txt", f"rows {n}, toggle-vs-fresh differences {d}\n" + "\n".join(lines))
    if WHICH in ("all", "g7off"):
        out("P_step2_G7_bit1off.txt", "\n".join(g7(False)))
    if WHICH in ("all", "g7on"):
        out("P_step2_G7_bit1on.txt", "\n".join(g7(True)))
    if WHICH in ("all", "g6off"):
        cl, w, lines = g6(False)
        out("P_step2_G6_bit1off.txt", f"TB-band root claims {cl}, wrong-vs-oracle {w}\n" + "\n".join(lines))
    if WHICH in ("all", "g6on"):
        cl, w, lines = g6(True)
        out("P_step2_G6_bit1on.txt", f"TB-band root claims {cl}, wrong-vs-oracle {w}\n" + "\n".join(lines))
    if WHICH in ("all", "g5off"):
        out("P_step2_G5_bits_off.txt", "\n".join(g5(False)))
    if WHICH in ("all", "g5on"):
        out("P_step2_G5_bits_on.txt", "\n".join(g5(True)))
    if WHICH in ("all", "g2off"):
        w, n, lines = g2(False)
        out("P_step2_G2_bit1off.txt", f"checked {n}, root-vs-oracle disagreements {w}\n" + "\n".join(lines[:50]))
    if WHICH in ("all", "g2on"):
        w, n, lines = g2(True)
        out("P_step2_G2_bit1on.txt", f"checked {n}, root-vs-oracle disagreements {w}\n" + "\n".join(lines[:50]))
    if WHICH in ("all", "g1off"):
        n, lines = g1(False)
        out("P_step2_G1_bit4off.txt", f"branch rows used {n}\n" + "\n".join(lines))
    if WHICH in ("all", "g1on"):
        n, lines = g1(True)
        out("P_step2_G1_bit4on.txt", f"branch rows used {n}\n" + "\n".join(lines))
    if WHICH in ("all", "g3"):
        d, n, lines = g3()
        out("P_step2_G3_activity.txt", f"rows {n}, output differences bit2off-vs-bit2on {d}\n" + "\n".join(lines))
