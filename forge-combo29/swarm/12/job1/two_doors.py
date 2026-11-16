#!/usr/bin/env python3
"""two_doors.py EXE OUTFILE — reproduce both root-draw doors on one build.

DOOR 1 (halfmove): the same mate-in-one board at halfmove 99 and at halfmove 100.
DOOR 2 (repetition): the very same board reached a third time by legal knight shuffles,
        halfmove clock 8 (well under 100), against the same board given by `position fen`.

Each case is a fresh process: `uci`, `position ...` (+ `moves ...` for door 2), `isready`,
then `go depth 6`, reading every line until `bestmove`. The script records the whole answer,
the last `info ... score ... nodes` line, and checks the bestmove's mating status with
python-chess, so a "missing mate" claim never rests on reading the engine's own score.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

# mate-in-one board: black king boxed on g8 by its own f7/g7/h7 pawns, white plays Ra8#. White
# has a knight on g1 and a king on h1 that can shuffle (Ng1-f3-g1, Kh1-g1) so the very same
# position can be reached a third time by legal moves — which is what door 2 needs.
BASE = "6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"

# white Ng1<->f3 and black Kg8<->h8: after 8 plies the base position stands for the third time
SHUFFLE = "g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8".split()


def mate_moves(fen):
    board = chess.Board(fen)
    return sorted(m.uci() for m in board.legal_moves if board.is_mate_after_push(m)) if hasattr(board, "is_mate_after_push") else _mates(board)


def _mates(board):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return sorted(out)


def ask(exe, position_line, depth=6, timeout_s=60):
    script = f"uci\n{position_line}\nisready\ngo depth {depth}\n"
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip("\n"))
        q.put(None)
    threading.Thread(target=reader, daemon=True).start()
    p.stdin.write(script)
    p.stdin.flush()
    lines, t0 = [], time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        lines.append(ln)
        if ln.startswith("bestmove"):
            break
    try:
        # `quit` only after the answer: quit itself stops the search, and a search stopped
        # at once answers with whatever the root ordering holds, not with its result.
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.stdin.close()
    except OSError:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


def summarize(lines):
    last_info = None
    for ln in lines:
        if ln.startswith("info") and " pv " in ln or (ln.startswith("info depth") and "score" in ln):
            last_info = ln
    bm = next((ln.split()[1] for ln in lines if ln.startswith("bestmove")), None)
    nodes = None
    if last_info:
        m = re.search(r" nodes (\d+)", last_info)
        nodes = int(m.group(1)) if m else None
    score = None
    if last_info:
        m = re.search(r"score (cp|mate) (-?\d+)", last_info)
        score = f"{m.group(1)} {m.group(2)}" if m else None
    san = [ln for ln in lines if re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|runtime error: ", ln)]
    return {"bestmove": bm, "nodes": nodes, "score": score, "last_info": last_info,
            "sanitizer_lines": san}


def repeats_to_threefold(fen, max_plies=24):
    """Legal shuffle that brings the same position back three times; returns the move list.

    Only the side to move repeats its own moves (the opponent must have a waiting move), so
    the search is a depth-limited walk over moves that restore a position already seen.
    """
    board = chess.Board(fen)
    seen = {board.fen(): 1}
    moves = []

    def walk(depth):
        if depth == 0:
            return None
        for m in board.legal_moves:
            board.push(m)
            f = board.fen()
            hit = f in seen
            if hit:
                seen[f] += 1
            else:
                seen[f] = 1
            moves.append(m.uci())
            if seen.get(board.fen(), 0) >= 3:
                return True
            if walk(depth - 1):
                return True
            moves.pop()
            seen[f] -= 1
            if seen[f] == 0:
                del seen[f]
            board.pop()
        return None

    ok = walk(max_plies)
    return list(moves) if ok else None


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    rec = Path(exe).stat().st_size
    cases = []

    # ---- DOOR 1: halfmove 99 vs 100 on the identical board
    for hm in (99, 100):
        fen = f"6k1/5ppp/8/8/8/8/8/R5NK w - - {hm} 40"
        cases.append((f"door1_hm{hm}", f"position fen {fen}", fen, None))

    # ---- DOOR 2: threefold repetition, halfmove far below 100
    board = chess.Board(BASE)
    for m in SHUFFLE:
        board.push_uci(m)
    rep_fen = board.fen()
    rep_hm = int(rep_fen.split()[-2])
    if not board.is_repetition(3):
        print("the shuffle does not reach a threefold repetition", file=sys.stderr)
        sys.exit(2)
    moves = SHUFFLE
    cases.append(("door2_after_moves", f"position fen {BASE} moves {' '.join(moves)}", rep_fen, moves))
    cases.append(("door2_control_fen", f"position fen {rep_fen}", rep_fen, None))

    out = {"exe": exe, "size": rec, "cases": []}
    print(f"exe {exe}")
    print(f"base board mate in 1 : {_mates(chess.Board(BASE))}")
    print(f"repetition move list : {moves}")
    print(f"repeated position    : {rep_fen}   (halfmove {rep_hm})")
    print()
    print(f"{'case':22} {'bestmove':9} {'nodes':>8} {'score':10} mate-after-bm?")
    for name, posline, fen, mv in cases:
        lines = ask(exe, posline)
        s = summarize(lines)
        m_ok = None
        if s["bestmove"]:
            b = chess.Board(fen)
            try:
                b.push_uci(s["bestmove"])
                m_ok = b.is_checkmate()
            except ValueError:
                m_ok = "unparseable"
        entry = {"case": name, "position_line": posline, "fen": fen, "moves": mv,
                 "answer": s, "bestmove_is_mate": m_ok, "mates_available": _mates(chess.Board(fen)),
                 "lines": lines[-4:]}
        out["cases"].append(entry)
        print(f"{name:22} {str(s['bestmove']):9} {str(s['nodes']):>8} {str(s['score']):10} {m_ok}")
    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nraw written to {outfile}")


if __name__ == "__main__":
    main()
