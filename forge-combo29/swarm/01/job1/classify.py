#!/usr/bin/env python3
"""swarm seat 01, job1: classify every disagreement between the engine and python-chess.

Two directions:
  A) engine ACCEPTED, python-chess REJECTED   -> invalid_list.txt (38 cases)
  B) engine REFUSED, python-chess ACCEPTED    -> refused_but_python_valid.txt
For each case, name which side is stricter and why, from the FEN text itself, so the report
does not guess.

Usage: classify.py <jobdir>
"""
import csv
import json
import sys
from collections import Counter

import chess


def fields6(fen):
    p = fen.split(" ")
    return p


def why_python_lenient(fen):
    """Return a short reason string for why python-chess accepts a FEN the engine refuses."""
    f = fields6(fen)
    if len(f) < 6:
        return "python-chess fills the missing counter fields (FEN has %d fields)" % len(f)
    if len(f) > 6:
        return "python-chess ignores trailing fields (FEN has %d)" % len(f)
    try:
        board = chess.Board(fen)
    except Exception:  # noqa: BLE001
        return "python-chess error (see raw)"
    wk = chess.popcount(board.kings & board.occupied_co[chess.WHITE])
    bk = chess.popcount(board.kings & board.occupied_co[chess.BLACK])
    if wk != 1 or bk != 1:
        return "python-chess allows %d white kings and %d black kings" % (wk, bk)
    if any(chess.square_rank(s) in (0, 7) for s in board.pieces(chess.PAWN, chess.WHITE) |
           board.pieces(chess.PAWN, chess.BLACK)):
        return "python-chess allows a pawn on rank 1 or 8"
    if board.castling_rights:
        # engine requires the king and rook to actually be there
        if board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK):
            return "python-chess allows a castling right the engine rejects (see refusal line)"
    if board.is_attacked_by(not board.turn, board.king(board.turn)):
        return "python-chess allows the side to move to be in check-mated-at-start shapes"
    if board.status() & chess.STATUS_TOO_MANY_CHECKERS:
        return "python-chess allows an impossible number of checkers"
    try:
        halfmove = int(f[4])
    except ValueError:
        return "halfmove field is not a number (python-chess defaults it)"
    try:
        fullmove = int(f[5])
    except ValueError:
        return "fullmove field is not a number (python-chess defaults it)"
    if fullmove < 1:
        return "fullmove %d < 1 (engine requires >= 1, the FEN spec starts at 1)" % fullmove
    if halfmove < 0:
        return "halfmove %d < 0" % halfmove
    return "other (see engine refusal line)"


def main(jobdir):
    rows = []
    for line in open(jobdir + "/results.jsonl"):
        rows.append(json.loads(line))
    mut = {}
    with open(jobdir + "/mutants.tsv") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) == 5:
                mut[int(p[0])] = p[4]

    a = []   # engine accepted, python rejected
    b = []   # engine refused, python accepted
    for rec in rows:
        if rec.get("crash"):
            continue
        fen = mut[rec["i"]]
        try:
            py_board = chess.Board(fen)
            py_ok = py_board.is_valid()
        except Exception:
            py_ok = False
        engine_ok = not rec.get("refused")
        if engine_ok and not py_ok:
            a.append((rec["i"], fen, rec.get("base_set"), rec.get("mutation_kind"),
                      rec.get("mutation_detail", "")))
        elif (not engine_ok) and py_ok:
            b.append((rec["i"], fen, rec.get("refusal_line", ""),
                      why_python_lenient(fen)))

    cat_a = Counter()
    for idx, fen, base, kind, detail in a:
        try:
            bb = chess.Board(fen)
            cat_a["python-chess parsed it but is_valid() is false: status %d" % bb.status()] += 1
        except Exception as exc:  # noqa: BLE001
            cat_a[str(exc).split("\n")[0]] += 1
    cat_b = Counter(r[3] for r in b)

    out = []
    out.append("A) engine ACCEPTED, python-chess REJECTED: %d" % len(a))
    for reason, n in cat_a.most_common():
        out.append("   %5d  %s" % (n, reason))
    out.append("")
    out.append("B) engine REFUSED, python-chess ACCEPTED: %d" % len(b))
    for reason, n in cat_b.most_common():
        out.append("   %5d  %s" % (n, reason))
    out.append("")
    out.append("B breakdown by the engine's own refusal line:")
    cat_b2 = Counter(r[2] for r in b)
    for reason, n in cat_b2.most_common():
        out.append("   %5d  %s" % (n, reason))
    text = "\n".join(out) + "\n"
    with open(jobdir + "/disagreements.txt", "w") as fh:
        fh.write(text)
    with open(jobdir + "/refused_but_python_valid.txt", "w") as fh:
        fh.write("idx\tfen\tengine_refusal\tpython_leniency\n")
        for r in b:
            fh.write("%d\t%s\t%s\t%s\n" % r)
    print(text)


if __name__ == "__main__":
    main(sys.argv[1])
