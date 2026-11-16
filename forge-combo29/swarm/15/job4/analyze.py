#!/usr/bin/env python3
"""analyze.py PVJSONL [--control]

Checks, for every record whose position was accepted:
  A. every move of the LAST `info ... pv` line is legal in sequence (python-chess);
  B. bestmove equals the first move of that pv line (when a pv exists);
  C. a `score mate N` score matches the PV length rule of the brief:
        N > 0  -> the PV ends in checkmate after exactly 2N-1 plies (mover mates)
        N < 0  -> after exactly 2|N| plies (mover is mated)
  D. a `score cp` on a position python-chess says is checkmate/stalemate at the root
     (reported separately, not counted as a fault here).

--control runs the illegal-move detector on copies of real PVs with one move replaced
by an illegal one, and prints how many of those the detector caught. Nothing is edited.
"""
import argparse
import json
import sys

import chess


def parse_score(info):
    """-> ('mate', N) or ('cp', v) or (None, None), from an info line."""
    tok = info.split()
    for i, t in enumerate(tok):
        if t == "score" and i + 2 < len(tok):
            kind, val = tok[i + 1], tok[i + 2]
            if kind in ("cp", "mate"):
                try:
                    return kind, int(val)
                except ValueError:
                    return None, None
    return None, None


def pv_of(info):
    tok = info.split()
    if "pv" not in tok:
        return []
    return tok[tok.index("pv") + 1:]


def replay(fen, moves):
    """-> (n_legal, first_illegal_index). Plays each move on a fresh board copy."""
    board = chess.Board(fen)
    for i, m in enumerate(moves):
        try:
            mv = chess.Move.from_uci(m)
        except ValueError:
            return i, i
        if mv not in board.legal_moves:
            return i, i
        board.push(mv)
    return len(moves), None


def replay_board(fen, moves):
    board = chess.Board(fen)
    for m in moves:
        mv = chess.Move.from_uci(m)
        if mv not in board.legal_moves:
            return board, False
        board.push(mv)
    return board, True


def mate_line_check(fen, moves, score_kind, score_val):
    """-> (ok, detail) for rule C."""
    if score_kind != "mate" or score_val in (None, 0):
        return None, "no mate score"
    n = score_val
    board = chess.Board(fen)
    plies = 0
    for m in moves:
        mv = chess.Move.from_uci(m)
        if mv not in board.legal_moves:
            return False, "pv illegal before mate check"
        board.push(mv)
        plies += 1
    want = (2 * n - 1) if n > 0 else (2 * abs(n))
    got_mate = board.is_checkmate()
    # after the PV, the side to move must be the one that is mated
    return (got_mate and plies == want), \
        "plies=%d want=%d checkmate=%s" % (plies, want, got_mate)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pvjsonl")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--maxlist", type=int, default=50)
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.pvjsonl, encoding="utf-8")]
    n_acc = n_ref = 0
    illegal = []
    bm_ne_pv = []
    mate_mis = []
    mate_pos = []
    no_pv = []
    cp_on_terminal = []
    fen_rejected = []

    for r in recs:
        if not r["accepted"]:
            n_ref += 1
            fen_rejected.append((r["idx"], r["fen"], r["answer"]))
            continue
        n_acc += 1
        if not r["infos"]:
            no_pv.append((r["idx"], r["fen"], r["bestmove"]))
        else:
            last = r["infos"][-1]
            moves = pv_of(last)
            legal_n, bad_i = replay(r["fen"], moves)
            if bad_i is not None:
                illegal.append((r["idx"], r["fen"], bad_i, moves[bad_i] if bad_i < len(moves) else "?",
                                last))
            kind, val = parse_score(last)
            ok, detail = mate_line_check(r["fen"], moves, kind, val)
            if kind == "mate" and val not in (None, 0):
                mate_pos.append((r["idx"], r["fen"], val, len(moves), detail))
            if ok is False:
                mate_mis.append((r["idx"], r["fen"], kind, val, detail, last))
            bm = (r["bestmove"] or "").split()
            if len(bm) >= 2 and moves and bm[1] != moves[0]:
                bm_ne_pv.append((r["idx"], r["fen"], bm[1], moves[0]))
            if kind == "cp":
                b = chess.Board(r["fen"])
                if b.is_checkmate() or b.is_stalemate():
                    cp_on_terminal.append((r["idx"], r["fen"], val, r["bestmove"], b.is_checkmate()))

    print("records        %d" % len(recs))
    print("accepted       %d" % n_acc)
    print("refused        %d" % n_ref)
    print("A illegal_pv_moves      %d" % len(illegal))
    print("B bestmove_not_pv_first %d" % len(bm_ne_pv))
    print("C mate_len_mismatch     %d" % len(mate_mis))
    print("   positions_with_mate_score %d" % len(mate_pos))
    print("D no_info_pv_line       %d" % len(no_pv))
    print("E cp_on_terminal_root   %d" % len(cp_on_terminal))
    for tag, lst in (("ILLEGAL", illegal), ("BM!=PV", bm_ne_pv), ("MATE_LEN", mate_mis),
                     ("NO_PV", no_pv), ("CP_TERMINAL", cp_on_terminal)):
        for item in lst[: args.maxlist]:
            print("%s  %s" % (tag, item))
    if n_ref:
        for item in fen_rejected[: args.maxlist]:
            print("REFUSED %s" % (item,))

    if args.control:
        # control: take 5 real PVs, replace the LAST move by a provably illegal one
        caught = tried = 0
        for r in recs:
            if not r["accepted"] or not r["infos"]:
                continue
            moves = pv_of(r["infos"][-1])
            if len(moves) < 2:
                continue
            board, okpre = replay_board(r["fen"], moves[:-1])
            if not okpre:
                continue
            legal = [m.uci() for m in board.legal_moves]
            if not legal:
                continue
            fake = "a1a8" if "a1a8" not in legal else "h1h8"
            mutated = moves[:-1] + [fake]
            n_legal, bad_i = replay(r["fen"], mutated)
            tried += 1
            if bad_i == len(moves) - 1:
                caught += 1
            if tried >= 5:
                break
        print("CONTROL planted_illegal_last_move tried %d caught %d" % (tried, caught))
    return 0


if __name__ == "__main__":
    sys.exit(main())
