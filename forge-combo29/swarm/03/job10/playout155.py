#!/usr/bin/env python3
"""playout155.py OUTFILE : independent verdict on position 155 by PLAY-OUT, not by the engine's scores.

For each candidate first move (c6d6 and c6c7), python-chess makes that move, then BOTH sides are played by the
engine at a FIXED depth under PC20, and python-chess decides the result (checkmate / draw / 120-ply cutoff). The
engine's scores are ignored entirely; only the game outcome and its length are recorded.

Determinism: each candidate is played 3 times with identical settings. If repeats diverge, that is recorded as a
non-deterministic adjudication rather than averaged away.

Rules obeyed: Threads 1, Hash 16, PC20, one search per fresh process, read to `bestmove` before sending anything
else, `quit` only after bestmove.
"""
import hashlib
import os
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = os.environ.get("PO_EXE", "/home/ubuntu/build-pc/forge")
START = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
MAXPLIES = 120
REPEATS = int(os.environ.get("PO_REPEATS", "3"))
DEPTH = int(os.environ.get("PO_DEPTH", "12"))
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)

PC20 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
        ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
        ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
        ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
        ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def uci_option_names():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        s = line.strip()
        if s.startswith("option name "):
            names.add(s[len("option name "):].split(" type ")[0])
        if s == "uciok":
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except Exception:  # noqa: BLE001
        p.kill()
    return names


AVAILABLE = uci_option_names()
# Send only options the exe actually lists, so the base build (no PC20 extras) is driven by S14 alone and the PC
# build by the full PC20 set. A requested option that is missing is reported, never silently skipped in a way that
# could mix regimes without saying so.
SENT = [(o, v) for o, v in PC20 if o in AVAILABLE]
SKIPPED = [(o, v) for o, v in PC20 if o not in AVAILABLE]
print(f"options sent: {len(SENT)}; not present in this exe and therefore NOT sent: {[o for o, _ in SKIPPED]}",
      flush=True)


def bestmove_for(fen, tag):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s
            for w in ("unknown option", "invalid value", "ERROR", "invalid FEN", "illegal move"):
                if w in s:
                    raise RuntimeError(f"engine refused ({tag}): {s}")

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in SENT:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH}")
    bm = None
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return bm


def play(first_move, rep):
    b = chess.Board(START)
    b.push_uci(first_move)
    plies = 1
    while plies < MAXPLIES:
        if b.is_game_over(claim_draw=False):
            break
        fen = b.fen()
        h = hashlib.sha1(fen.encode()).hexdigest()[:12]
        mv = bestmove_for(fen, f"{first_move}_r{rep}_p{plies:03d}_{h}")
        if mv not in [m.uci() for m in b.legal_moves]:
            raise RuntimeError(f"ENGINE PLAYED AN ILLEGAL MOVE: {mv} at ply {plies} ({fen})")
        if mv == "0000":
            raise RuntimeError(f"engine answered 0000 on a position with legal moves ({fen})")
        b.push_uci(mv)
        plies += 1
    if b.is_checkmate():
        result = "black mates" if b.turn == chess.WHITE else "white mates"
    elif b.is_game_over(claim_draw=False):
        result = "draw by rule"
    else:
        result = f"cut off at {MAXPLIES} plies"
    return result, plies, b.fen()


lines = [f"start: {START}", f"engine: {EXE}", f"settings: PC20, Threads 1, Hash 16, go depth {DEPTH}",
         f"adjudication: python-chess decides the result; engine scores are ignored", ""]
summary = {}
for first in ("c6d6", "c6c7"):
    lines.append(f"=== first move {first}")
    outcomes = []
    for rep in range(1, REPEATS + 1):
        result, plies, fen = play(first, rep)
        outcomes.append((result, plies))
        lines.append(f"  repeat {rep}: {result} after {plies} plies   final {fen}")
        print(f"{first} rep {rep}: {result} after {plies} plies", flush=True)
    summary[first] = outcomes
    lines.append("")

lines.append("=== paired comparison (plies survived by white)")
for i in range(REPEATS):
    a = summary["c6d6"][i]
    b = summary["c6c7"][i]
    lines.append(f"  pair {i+1}: c6d6 {a[1]} plies ({a[0]})   c6c7 {b[1]} plies ({b[0]})")
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[-6:]))
