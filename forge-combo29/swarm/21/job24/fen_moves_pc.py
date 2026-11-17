#!/usr/bin/env python3
"""fen_moves_pc.py OUTDIR

`position fen <FEN> moves <moves>` and the illegal-prefix rule on BOTH builds, Threads 1.

Cases (fresh process each, read to `nodes`, asserted present):
  1  fen F, moves e1d1              perft 1 must be python-chess's count AFTER e1d1
  2  fen F only (control)           perft 1 must be python-chess's count for F
  3  startpos, 200 legal plies      perft 1 and perft 2 must match python-chess
  4  200 plies + illegal at 10      perft 1/2 must match python-chess after the 9-ply prefix
  5  a REFUSED fen followed by moves, then perft 1
                                    the old position must stand (21-F2), i.e. NOT F's moves
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine  # noqa: E402

import chess

F = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
REFUSED = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3"


def perft2(bd):
    t = 0
    for m in bd.legal_moves:
        c = bd.copy()
        c.push(m)
        t += c.legal_moves.count()
    return t


def nodes_of(lines, tag):
    vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
    if not vals:
        raise AssertionError("%s: no nodes line" % tag)
    return vals[0]


def game(nplies):
    import random
    rng = random.Random(2101)
    b = chess.Board()
    seq, boards = [], [b.copy()]
    while len(seq) < nplies:
        ms = list(b.legal_moves)
        if not ms:
            break
        b.push(rng.choice(ms))
        seq.append(b.peek().uci())
        boards.append(b.copy())
    return seq, boards


def illegal_token(board):
    legal = {m.uci() for m in board.legal_moves}
    for frm in chess.SQUARES:
        p = board.piece_at(frm)
        if p is None:
            continue
        for to in chess.SQUARES:
            if frm == to:
                continue
            tok = chess.square_name(frm) + chess.square_name(to)
            if tok in legal:
                continue
            t = board.piece_at(to)
            if t is not None and t.color == p.color:
                return tok
    raise RuntimeError("no illegal token")


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    b_after = chess.Board(F)
    b_after.push_uci("e1d1")
    seq, boards = game(200)
    tok = illegal_token(boards[9])

    cases = [
        ("1_fen_moves", "position fen %s moves e1d1" % F,
         [(b_after.legal_moves.count(), perft2(b_after.copy()))]),
        ("2_fen_only", "position fen " + F,
         [(chess.Board(F).legal_moves.count(), perft2(chess.Board(F)))]),
        ("3_200_legal", "position startpos moves " + " ".join(seq),
         [(boards[-1].legal_moves.count(), perft2(boards[-1].copy()))]),
        ("4_illegal_10", "position startpos moves " + " ".join(seq[:9] + [tok] + seq[9:]),
         [(boards[9].legal_moves.count(), perft2(boards[9].copy()))]),
    ]
    builds = [("pc", os.path.expanduser("~/b/pc_asan/forge")),
              ("base", os.path.expanduser("~/b/asan/forge"))]
    R = {}
    rows = ["| build | case | perft1 engine | perft1 python | perft2 engine | perft2 python | match |",
            "|---|---|---|---|---|---|---|"]
    for bname, exe in builds:
        for tag, pos, expect in cases:
            e = SafeEngine(exe, os.path.join(outdir, "%s_%s_raw.txt" % (bname, tag)),
                           hash_mb=16, threads=1)
            e.position(pos)
            n1 = nodes_of(e.go("go perft 1", token="nodes"), tag)
            n2 = nodes_of(e.go("go perft 2", token="nodes"), tag)
            e.close()
            py1, py2 = expect[0]
            ok = (n1 == py1 and n2 == py2)
            R["%s|%s" % (bname, tag)] = dict(n1=n1, n2=n2, py1=py1, py2=py2, ok=ok)
            rows.append("| %s | %s | %d | %d | %d | %d | %s |" % (
                bname, tag, n1, py1, n2, py2, "yes" if ok else "NO"))

        # 5: refused FEN, then perft 1 must be the OLD position
        e = SafeEngine(exe, os.path.join(outdir, "%s_5_refused_raw.txt" % bname),
                       hash_mb=16, threads=1)
        e.position("position fen " + F)
        pre = nodes_of(e.go("go perft 1", token="nodes"), "pre")
        ans = e.position("position fen %s moves e1d1" % REFUSED)
        post = nodes_of(e.go("go perft 1", token="nodes"), "post")
        e.close()
        kept_old = (post == pre)
        R["%s|5_refused" % bname] = dict(pre=pre, post=post, kept_old=kept_old,
                                         answer=[l for l in ans if "info string" in l])
        rows.append("| %s | 5 refused fen+moves | pre=%d | post=%d | old kept=%s | – | – |" % (
            bname, pre, post, kept_old))

    all_ok = all(v.get("ok", v.get("kept_old")) for v in R.values())
    text = "\n".join(rows)
    text += "\n\nall cases as predicted on both builds: %s\n" % all_ok
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()