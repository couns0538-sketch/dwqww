#!/usr/bin/env python3
"""ep_pin_control.py EXE OUT : the control that makes ep_pin_compare.py meaningful.

For each constructed class-B position, remove the enemy slider that pins our pawn to our king and ask again:
  * in the ORIGINAL position the ep capture must be absent from python-chess's legal moves (the pin),
  * in the SLIDER-REMOVED position the same ep capture must be PRESENT and legal (so the position really is about
    the pin, not about a pawn that could never capture),
  * and the engine's root move set must agree with python-chess in BOTH cases.
A set of positions that fails this control would make "the engine omits the ep capture" meaningless: it would be
omitting a move that is illegal for a different reason.
"""
import os
import subprocess
import sys

import chess

EXE, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT + ".raw", exist_ok=True)
rows = [l.rstrip("\n").split("\t") for l in open(SET) if l.strip()]

SLIDERS = (chess.ROOK, chess.QUEEN, chess.BISHOP)


def engine_moves(exe, fen, rawpath):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(rawpath, "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                return None
            raw.write(line)
            raw.flush()
            if line.strip().startswith(tok):
                return line.strip()

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}"); send("isready"); until("readyok")
    send("go perft 1")
    mv = []
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("nodes "):
            break
        if ":" in s and not s.startswith(("info", "option", "id")):
            mv.append(s.split(":")[0].strip())
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return sorted(mv)


def ep_capture_uci(board):
    """the uci string of the raw ep capture, if there is a raw one."""
    ep = board.ep_square
    if ep is None:
        return None
    us = board.turn
    cap_sq = ep - 8 if us == chess.WHITE else ep + 8
    for df in (-1, 1):
        f = chess.square_file(cap_sq) + df
        if not 0 <= f <= 7:
            continue
        frm = chess.square(f, chess.square_rank(cap_sq))
        p = board.piece_at(frm)
        if p and p.piece_type == chess.PAWN and p.color == us:
            return chess.square_name(frm) + chess.square_name(ep)
    return None


rowsout, bad = [], 0
for i, row in enumerate(rows):
    fen = row[2]
    b = chess.Board(fen)
    cap = ep_capture_uci(b)
    if cap is None:
        rowsout.append((i, fen, "NO_RAW_EP", "", ""))
        bad += 1
        continue
    # original: the ep capture must NOT be legal
    orig_legal = cap in {m.uci() for m in b.legal_moves}
    # find the slider that pins and remove exactly it
    stripped_fen, removed = None, None
    for sq in chess.SQUARES:
        p = b.piece_at(sq)
        if p and p.color != b.turn and p.piece_type in SLIDERS:
            b2 = b.copy(stack=False)
            b2.remove_piece_at(sq)
            if cap in {m.uci() for m in b2.legal_moves} and cap not in {m.uci() for m in b.legal_moves}:
                stripped_fen = b2.fen(en_passant="fen")
                removed = chess.square_name(sq)
                break
    eng_orig = engine_moves(EXE, fen, f"{OUT}.raw/b{i:03d}_orig.txt")
    py_orig = sorted(m.uci() for m in b.legal_moves)
    ok_orig = eng_orig == py_orig
    if stripped_fen is None:
        rowsout.append((i, fen, "NO_PINNER_FOUND", cap, f"orig_legal={orig_legal} engine_match={ok_orig}"))
        bad += 1
        continue
    b3 = chess.Board(stripped_fen)
    py_strip = sorted(m.uci() for m in b3.legal_moves)
    eng_strip = engine_moves(EXE, stripped_fen, f"{OUT}.raw/b{i:03d}_strip.txt")
    ok_strip = eng_strip == py_strip
    strip_allows = cap in py_strip
    good = (not orig_legal) and strip_allows and ok_orig and ok_strip
    if not good:
        bad += 1
    rowsout.append((i, fen, "OK" if good else "FAIL", cap,
                    f"pinner={removed} orig_legal={orig_legal} strip_allows={strip_allows} "
                    f"engine_match_orig={ok_orig} engine_match_strip={ok_strip}"))

with open(OUT, "w") as f:
    f.write(f"positions: {len(rowsout)}\n")
    f.write(f"control passed (pin removed -> ep becomes legal, engine matches python-chess both times): "
            f"{len(rowsout)-bad}\n")
    f.write(f"control failed: {bad}\n\n")
    for r in rowsout:
        f.write("\t".join(str(x) for x in r) + "\n")
print(f"positions: {len(rowsout)}  control passed: {len(rowsout)-bad}  failed: {bad}")
for r in rowsout:
    if r[2] != "OK":
        print("FAIL", r)
