#!/usr/bin/env python3
"""verify_all.py EXE : re-verifies every headline claim of seat 25 from scratch, one command.

Each claim is checked by its own minimum sufficient evidence, and the script prints PASS/FAIL per claim
plus a final count. A FAIL means I must withdraw or correct the corresponding finding.
"""
import re
import shlex
import subprocess
import sys

import chess

EXE = sys.argv[1]
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def search(fen, depth, s14=True, hash_mb=16, fresh_newgame=True):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write(f"setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    if s14:
        for n, v in S14:
            p.stdin.write(f"setoption name {n} value {v}\n")
        p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    if fresh_newgame:
        p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    reached = 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth") and " pv" in line:
            last = line
            d = re.search(r"depth (\d+)", line)
            if d:
                reached = int(d.group(1))
        if line.startswith("bestmove"):
            best = line.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if not last:
        return None, None, 0
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:]
    return ((m.group(1), int(m.group(2))) if m else None), pv, reached


results = []


def claim(name, ok, detail):
    results.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# 1. S-F1: depth 12 gives mate -12 with an 18-ply PV
sc, pv, d = search("8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", 12)
claim("S-F1 depth-12 mate number", sc == ("mate", -12) and len(pv) == 18 and d == 12,
      f"{sc} pv {len(pv)} plies reached depth {d}")

# 2. S-F1 truth: the engine's own deep answer checkmates in the plies it claims.
#    NOTE: a search may stop before the requested depth when the TT fills, so the deep answer is read
#    from whatever depth was REACHED, and only a COMPLETED iteration is trusted.
sc24, pv24, d24 = search("8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", 24, hash_mb=64)
b = chess.Board("8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1")
ok_moves = True
for mv in pv24:
    m = chess.Move.from_uci(mv)
    if m not in b.legal_moves:
        ok_moves = False
        break
    b.push(m)
claim("S-F1 truth: deep search gives mate -4 and its 8-ply PV is a real mate",
      sc24 == ("mate", -4) and len(pv24) == 8 and ok_moves and b.is_checkmate(),
      f"{sc24} pv {len(pv24)} checkmate={b.is_checkmate()} (reached depth {d24})")

# 3. S-F1 score is stable across Hash sizes (so not a TT-size artefact)
vals = [search("8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", 12, hash_mb=h)[0] for h in (1, 64, 256)]
claim("S-F1 unchanged by Hash 1/64/256 MB", vals == [("mate", -12)] * 3, f"{vals}")

# 4. S-F3: clock 98 is normal, clock 99 is 0
fen98 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 98 1"
fen99 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"
s98, _, _ = search(fen98, 10)
s99, _, _ = search(fen99, 10)
claim("S-F3 boundary clock 98 vs 99", bool(s98) and s98[0] == "cp" and s98[1] != 0 and s99 == ("cp", 0),
      f"clock 98 -> {s98}, clock 99 -> {s99}")

# 5. S-F3: clock 99 collapses at depth 20 too (not a horizon)
s99d20, _, d99 = search(fen99, 20)
claim("S-F3 clock-99 zero at depth 20", s99d20 == ("cp", 0), f"depth 20 -> {s99d20} (reached {d99})")

# 6. S-F6: checkmated root reports mate 0  (terminal roots emit a bare 'pv' with no moves)
scm, _, _ = search("8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1", 5)
claim("S-F6 checkmated root says mate 0", scm == ("mate", 0), f"{scm}")

# 7. S-F6 control: same engine on a stalemated root says cp 0 (different currency, same position class)
scs, _, _ = search("8/2q5/8/8/8/1q6/5k2/7K w - - 0 1", 5)
claim("S-F6 stalemated root says cp 0 (inconsistent with the above)", scs == ("cp", 0), f"{scs}")

# 8. S-F8: middlegame mate -9 at d12, and a deep search giving mate -7 whose PV is a real mate.
#    The deep part is read at Hash 64 because at Hash 16 the table fills (hashfull 1000) and the
#    search stops early at a DIFFERENT answer -- recorded honestly here.
fen8 = "2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22"
sc8, pv8, d8 = search(fen8, 12)
sc8d, pv8d, d8d = search(fen8, 24, hash_mb=64)
b8 = chess.Board(fen8)
ok8 = True
for mv in pv8d:
    m = chess.Move.from_uci(mv)
    if m not in b8.legal_moves:
        ok8 = False
        break
    b8.push(m)
claim("S-F8 depth-12 mate -9 vs deep mate -7 with a real 14-ply mate",
      sc8 == ("mate", -9) and sc8d == ("mate", -7) and len(pv8d) == 14 and ok8 and b8.is_checkmate(),
      f"d12 {sc8} ({len(pv8)} plies), deep {sc8d} ({len(pv8d)} plies, reached {d8d}), "
      f"checkmate={b8.is_checkmate()}")

# 9. Hash-16 deep answer for S-F8, recorded because it DIFFERS (evidence, not a claim)
sc8h16, pv8h16, d8h16 = search(fen8, 24, hash_mb=16)
print(f"[note] S-F8 deep at Hash 16: {sc8h16} pv {len(pv8h16)} reached depth {d8h16} "
      f"(table fills at Hash 16; this is a different answer from Hash 64 and is recorded, not used)")

print()
npass = sum(1 for _, ok in results if ok)
print(f"{npass}/{len(results)} claims PASS")
sys.exit(0 if npass == len(results) else 3)
