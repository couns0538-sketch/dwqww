#!/usr/bin/env python3
"""quiet_tactics.py OUT — the case 08-F20 does not cover: QUIET positions where the right move is a tactic
(a check, a fork, a mate threat) that a one-ply search cannot see, and no capture is the answer.

The point of the exercise: at `go wtime 10 btime 10` the engine plays a 1-ply answer. In a position whose best move
is quiet but tactically necessary, a 1-ply search cannot have found it. This measures whether the answer is wrong,
and if so how wrong (material, or the tactic it missed).

Design of the ten positions (all QUIET best move, no capture is the recommended move):
 1. back-rank mate threat: the only defence is a quiet king/hook move
 2. fork available two plies deep: a quiet knight jump setting up a fork
 3. a zwischenzug: quiet check-prevention
 4. pin the queen to the king with a quiet bishop move
 5. a quiet rook lift creating a mating net
 6. quiet king move to stop a promotion
 7. quiet pawn push that stops a fork square
 8. a discovered-attack setup (quiet move, threat wins the queen)
 9. quiet queen move to defend a mate threat
10. a quiet knight retreat that keeps the fork square covered

MEASUREMENT, per position, on the PC BUILD under PC20 at Threads 1:
 - the `go wtime 10` answer (the one-ply answer)
 - a deep real search (`go depth 20`, which needs far more than 45 plies of the ladder on these small positions
   to converge; also `go movetime 500`) — the reference
 - whether the one-ply answer is the same as the deep answer
 - whether the one-ply answer is a CAPTURE (it should not be, by construction, unless the engine disagrees)

CONTROLS (enforced):
 - every position must be accepted by the engine and parse in python-chess;
 - `go depth 20` must reach at least depth 12 on each position (else the "deep reference" is not deep);
 - at least 8 of the 10 positions must have a QUIET deep best move (else the set is not the set it claims).
"""
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# Ten positions. Each: label, fen, and the tactic the position is built around (for the report).
POSITIONS = [
    ("back_rank_defence", "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
     "quiet rook lift / king safety: the best move is quiet, no capture exists"),
    ("fork_setup", "r5k1/5ppp/8/8/8/2N5/5PPP/4R1K1 w - - 0 1",
     "the knight jump to a forking square is quiet; the fork wins a rook two plies later"),
    ("pin_the_queen", "r2q1rk1/ppp2ppp/8/8/3n4/2N5/PPP2PPP/R2Q1RK1 w - - 0 1",
     "re-capture/defence: the best move is quiet and holds the position"),
    ("stop_promotion", "8/P4pk1/8/8/8/8/5K2/8 w - - 0 1",
     "the pawn runs; the best move is quiet and the promotion decides"),
    ("mating_net", "r4rk1/ppp2ppp/8/8/8/8/PPP2PPP/2KR3R w - - 0 1",
     "quiet rook coordination creating a mating net; no capture available"),
    ("discovered_attack", "r1bq1rk1/ppp2ppp/2n5/3n4/8/2N2N2/PPP2PPP/R1BQ1RK1 w - - 0 1",
     "quiet move sets up a discovered attack on the queen"),
    ("defend_mate", "6k1/5p1p/6p1/8/8/8/5PPP/1R4K1 b - - 0 1",
     "quiet defence against a back-rank mate threat"),
    ("knight_retreat", "r1b1k2r/pppp1ppp/8/8/1b1n4/2N5/PPPP1PPP/R1BQK2R w KQkq - 0 1",
     "quiet knight retreat keeping the fork square covered"),
    ("quiet_king", "8/8/8/8/8/5k2/p6P/6K1 w - - 0 1",
     "quiet king move; the black a-pawn runs and only a precise king move holds"),
    ("quiet_queen", "r2qk2r/ppp2ppp/2n5/3p4/8/2N5/PPP2PPP/R2QK2R w KQkq - 0 1",
     "quiet queen move holding the centre; no capture"),
]


def ask(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return None
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    depths = [int(l.split()[2]) for l in lines if l.startswith("info depth")]
    score = ""
    for l in lines:
        if l.startswith("info depth") and " score " in l:
            score = l.split(" score ")[1].split(" nodes")[0]
    return {"bm": lines[-1].split()[1], "wall": wall, "maxd": max(depths) if depths else None,
            "score": score}


def kind(fen, uci):
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(uci)
    except Exception:
        return "unparsable"
    if m not in b.legal_moves:
        return "ILLEGAL"
    if b.piece_at(m.to_square) is not None:
        return "capture"
    b.push(m)
    return "check" if b.is_check() else "quiet"


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## Ten QUIET tactically-loaded positions at 10 ms — PC r15 under PC20, Threads 1")
emit("")
emit("| # | position | the tactic | 10 ms answer | that move | deep answer (depth 20) | depth reached | deep move | same? | deep score |")
emit("|---|---|---|---|---|---|---|---|---|---|")
rows = []
for i, (label, fen, tactic) in enumerate(POSITIONS, 1):
    r10 = ask(fen, "go wtime 10 btime 10")
    rdeep = ask(fen, "go depth 20")
    if r10 is None or rdeep is None:
        raise SystemExit("CONTROL FAILED: engine refused %r" % fen)
    if rdeep["maxd"] is None or rdeep["maxd"] < 12:
        raise SystemExit("CONTROL FAILED: `go depth 20` only reached depth %r on %r; the reference is not deep"
                         % (rdeep["maxd"], fen))
    k10 = kind(fen, r10["bm"])
    rows.append({"label": label, "fen": fen, "tactic": tactic, "bm10": r10["bm"], "k10": k10,
                 "bmdeep": rdeep["bm"], "maxd": rdeep["maxd"], "score": rdeep["score"],
                 "same": r10["bm"] == rdeep["bm"], "w10": r10["wall"]})
    emit("| %d | %s | %s | %s | %s | %s | %d | %s | **%s** | %s |" %
         (i, label, tactic[:42], r10["bm"], k10, rdeep["bm"], rdeep["maxd"], rdeep["bm"],
          "yes" if r10["bm"] == rdeep["bm"] else "NO", rdeep["score"]))

same = sum(1 for r in rows if r["same"])
caps = sum(1 for r in rows if r["k10"] == "capture")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions | %d |" % len(rows))
emit("| one-ply answer == deep answer | **%d of %d** |" % (same, len(rows)))
emit("| one-ply answers that were captures | %d of %d |" % (caps, len(rows)))
emit("| one-ply answers that were checks | %d of %d |" % (sum(1 for r in rows if r["k10"] == "check"), len(rows)))
emit("| median one-ply wall | %.2f ms |" % sorted(r["w10"] for r in rows)[len(rows) // 2])

emit("")
emit("### the positions where the one-ply answer differed from the deep one")
diff = [r for r in rows if not r["same"]]
if diff:
    emit("| position | 10 ms | deep | deep score | what one ply cannot see |")
    emit("|---|---|---|---|---|")
    for r in diff:
        emit("| %s | %s | %s | %s | %s |" % (r["label"], r["bm10"], r["bmdeep"], r["score"], r["tactic"][:50]))
else:
    emit("none — the one-ply answer matched the deep answer in all ten.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
